
import re

def clean_text_for_tts(text):
    """移除文本中的emoji和特殊图标，防止TTS读出乱码"""
    import unicodedata
    out = []
    for ch in text:
        cp = ord(ch)
        cat = unicodedata.category(ch)
        if cat == 'So':
            continue
        if cat == 'Sk':
            continue
        if cat == 'Cf' and cp >= 0xFE00:
            continue
        out.append(ch)
    stripped = ''.join(out).strip()
    return re.sub(r'[#*`~\-]+', '', stripped)

from datetime import date, timedelta
import asyncio, io, csv, subprocess, time, uuid, shutil, wave, struct
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, HTMLResponse, StreamingResponse
from pydantic import BaseModel

from core.rag_engine import RAGEngine
from core.asr_tts import ASRService, TTSService, CACHE_DIR
from core.logger import InteractionLogger

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

rag = RAGEngine()
asr = ASRService()
tts = TTSService()
logger = InteractionLogger()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def remove_emoji(text):
    return clean_text_for_tts(text)

PRESET_REPLIES = {
    '你是谁': '我是小灵，灵山胜境的AI数字导游。我可以为您讲解灵山大佛、梵宫等景点，推荐游览路线，解答各类景区问题。随时问我吧！',
    '介绍自己': '我叫小灵，是灵山胜境景区的专属AI导游。我熟悉这里的每一个景点和每一段故事，希望能带您领略千年佛国的魅力。',
    '你好': '您好！我是小灵，灵山胜境的AI导游。有什么可以帮您的吗？',
    '嗨': '嗨！我是小灵，很高兴为您服务。关于灵山胜境的任何问题，尽管问我哦。',
}

def get_preset_reply(text):
    print(f"[PRESET_CHECK] text={text[:30]}", flush=True)
    for key, reply in PRESET_REPLIES.items():
        if key in text:
            print(f"[PRESET_HIT] key={key}", flush=True)
            return reply
    if '梵宫' in text and ('火灾' in text or '烧' in text):
        return (
            '灵山梵宫2016年11月8日廊厅发生火灾，过火面积约600平方米，'
            '未造成人员伤亡。景区闭园约一年重建升级，2017年11月15日以全新面貌重新开放。'
            '修复后廊厅采用更先进的防火防震工艺，12幅巨型油画邀请原作者重绘，'
            '同时增设了《灵山吉祥颂》专场演出。'
        )
    if '灵山精舍' in text:
        return (
            '灵山精舍是灵山胜境三期配套的禅意主题住宿，2009年左右与灵山佛学院、三圣殿、慈恩塔一同建成。'
            '整体采用极简禅意设计，约95间客房（480~1280元/间/晚），配有榻榻米、禅服、抄写台。'
            '除住宿外还提供素斋自助、抄经室、禅修体验课（坐禅/行禅/止语茶会）、朝山早课和香道花道手作。'
            '地址在景区内，距大佛步行约8分钟。'
        )
    if '灵山佛学院' in text:
        return (
            '灵山佛学院是灵山胜境三期辅助工程的一部分，2009年左右与灵山精舍、三圣殿、慈恩塔一同建成。'
            '致力于佛教人才培养与佛法弘扬，是景区信仰、教育、文化三位一体的重要体现。'
        )
    if ('开放时间' in text or '开门' in text or '关门' in text or '几点' in text or '营业' in text) and ('灵山' in text or '胜境' in text or '大佛' in text):
        return (
            '灵山胜境全年开放时间为07:30至17:30。灵山大佛全天开放，无论白天黑夜都能参观，夜间还有灯光点缀。'
            '梵宫、五印坛城等室内场馆一般09:00开馆、17:00闭馆，冬季可能提前到16:30。'
            '九龙灌浴平日10:00、11:30、13:30、15:00各一场，周末及节假日加场。'
        )
    if '门票' in text:
        return (
            '灵山胜境成人票210元/人；6-18岁未成年人、全日制本科及以下学生、60-69岁老人半价105元；'
            '6岁以下或1.4米以下儿童、70岁以上老人、现役军人、残疾人免票。网购联票225元含门票和无限次观光车，更划算哦～'
        )
    return None

class ChatRequest(BaseModel):
    text: str
    voice: str = None
    tags: list[str] | None = None

class FeedbackRequest(BaseModel):
    rating: str | int


# ========== async helpers ==========

async def run_subprocess_async(cmd, input_bytes=None, timeout=None):
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE if input_bytes is not None else None,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(input=input_bytes), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise
    if proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, cmd, output=stdout, stderr=stderr)
    return stdout, stderr


async def ffmpeg_convert_to_wav_async(src_path, dst_wav):
    cmd = ['ffmpeg', '-y', '-i', src_path, '-ar', '16000', '-ac', '1', dst_wav]
    await run_subprocess_async(cmd, timeout=15)


async def tts_synthesize_async(text, output_path, voice=None):
    actual_voice = voice or tts.voice
    cache_file = tts._cache_path(text, actual_voice)

    if os.path.exists(cache_file):
        if not os.path.isabs(output_path):
            output_path = os.path.join(os.getcwd(), output_path)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        shutil.copy2(cache_file, output_path)
        return output_path

    if not os.path.isabs(output_path):
        output_path = os.path.join(os.getcwd(), output_path)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    try:
        cmd = ['edge-tts', '--voice', actual_voice, '--text', text, '--write-media', cache_file]
        await run_subprocess_async(cmd, timeout=20)
        shutil.copy2(cache_file, output_path)
        tts._mem_cache[f"{text}_{actual_voice}"] = cache_file
    except Exception as e:
        print(f"TTS async fail: {e}, fallback silence")
        with wave.open(output_path, 'w') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(struct.pack('<h', 0) * 32000)
    return output_path


async def rag_answer_async(user_query, tags=None):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: rag.answer(user_query, tags=tags))


async def asr_transcribe_async(wav_path):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, asr.transcribe, wav_path)


def gen_reply_audio_path():
    return f"../data/processed/reply_{uuid.uuid4().hex[:8]}.wav"


# ========== 路由 ==========

@app.get("/", response_class=HTMLResponse)
async def index():
    with open(os.path.join(BASE_DIR, 'static', 'index.html'), 'r', encoding='utf-8') as f:
        return f.read()

@app.post("/api/config/set-voice")
async def set_voice(voice_id: str):
    tts.voice = voice_id
    return {"status": "ok", "voice": voice_id}

@app.get("/api/config/voices")
async def get_voices():
    voices = [
        {"id": "zh-CN-XiaoxiaoNeural", "name": "晓晓", "gender": "女", "style": "温暖亲切"},
        {"id": "zh-CN-XiaoyiNeural", "name": "小艺", "gender": "女", "style": "活泼可爱"},
        {"id": "zh-CN-YunjianNeural", "name": "云健", "gender": "男", "style": "激情有力"},
        {"id": "zh-CN-YunxiNeural", "name": "云希", "gender": "男", "style": "阳光清朗"},
        {"id": "zh-CN-YunxiaNeural", "name": "云霞", "gender": "男", "style": "温柔可爱"},
        {"id": "zh-CN-YunyangNeural", "name": "云阳", "gender": "男", "style": "专业沉稳"},
    ]
    return {"voices": voices, "current_voice": tts.voice}

def _build_effective_query(text: str, tags) -> tuple:
    """Return (effective_query, tags_clean). Strips any existing Chinese prefix if present."""
    if not tags and not text.startswith("【游客的兴趣是："):
        return text, tags
    tag_prefix = ""
    if tags:
        tag_prefix = "【游客的兴趣是：" + "/".join([t for t in tags if isinstance(t, str) and t.strip()]) + "】"
    elif text.startswith("【游客的兴趣是："):
        end = text.find("】", 9)
        if end > 0:
            tag_prefix = text[:end+1]
            text = text[end+1:]
    if tag_prefix and not text.startswith("【游客的兴趣是："):
        return tag_prefix + text, tags
    return text, tags


@app.post("/api/chat/tts")
async def text_to_speech(req: ChatRequest):
    start = time.time()

    effective_query, tags_clean = _build_effective_query(req.text, req.tags)

    preset = get_preset_reply(req.text)
    if preset:
        reply_audio = gen_reply_audio_path()
        tts_start = time.time()
        await tts_synthesize_async(preset, reply_audio, voice=req.voice)
        tts_time = time.time() - tts_start
        duration = time.time() - start
        print(f"[TIMER] Preset reply - TTS: {tts_time:.2f}s, Total: {duration:.2f}s")
        logger.add(req.text, preset, duration=duration, source="tts")
        return {"question": req.text, "answer": preset, "audioUrl": f"/api/audio/{os.path.basename(reply_audio)}"}

    rag_start = time.time()
    result = await rag_answer_async(effective_query, tags=tags_clean)
    rag_time = time.time() - rag_start

    clean_answer = remove_emoji(result['answer'])

    tts_start = time.time()
    reply_audio = gen_reply_audio_path()
    await tts_synthesize_async(clean_answer, reply_audio, voice=req.voice)
    tts_time = time.time() - tts_start

    duration = time.time() - start
    print(f"[TIMER] RAG: {rag_time:.2f}s, TTS: {tts_time:.2f}s, Total: {duration:.2f}s")

    logger.add(req.text, clean_answer, duration=duration, source="tts")
    return {
        "question": result['question'],
        "answer": clean_answer,
        "audioUrl": f"/api/audio/{os.path.basename(reply_audio)}"
    }

@app.post("/api/chat/text")
async def text_chat(req: ChatRequest):
    start = time.time()
    preset = get_preset_reply(req.text)
    if preset:
        duration = time.time() - start
        logger.add(req.text, preset, duration=duration, source="text")
        return {"question": req.text, "answer": preset, "sources": []}
    result = await rag_answer_async(req.text)
    clean_answer = remove_emoji(result['answer'])
    duration = time.time() - start
    logger.add(req.text, clean_answer, duration=duration, source="text")
    return {
        "question": result['question'],
        "answer": clean_answer,
        "sources": result['sources']
    }

@app.post("/api/chat/voice16")
async def voice16_chat(file: UploadFile = File(...)):
    start = time.time()
    ts = time.time()
    wav = f"../data/processed/{uuid.uuid4().hex[:8]}.wav"
    payload = await file.read()
    t_io = time.time() - ts
    with open(wav, "wb") as f:
        f.write(payload)

    ts = time.time()
    user_text = await asr_transcribe_async(wav) or "未识别"
    t_asr = time.time() - ts
    print(f"[voice16] io={t_io:.2f}s asr={t_asr:.2f}s text={user_text}")

    preset = get_preset_reply(user_text)
    if preset:
        reply_audio = gen_reply_audio_path()
        await tts_synthesize_async(preset, reply_audio)
        duration = time.time() - start
        logger.add(user_text, preset, duration=duration, source="voice16")
        return {"user_text": user_text, "reply_text": preset, "audioUrl": f"/api/audio/{os.path.basename(reply_audio)}"}

    ts = time.time()
    result = await rag_answer_async(user_text)
    t_rag = time.time() - ts
    clean_answer = remove_emoji(result['answer'])

    ts = time.time()
    reply_audio = gen_reply_audio_path()
    await tts_synthesize_async(clean_answer, reply_audio)
    t_tts = time.time() - ts

    duration = time.time() - start
    print(f"[TIMER] voice16 total={duration:.2f}s | io={t_io:.2f} asr={t_asr:.2f} rag={t_rag:.2f} tts={t_tts:.2f}")
    logger.add(user_text, clean_answer, duration=duration, source="voice16")
    return {
        "user_text": user_text,
        "reply_text": clean_answer,
        "audioUrl": f"/api/audio/{os.path.basename(reply_audio)}"
    }


@app.post("/api/chat/voice")
async def voice_chat(file: UploadFile = File(...)):
    start = time.time()
    ts = time.time()
    raw = f"../data/processed/{uuid.uuid4().hex[:8]}.webm"
    wav = raw.replace('.webm', '.wav')
    payload = await file.read()
    t_io = time.time() - ts
    with open(raw, "wb") as f:
        f.write(payload)

    ts = time.time()
    try:
        await ffmpeg_convert_to_wav_async(raw, wav)
        t_ffmpeg = time.time() - ts
    except Exception as e:
        print(f"[voice] ffmpeg failed: {e}, fallback: reuse raw")
        wav = raw

    ts = time.time()
    user_text = await asr_transcribe_async(wav) or "未识别"
    t_asr = time.time() - ts
    print(f"[voice] io={t_io:.2f}s ffmpeg={t_ffmpeg:.2f}s asr={t_asr:.2f}s text={user_text}")

    preset = get_preset_reply(user_text)
    if preset:
        reply_audio = gen_reply_audio_path()
        await tts_synthesize_async(preset, reply_audio)
        duration = time.time() - start
        logger.add(user_text, preset, duration=duration, source="voice")
        return {"user_text": user_text, "reply_text": preset, "audioUrl": f"/api/audio/{os.path.basename(reply_audio)}"}

    ts = time.time()
    result = await rag_answer_async(user_text)
    t_rag = time.time() - ts
    clean_answer = remove_emoji(result['answer'])

    ts = time.time()
    reply_audio = gen_reply_audio_path()
    await tts_synthesize_async(clean_answer, reply_audio)
    t_tts = time.time() - ts

    duration = time.time() - start
    print(f"[TIMER] voice total={duration:.2f}s | io={t_io:.2f} ffmpeg={t_ffmpeg:.2f} asr={t_asr:.2f} rag={t_rag:.2f} tts={t_tts:.2f}")
    logger.add(user_text, clean_answer, duration=duration, source="voice")
    return {
        "user_text": user_text,
        "reply_text": clean_answer,
        "audioUrl": f"/api/audio/{os.path.basename(reply_audio)}"
    }

@app.get("/api/audio/{filename}")
async def get_audio(filename: str):
    path = f"../data/processed/{filename}"
    if not os.path.exists(path):
        return Response(status_code=404)
    with open(path, 'rb') as f:
        content = f.read()
    return Response(content=content, media_type="audio/wav")


@app.post("/api/chat/image")
async def image_chat(text: str = Form(""), file: UploadFile = File(...)):
    img_bytes = await file.read()
    img_path = f"../data/processed/img_{uuid.uuid4().hex[:8]}.jpg"
    with open(img_path, "wb") as f:
        f.write(img_bytes)

    try:
        import dashscope
        from dashscope import MultiModalConversation

        messages = [{
            "role": "system",
            "content": [{"text": "你是灵山胜境景区的AI导游小灵，请根据图片和问题，结合景区知识回答。"}]
        }, {
            "role": "user",
            "content": [
                {"image": f"file://{os.path.abspath(img_path)}"},
                {"text": text or "请描述这张图片"}
            ]
        }]

        response = MultiModalConversation.call(
            model="qwen-vl-plus",
            messages=messages,
            api_key=os.getenv("DASHSCOPE_API_KEY")
        )

        if response.status_code == 200:
            answer = response.output.choices[0].message.content[0]["text"]
        else:
            answer = "抱歉，小灵无法理解这张图片"
    except Exception as e:
        print(f"多模态API调用失败: {e}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, rag.answer, text) if text else {"answer": "请提供问题描述"}
        answer = result.get("answer", "请提供问题描述")

    clean_answer = remove_emoji(answer)
    tts_audio = gen_reply_audio_path()
    await tts_synthesize_async(clean_answer, tts_audio)
    logger.add(text or "图片提问", clean_answer, source="image")

    return {
        "answer": clean_answer,
        "audioUrl": f"/api/audio/{os.path.basename(tts_audio)}"
    }


@app.post("/api/chat/clear")
async def clear():
    return rag.clear_history()

@app.get("/api/admin/dashboard")
async def dashboard():
    return logger.get_stats()

@app.get("/api/admin/recent")
async def recent(limit: int = 20):
    return logger.get_recent(limit)

@app.get("/admin", response_class=HTMLResponse)
async def admin():
    with open(os.path.join(BASE_DIR, 'static', 'admin.html'), 'r', encoding='utf-8') as f:
        return f.read()


@app.post("/api/feedback")
async def feedback(req: FeedbackRequest):
    rating = req.rating
    valid = {"good", "neutral", "bad", "1", "2", "3", "4", "5", 1, 2, 3, 4, 5}
    if rating not in valid:
        return {"status": "error", "message": "无效的评分"}
    logger.add_feedback(rating)
    return {"status": "ok"}


import json

AVATAR_DIR = os.path.join(BASE_DIR, "static", "avatars")
os.makedirs(AVATAR_DIR, exist_ok=True)

@app.post("/api/admin/upload-avatar")
async def upload_avatar(file: UploadFile = File(...)):
    if file.content_type not in ("image/png", "image/jpeg", "image/gif"):
        return {"error": "仅支持 PNG/JPG/GIF 图片"}
    filename = f"{uuid.uuid4().hex}_{file.filename}"
    filepath = os.path.join(AVATAR_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(await file.read())
    return {"url": f"/static/avatars/{filename}", "name": file.filename}

@app.get("/api/admin/avatars")
async def list_avatars():
    avatars = [{"id": "default", "name": "默认导游", "type": "svg", "url": ""}]
    if os.path.exists(AVATAR_DIR):
        for fname in sorted(os.listdir(AVATAR_DIR)):
            if fname.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                avatars.append({
                    "id": fname,
                    "name": fname.split("_", 1)[-1],
                    "type": "image",
                    "url": f"/static/avatars/{fname}"
                })
    return avatars

@app.delete("/api/admin/avatars/{filename}")
async def delete_avatar(filename: str):
    filepath = os.path.join(AVATAR_DIR, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return {"status": "ok"}
    return {"error": "文件不存在"}


@app.post("/api/admin/upload-live2d")
async def upload_live2d_model(file: UploadFile = File(...)):
    import zipfile

    if not file.filename.endswith('.zip'):
        return {"error": "仅支持 ZIP 格式的 Live2D 模型"}

    temp_dir = os.path.join(BASE_DIR, "static", "live2d", "custom_models", uuid.uuid4().hex)
    os.makedirs(temp_dir, exist_ok=True)

    try:
        zip_path = os.path.join(temp_dir, file.filename)
        with open(zip_path, "wb") as f:
            content = await file.read()
            f.write(content)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        os.remove(zip_path)

        model_json_path = None
        model_name = file.filename.replace('.zip', '')

        for root, dirs, files in os.walk(temp_dir):
            for fname in files:
                if fname.endswith('.model.json'):
                    model_json_path = os.path.join(root, fname)
                    try:
                        with open(model_json_path, 'r', encoding='utf-8') as f:
                            model_data = json.load(f)
                            if 'name' in model_data:
                                model_name = model_data['name']
                    except:
                        pass
                    break
            if model_json_path:
                break

        if not model_json_path:
            shutil.rmtree(temp_dir, ignore_errors=True)
            return {"error": "未找到 .model.json 文件，请确认是有效的 Live2D 模型"}

        rel_path = os.path.relpath(model_json_path, os.path.join(BASE_DIR, "static", "live2d"))
        model_url = f"/static/live2d/{rel_path.replace(os.sep, '/')}"

        model_id = uuid.uuid4().hex[:8]

        models_file = os.path.join(BASE_DIR, "static", "live2d", "models.json")
        try:
            with open(models_file, 'r', encoding='utf-8') as f:
                models_data = json.load(f)
        except:
            models_data = {"models": []}

        existing = any(m.get("modelUrl") == model_url for m in models_data.get("models", []))

        if not existing:
            new_model = {
                "id": model_id,
                "name": model_name,
                "type": "live2d",
                "modelUrl": model_url,
                "voice": "zh-CN-XiaoxiaoNeural",
                "custom": True
            }
            models_data["models"].append(new_model)
            with open(models_file, 'w', encoding='utf-8') as f:
                json.dump(models_data, f, ensure_ascii=False, indent=2)

        return {
            "status": "ok",
            "model": {
                "id": model_id,
                "name": model_name,
                "modelUrl": model_url
            }
        }

    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return {"error": f"处理失败: {str(e)}"}

@app.delete("/api/admin/delete-live2d/{model_id}")
async def delete_live2d_model(model_id: str):
    models_file = os.path.join(BASE_DIR, "static", "live2d", "models.json")
    try:
        with open(models_file, 'r', encoding='utf-8') as f:
            models_data = json.load(f)

        original_length = len(models_data.get("models", []))
        models_data["models"] = [m for m in models_data.get("models", [])
                                  if m.get("id") != model_id or not m.get("custom")]

        if len(models_data["models"]) < original_length:
            with open(models_file, 'w', encoding='utf-8') as f:
                json.dump(models_data, f, ensure_ascii=False, indent=2)
            return {"status": "ok"}

        return {"error": "模型不存在或无法删除内置模型"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/admin/refresh-models")
async def refresh_models():
    return {"status": "ok"}


@app.get("/api/admin/export")
async def export_data(format: str = "json"):
    logs = logger._read(logger.log_path)
    if format == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["timestamp","date","question","answer","duration","source"])
        writer.writeheader()
        writer.writerows(logs)
        return StreamingResponse(iter([output.getvalue()]), media_type="text/csv",
                                 headers={"Content-Disposition": "attachment; filename=interaction_log.csv"})
    else:
        return logs

@app.get("/api/admin/feedbacks")
async def get_feedbacks():
    return logger._read(logger.feedback_path)

@app.get("/api/admin/wordcloud")
async def word_cloud(top: int = 10):
    return {"words": logger.get_word_cloud(top_n=top)}

@app.get("/api/admin/stats/daily")
async def daily_stats():
    logs = logger._read(logger.log_path)
    daily = {}
    for l in logs:
        day = l["date"]
        daily[day] = daily.get(day, 0) + 1
    today = date.today()
    result = []
    for i in range(6, -1, -1):
        d = str(today - timedelta(days=i))
        result.append({"date": d, "count": daily.get(d, 0)})
    return result

@app.get("/api/admin/documents")
async def list_documents():
    return rag.kb.list_files()


@app.post("/api/admin/upload-document")
async def upload_document(file: UploadFile = File(...)):
    ALLOW = {".txt", ".md", ".pdf", ".docx", ".doc", ".xlsx", ".xls"}
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOW:
        return {"status": "error", "message": f"不支持的文件类型 {ext}，仅允许: {', '.join(sorted(ALLOW))}"}

    save_dir = os.path.join(BASE_DIR, "..", "data", "raw")
    os.makedirs(save_dir, exist_ok=True)
    # 去重：同名覆盖 → 自动加 _1 / _2 后缀
    base_name = filename
    target_path = os.path.join(save_dir, base_name)
    n = 1
    while os.path.exists(target_path):
        stem, e = os.path.splitext(base_name)
        target_path = os.path.join(save_dir, f"{stem}_{n}{e}")
        n += 1

    try:
        content = await file.read()
        if len(content) == 0:
            return {"status": "error", "message": "文件为空"}
        with open(target_path, "wb") as f:
            f.write(content)
    except Exception as e:
        return {"status": "error", "message": f"保存失败: {e}"}

    try:
        info = rag.kb.build_vector_store()
        rag.clear_history()
        return {
            "status": "ok",
            "filename": os.path.basename(target_path),
            "size": len(content),
            "chunks": info.get("chunks", 0),
            "docs": info.get("docs", 0),
        }
    except Exception as e:
        return {
            "status": "partial",
            "message": f"文件已保存但索引重建失败: {e}",
            "filename": os.path.basename(target_path),
        }


@app.post("/api/admin/upload-documents")
async def upload_documents(files: list[UploadFile] = File(...)):
    ALLOW = {".txt", ".md", ".pdf", ".docx", ".doc", ".xlsx", ".xls"}
    save_dir = os.path.join(BASE_DIR, "..", "data", "raw")
    os.makedirs(save_dir, exist_ok=True)
    saved, errors = [], []
    for f in files:
        ext = os.path.splitext((f.filename or ""))[1].lower()
        if ext not in ALLOW:
            errors.append({"filename": f.filename, "reason": f"不支持的类型 {ext}"})
            continue
        try:
            content = await f.read()
            if len(content) == 0:
                errors.append({"filename": f.filename, "reason": "文件为空"})
                continue
            base_name = f.filename
            target_path = os.path.join(save_dir, base_name)
            n = 1
            while os.path.exists(target_path):
                stem, e = os.path.splitext(base_name)
                target_path = os.path.join(save_dir, f"{stem}_{n}{e}")
                n += 1
            with open(target_path, "wb") as wf:
                wf.write(content)
            saved.append({"filename": os.path.basename(target_path), "size": len(content)})
        except Exception as e:
            errors.append({"filename": f.filename, "reason": str(e)})

    try:
        info = rag.kb.build_vector_store()
        rag.clear_history()
        return {
            "status": "ok",
            "saved": saved,
            "errors": errors,
            "chunks": info.get("chunks", 0),
            "docs": info.get("docs", 0),
        }
    except Exception as e:
        return {"status": "partial", "saved": saved, "errors": errors, "message": f"索引重建失败: {e}"}


@app.post("/api/admin/delete-document")
async def delete_document(payload: dict):
    name = payload.get("name", "")
    if not name or ".." in name or "/" in name or "\\" in name:
        return {"status": "error", "message": "非法文件名"}
    save_dir = os.path.join(BASE_DIR, "..", "data", "raw")
    target = os.path.join(save_dir, name)
    if not os.path.isfile(target):
        return {"status": "error", "message": "文件不存在"}
    try:
        os.remove(target)
    except Exception as e:
        return {"status": "error", "message": str(e)}
    try:
        info = rag.kb.build_vector_store()
        rag.clear_history()
        return {"status": "ok", "chunks": info.get("chunks", 0), "docs": info.get("docs", 0)}
    except Exception as e:
        return {"status": "partial", "message": f"已删除文件但索引重建失败: {e}"}


@app.post("/api/admin/rebuild-index")
async def rebuild_index():
    try:
        info = rag.kb.build_vector_store()
        rag.clear_history()
        return {"status": "ok", "message": "向量库已重建", **info}
    except Exception as e:
        return {"status": "error", "message": str(e)}


MODEL_DIR = os.path.join(BASE_DIR, "static", "models")
os.makedirs(MODEL_DIR, exist_ok=True)

@app.post("/api/admin/models/upload")
async def upload_model(file: UploadFile = File(...)):
    if file.content_type not in ("image/png", "image/jpeg", "image/gif"):
        return {"error": "仅支持 PNG/JPG/GIF 图片"}
    filename = f"{uuid.uuid4().hex}_{file.filename}"
    filepath = os.path.join(MODEL_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(await file.read())
    return {"url": f"/static/models/{filename}", "name": file.filename}

@app.get("/api/admin/models")
async def list_models():
    models = [{"id": "default", "name": "默认导游小灵", "type": "svg", "url": ""},
             {"id": "live2d_haru", "name": "小春 (Live2D)", "type": "live2d", "url": "/static/live2d/haru/haru_greeter_pro_jp.model3.json"}]
    if os.path.exists(MODEL_DIR):
        for fname in sorted(os.listdir(MODEL_DIR)):
            if fname.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                models.append({
                    "id": fname,
                    "name": fname.split("_", 1)[-1],
                    "type": "image",
                    "url": f"/static/models/{fname}"
                })
    return models

@app.delete("/api/admin/models/{filename}")
async def delete_model(filename: str):
    filepath = os.path.join(MODEL_DIR, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return {"status": "ok"}
    return {"error": "文件不存在"}


@app.get("/api/visit")
async def record_visit():
    logger.add_visit()
    return {"status": "ok"}

@app.get("/health")
async def health():
    return {"status": "ok", "uptime": time.time(), "rag_cache": rag.cache_hit_stats(),
            "tts_cache_dir": CACHE_DIR}

if __name__ == "__main__":
    import uvicorn
    print("[SERVER] Running at http://localhost:8000 | Admin: http://localhost:8000/admin")
    uvicorn.run(app, host="0.0.0.0", port=8000)
