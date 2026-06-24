"""灵山胜境 AI数字人导游"""
import os, sys, uuid, subprocess, shutil, time
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, Response
from pydantic import BaseModel
import sqlite3
import traceback

# 第一步：先设置环境变量（必须放在最前面！）
os.environ["DASHSCOPE_API_KEY"] = "sk-7d9eb5d3d31d4eddaed244c54742f2b7"

# 你的路径
BASE_DIR = r"C:\Users\van\Desktop\aaa\t2\tour-guide-ai\backend"
sys.path.insert(0, BASE_DIR)

from core.rag_engine import RAGEngine
from core.asr_tts import ASRService, TTSService
from core.data_analyzer import DataAnalyzer
from core.file_library import FileLibrary
from database import (
    record_session, get_today_sessions, record_qa, normalize_question,
    record_unsatisfied, get_dashboard_data, reset_stats
)

app = FastAPI(title="灵山胜境AI导游")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# 现在加载服务就不会报错了
rag = RAGEngine()
asr = ASRService()
tts = TTSService()
analyzer = DataAnalyzer()
library = FileLibrary()

# 数据库路径
DB_PATH = os.path.join(BASE_DIR, "data", "stats.db")

class ChatRequest(BaseModel):
    text: str

# ============ 页面 ============
@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = os.path.join(BASE_DIR, "static", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()

# ============ 文字+语音 ============
@app.post("/api/chat/tts")
async def text_to_speech(req: ChatRequest):
    result = rag.answer(req.text)
    audio_file = f"reply_{uuid.uuid4()}.wav"
    audio_path = os.path.join(BASE_DIR, "..", "data", "processed", audio_file)
    tts.synthesize(result['answer'], audio_path)
    return {
        "question": result['question'],
        "answer": result['answer'],
        "audio_url": f"/api/audio/{audio_file}"
    }

# ============ 纯文字 ============
@app.post("/api/chat/text")
async def text_chat(req: ChatRequest):
    result = rag.answer(req.text)
    return {
        "question": result['question'],
        "answer": result['answer'],
        "sources": result['sources']
    }

# ============ 语音输入 ============
@app.post("/api/chat/voice")
async def voice_chat(file: UploadFile = File(...)):
    webm_file = f"{uuid.uuid4()}.webm"
    wav_file = webm_file.replace(".webm", ".wav")
    
    webm_path = os.path.join(BASE_DIR, "..", "data", "processed", webm_file)
    wav_path = os.path.join(BASE_DIR, "..", "data", "processed", wav_file)

    with open(webm_path, "wb") as f:
        f.write(await file.read())

    subprocess.run([
        "ffmpeg", "-y",
        "-i", webm_path,
        "-ar", "16000",
        "-ac", 1,
        "-f", "wav",
        wav_path
    ], capture_output=True)

    user_text = asr.transcribe(wav_path) or "未识别到语音"
    result = rag.answer(user_text)
    
    reply_file = f"reply_{uuid.uuid4()}.wav"
    reply_path = os.path.join(BASE_DIR, "..", "data", "processed", reply_file)
    tts.synthesize(result['answer'], reply_path)

    return {
        "user_text": user_text,
        "reply_text": result['answer'],
        "audio_url": f"/api/audio/{reply_file}"
    }

# ============ 音频播放 ============
@app.get("/api/audio/{filename}")
async def get_audio(filename: str):
    audio_path = os.path.join(BASE_DIR, "..", "data", "processed", filename)
    if not os.path.exists(audio_path):
        return Response(status_code=404)
    with open(audio_path, "rb") as f:
        return Response(content=f.read(), media_type="audio/wav")

# ============ 管理后台 ============
@app.get("/admin", response_class=HTMLResponse)
async def admin():
    admin_path = os.path.join(BASE_DIR, "static", "admin.html")
    with open(admin_path, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/admin/dashboard")
async def dashboard():
    stats = analyzer.get_core_stats()
    return {
        "today_visitors": stats["total_visitors"],
        "satisfaction_rate": stats["avg_satisfaction"] / 5.0,
        "peak_hour": f"{stats['peak_hour']}:00",
        "avg_stay_minutes": stats["avg_stay_minutes"],
        "hot_spots": analyzer.get_hot_spots()
    }

@app.get("/api/admin/report")
async def admin_report():
    return {"report": analyzer.get_full_report()}

@app.get("/health")
async def health():
    return {"status": "ok"}

# ============ 统计API ============
@app.post("/api/stats/visit")
async def api_record_visit(request: Request):
    """记录一次访问（打开窗口），返回今日会话数"""
    try:
        session_id = request.headers.get("X-Session-Id")
        if not session_id:
            session_id = str(uuid.uuid4())
        today_sessions = record_session(session_id)
        print(f"[统计] 会话记录: session_id={session_id}, today_sessions={today_sessions}")
        return {"session_id": session_id, "today_sessions": today_sessions}
    except Exception as e:
        print(f"[统计错误] 会话记录失败: {e}")
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

@app.post("/api/stats/qa")
async def api_record_qa(request: Request):
    """记录一次问答"""
    try:
        data = await request.json()
        session_id = data.get("session_id", "")
        user_query = data.get("user_query", "")
        ai_answer = data.get("ai_answer", "")
        response_time = data.get("response_time", 0)
        
        print(f"[统计] 问答记录: session_id={session_id}, query={user_query[:30] if user_query else '空'}...")
        
        normalized = normalize_question(user_query)
        record_qa(session_id, user_query, normalized, ai_answer, response_time)
        print(f"[统计] 问答记录成功")
        return {"status": "ok"}
    except Exception as e:
        print(f"[统计错误] 问答记录失败: {e}")
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

@app.post("/api/stats/unsatisfied")
async def api_record_unsatisfied(request: Request):
    """记录不满意反馈"""
    try:
        data = await request.json()
        session_id = data.get("session_id", "")
        user_query = data.get("user_query", "")
        reason = data.get("reason", "")
        record_unsatisfied(session_id, user_query, reason)
        print(f"[统计] 不满意反馈记录成功: session_id={session_id}")
        return {"status": "ok"}
    except Exception as e:
        print(f"[统计错误] 不满意反馈记录失败: {e}")
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

@app.get("/api/stats/dashboard")
async def api_get_dashboard():
    """获取数据大屏全部数据（基底+真实）"""
    try:
        return get_dashboard_data()
    except Exception as e:
        print(f"[统计错误] 获取数据大屏失败: {e}")
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

@app.post("/api/stats/reset")
async def api_reset_stats():
    """重置数据到基底"""
    try:
        reset_stats()
        return {"status": "ok", "message": "数据已重置"}
    except Exception as e:
        print(f"[统计错误] 重置失败: {e}")
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

# ============ Debug 接口 ============
@app.get("/debug/db")
async def debug_db():
    """查看数据库各表记录数"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sessions")
        sessions = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM qa_records")
        qa = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM unsatisfied_feedback")
        fb = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM hot_questions")
        hot = cursor.fetchone()[0]
        conn.close()
        return {
            "sessions": sessions,
            "qa_records": qa,
            "unsatisfied_feedback": fb,
            "hot_questions": hot,
            "db_path": DB_PATH
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/debug/qa")
async def debug_qa():
    """查看最近的问答记录"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT session_id, user_query, normalized_query, response_time, created_at 
            FROM qa_records 
            ORDER BY id DESC 
            LIMIT 10
        """)
        rows = cursor.fetchall()
        conn.close()
        return {
            "recent_qa": [
                {
                    "session_id": r[0],
                    "user_query": r[1],
                    "normalized_query": r[2],
                    "response_time": r[3],
                    "created_at": r[4]
                }
                for r in rows
            ]
        }
    except Exception as e:
        return {"error": str(e)}

# ============ 文件库接口 ============
@app.get("/api/admin/files")
async def list_files():
    return {"files": library.list_files()}

@app.post("/api/admin/files/upload")
async def upload_file(file: UploadFile = File(...)):
    file_id = library.upload_file(file.filename, await file.read())
    return {"file_id": file_id, "name": file.filename}

@app.delete("/api/admin/files/{file_id}")
async def delete_file(file_id: str):
    success = library.delete_file(file_id)
    return {"success": success}

# ============ 官方资料管理（只读） ============
OFFICIAL_DIR = os.path.join(BASE_DIR, "..", "data", "raw")

@app.get("/api/admin/official-files")
async def get_official_files():
    """获取官方资料文件列表（只读，不可删除）"""
    files = []
    if not os.path.exists(OFFICIAL_DIR):
        return {"files": []}
    
    for fname in os.listdir(OFFICIAL_DIR):
        if fname.endswith('.txt'):
            file_path = os.path.join(OFFICIAL_DIR, fname)
            stat = os.stat(file_path)
            files.append({
                "name": fname,
                "size": stat.st_size,
                "modified": stat.st_mtime
            })
    return {"files": files}

@app.get("/api/admin/official-files/{filename}")
async def get_official_file_content(filename: str):
    """查看官方资料文件内容（只读预览）"""
    if '..' in filename or '/' in filename or '\\' in filename:
        return Response(status_code=400)
    
    file_path = os.path.join(OFFICIAL_DIR, filename)
    if not os.path.exists(file_path) or not filename.endswith('.txt'):
        return Response(status_code=404)
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    return {"filename": filename, "content": content}

# ============ 知识库刷新 ============
@app.post("/api/admin/refresh-knowledge")
async def refresh_knowledge():
    """手动刷新知识库，重新读取 LEVEL1/LEVEL2 文件"""
    try:
        result = rag.refresh_knowledge()
        return result
    except Exception as e:
        print(f"❌ 刷新知识库失败: {e}")
        return {"status": "error", "message": str(e)}

# ============ LEVEL1 / LEVEL2 文件管理 ============
LEVEL1_DIR = r"C:\Users\van\Desktop\aaa\t2\tour-guide-ai\data\library\level1"
LEVEL2_DIR = r"C:\Users\van\Desktop\aaa\t2\tour-guide-ai\data\library\level2"

os.makedirs(LEVEL1_DIR, exist_ok=True)
os.makedirs(LEVEL2_DIR, exist_ok=True)

# 上传文件
@app.post("/api/upload/{level}")
async def upload_file(level: str, file: UploadFile = File(...)):
    target_dir = LEVEL1_DIR if level == "level1" else LEVEL2_DIR
    path = os.path.join(target_dir, file.filename)
    print(f"===== 上传文件: {file.filename} -> {path} =====")
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    print("===== 保存成功 =====")
    return {"status": "ok"}

# 获取文件列表
@app.get("/api/files/list")
async def get_files():
    def list_dir(d):
        if not os.path.exists(d):
            return []
        return [f for f in os.listdir(d) if os.path.isfile(os.path.join(d, f))]
    return {
        "level1": list_dir(LEVEL1_DIR),
        "level2": list_dir(LEVEL2_DIR)
    }

# 删除文件
@app.delete("/api/delete/{level}/{fname}")
async def del_file(level: str, fname: str):
    from urllib.parse import unquote
    
    target_dir = LEVEL1_DIR if level == "level1" else LEVEL2_DIR
    decoded_fname = unquote(fname)
    
    if '/' in decoded_fname or '\\' in decoded_fname or '..' in decoded_fname:
        return {"status": "error", "message": "非法文件名"}
    
    file_path = os.path.join(target_dir, decoded_fname)
    
    print(f"===== 删除文件: {file_path} =====")
    
    if os.path.isfile(file_path):
        os.remove(file_path)
        print(f"===== 删除成功 =====")
        return {"status": "ok", "message": f"已删除 {decoded_fname}"}
    else:
        print(f"===== 文件不存在: {file_path} =====")
        return {"status": "error", "message": "文件不存在"}

# ============ 在线编辑文件内容 ============
@app.get("/api/file-content/{level}/{filename}")
async def get_file_content(level: str, filename: str):
    """获取 LEVEL1/LEVEL2 文件内容（用于在线编辑）"""
    from urllib.parse import unquote
    
    if '..' in filename or '/' in filename or '\\' in filename:
        return {"status": "error", "message": "非法文件名"}
    
    target_dir = LEVEL1_DIR if level == "level1" else LEVEL2_DIR
    decoded_filename = unquote(filename)
    file_path = os.path.join(target_dir, decoded_filename)
    
    if not os.path.exists(file_path):
        return {"status": "error", "message": "文件不存在"}
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"status": "ok", "content": content}
    except UnicodeDecodeError:
        try:
            with open(file_path, "r", encoding="gbk") as f:
                content = f.read()
            return {"status": "ok", "content": content}
        except Exception as e:
            return {"status": "error", "message": f"读取文件失败: {str(e)}"}

@app.put("/api/file-content/{level}/{filename}")
async def save_file_content(level: str, filename: str, req: dict):
    """保存 LEVEL1/LEVEL2 文件内容（在线编辑后保存）"""
    from urllib.parse import unquote
    
    if '..' in filename or '/' in filename or '\\' in filename:
        return {"status": "error", "message": "非法文件名"}
    
    target_dir = LEVEL1_DIR if level == "level1" else LEVEL2_DIR
    decoded_filename = unquote(filename)
    file_path = os.path.join(target_dir, decoded_filename)
    
    if not os.path.exists(file_path):
        return {"status": "error", "message": "文件不存在"}
    
    content = req.get("content", "")
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"===== 文件已保存: {file_path} =====")
        return {"status": "ok", "message": "文件保存成功"}
    except Exception as e:
        return {"status": "error", "message": f"保存失败: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 启动成功：http://localhost:8000")
    print("🏢 管理后台：http://localhost:8000/admin")
    print("🔍 Debug接口：http://localhost:8000/debug/db")
    uvicorn.run(app, host="127.0.0.1", port=8000)