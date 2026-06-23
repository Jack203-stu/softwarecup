# 灵山胜境 AI 数字人导游（小灵）

一个基于 **Live2D + RAG 知识库** 的景区智能导游系统。游客可以通过文字、语音或图片向"小灵"提问，系统返回带 TTS 语音的回答，并由 Live2D 数字人做对口型、表情和动作动画。

## 功能概览

- **Live2D 数字人**：支持多个内置形象（小春 haru、Nico、Tsumiki、Unitychan、GF、Z16 等），可在形象管理页上传自定义 Live2D ZIP 模型。
- **RAG 智能问答**：基于灵山胜境景区知识库，融合向量检索（ChromaDB / LangChain）+ 大模型推理。
- **多模态交互**：文字问答 / 语音问答（FunASR ASR）/ 图片问答（DashScope `qwen-vl-plus`）。
- **语音播报 & 对口型**：Edge TTS 合成 WAV 音频，前端 Web Audio 根据音频能量驱动口型动画。
- **表情分析**：前端 sentiment-analyzer.js 根据回答文本分析情绪，切换开心 / 惊讶 / 生气等表情。
- **音色切换**：6 种中文音色（晓晓 / 小艺 / 云健 / 云希 / 云霞 / 云阳）。
- **运营后台**：`/admin` 数据大屏（今日人次、近 7 天、满意度、交互历史、导出 JSON/CSV）、知识库文档管理（支持 txt/pdf/docx/doc/xlsx/xls 自动学习与重建向量库）、反馈五星评级、形象管理。
- **形象 / 背景管理**：上传 / 删除 PNG/JPG 形象图与背景图；管理 Live2D 模型列表。
- **交互日志**：自动记录每次问答（问题、答案、耗时、来源）与用户**五星评价**反馈。
- **知识库多格式解析**：后端内置解析器，自动处理 `.txt` / `.pdf` / `.docx` / `.doc` / `.xlsx` / `.xls`，切分后向量化存 ChromaDB；上传或删除后自动重建索引并清空 RAG 缓存。

## 运行要求

- Python 3.10+
- FFmpeg（用于把 webm 转码为 16kHz WAV）
- 8GB+ 内存（FunASR + Chroma + 大模型推理）
- Windows / Linux / macOS
- 网络连接（调用阿里云百炼 / DashScope API）

## 快速开始

> 推荐 **Python 3.10+**，在 Windows PowerShell 5 下建议加 `python -X utf8` 启动以避免控制台中文乱码。

### 1. 安装依赖

项目未附带 `requirements.txt`，请一次性执行下面命令：

```bash
pip install fastapi uvicorn pydantic python-multipart websockets httpx numpy pydub
pip install edge-tts funasr chromadb langchain openai dashscope
```

首次启动 FunASR 会自动从 ModelScope 下载 Paraformer 模型（约 1GB），请预留网络。

**系统依赖**（仅语音输入需要）：

- **FFmpeg**：把浏览器录制的 WebM 转码为 16kHz WAV。Windows 可用 `winget install Gyan.FFmpeg`，装完重开终端，`ffmpeg -version` 能跑即可。
- **8GB+ 内存**（FunASR + ChromaDB + 大模型推理同时驻留）。

### 2. 配置 API Key

项目依赖阿里云百炼 DashScope：RAG 问答调用 `qwen-plus`，拍照识图调用 `qwen-vl-plus`。在 [阿里云百炼控制台](https://dashscope.console.aliyun.com/) 申请 API Key 后：

```powershell
# Windows PowerShell（临时，当前终端有效）
$env:DASHSCOPE_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxx"

# Windows CMD
set DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxx

# Windows PowerShell（永久，用户级，下次开终端自动生效）
[Environment]::SetEnvironmentVariable("DASHSCOPE_API_KEY","sk-xxxxxxxxxxxxxxxxxxxxxxxxxx","User")

# Linux / macOS
export DASHSCOPE_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxx"
```

> 账号需开通百炼控制台里 **qwen-plus** 和 **qwen-vl-plus** 两个模型（通常默认已开通）。

### 大语言模型清单

项目使用阿里云百炼（DashScope）平台上的通义千问（Qwen）系列，以及本地 FunASR 语音模型。全部列在下表：

| 模块 | 模型 | 平台 / 提供商 | 代码位置 |
|------|------|---------------|----------|
| 文本对话 LLM（RAG 问答核心） | `qwen-plus` | 阿里云百炼 DashScope | [rag_engine.py](file:///d:/softwarecup/backup/softwarecup/backend/core/rag_engine.py#L32) |
| 多模态图文 LLM（图片问答） | `qwen-vl-plus` | 阿里云百炼 DashScope | [main.py](file:///d:/softwarecup/backup/softwarecup/backend/main.py#L346) |
| Embedding 向量模型（RAG 检索用） | `text-embedding-v4` | 阿里云百炼 DashScope | [knowledge_base.py](file:///d:/softwarecup/backup/softwarecup/backend/core/knowledge_base.py#L156) |
| ASR 语音识别 | `paraformer-small`（默认）/ `paraformer-large` / `sensevoice` | 本地 CPU（FunASR） | [asr_tts.py](file:///d:/softwarecup/backup/softwarecup/backend/core/asr_tts.py) |

#### 模型切换

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `DASHSCOPE_API_KEY` | （必填） | DashScope API Key，上述三个云端模型共用 |
| `RAG_MODEL` | `qwen-plus` | RAG 对话模型，可改 `qwen-turbo`（快）或 `qwen-max`（强） |
| `ASR_MODEL` | `paraformer-small` | FunASR 预设，可选 `paraformer-large` 或 `sensevoice` |

#### 替换 Embedding 模型注意事项

Embedding 模型的向量维度在升级版本时会变化（如 v2 → v4），**替换模型后必须**：

1. **重启后端进程**（让 Python 加载新的模型名称）
2. **重建向量库**（管理后台 → 知识库 → "重新读入数据库"，或 `POST /api/admin/rebuild-index`）

否则旧模型生成的向量和新模型的 query 向量空间不一致，会导致检索失败或结果完全错误，同时账单持续产生旧模型费用。

### 3. 启动服务

```powershell
# Windows PowerShell（推荐，-X utf8 避免中文乱码）
cd .\backend
$env:PYTHONIOENCODING="utf-8"
python -X utf8 main.py

# 或用 uvicorn
cd .\backend
python -X utf8 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

启动成功后控制台会打印：

```
[OK] ASR ready
[OK] Edge TTS ready (Xiaoxiao)
[SERVER] Running at http://localhost:8000 | Admin: http://localhost:8000/admin
```

### 4. 访问地址

| 页面 | URL | 说明 |
|---|---|---|
| 游客主页 | http://localhost:8000/ | Live2D + 对话 + 拍照识图 |
| 管理后台 | http://localhost:8000/admin | 数据大屏 / 知识库 / 反馈 / 形象 |
| 形象管理 | http://localhost:8000/static/avatar-manage.html | 上传 Live2D / 切换音色 |

主页右上角：
- **设置** → 当前页跳转到 `/static/avatar-manage.html`（不再新开标签页）
- **驾驶舱** → 新标签页打开 `/admin`

### 5. 一键体验流程

1. 浏览器打开 http://localhost:8000/
2. 输入框打字对话 → Live2D 小灵会回答、合成语音、做口型
3. 点麦克风 → 语音输入（需要浏览器麦克风权限 + FFmpeg）
4. 点左下"拍照识图" → 选图片 → 输入框问问题 → 回车
5. 点右上"设置" → 换形象、换音色、上传 Live2D
6. 浏览器打开 http://localhost:8000/admin → 看运营数据 / 反馈 / 交互历史

## 目录结构

```
softwarecup/
├─ backend/                    # FastAPI 服务
│  ├─ main.py                  # 主入口（所有路由）
│  ├─ config.py                # 预留配置
│  ├─ core/
│  │  ├─ rag_engine.py         # RAG 问答（向量检索 + LLM 推理）
│  │  ├─ knowledge_base.py     # 知识库管理（向量库构建）
│  │  ├─ asr_tts.py            # FunASR（语音识别）+ Edge TTS（语音合成）
│  │  └─ logger.py             # 交互日志 / 反馈 / 统计
│  └─ static/
│     ├─ index.html            # 游客主页（带 Live2D 显示 + 对话）
│     ├─ admin.html            # 管理后台页面
│     ├─ avatar-manage.html    # 形象 / 背景 / 音色管理页面
│     ├─ avatar.html
│     ├─ js/
│     │  ├─ live2d-manager.js        # Live2D Cubism + PixiJS 渲染与口型
│     │  ├─ sentiment-analyzer.js    # 中文情绪关键词分析
│     │  ├─ pixi.min.js
│     │  └─ live2dcubismcore.min.js / live2dcubismframework.min.js
│     ├─ cubism-sdk/           # Live2D Cubism SDK Core / Framework
│     ├─ live2d/
│     │  ├─ models.json                      # 全部数字人模型清单
│     │  └─ custom_models/*/...              # 上传后的 Live2D ZIP 解压目录
│     ├─ backgrounds/          # 景区背景图
│     └─ (avatars/  models/)   # 运行时生成（上传时写入）
├─ data/                       # 知识库与音频产物（与 backend 同级）
│  ├─ raw/                     # 原始知识库文档 (.txt / .pdf / .docx / .doc / .xlsx / .xls)
│  ├─ processed/               # 生成的 WAV / 图片临时文件
│  ├─ chroma_storage/          # ChromaDB 向量存储（注意：替换文档需重建索引）
│  └─ tts_cache/               # Edge TTS 合成 WAV 磁盘缓存（md5(voice|text)）
└─ README.md
```

## API 接口

### 页面

| 方法 | URL | 说明 |
|------|-----|------|
| GET | `/` | 游客主页 |
| GET | `/admin` | 管理后台 |
| GET | `/static/avatar-manage.html` | 形象管理页 |

### 游客端（对话 / 语音）

| 方法 | URL | 说明 |
|------|-----|------|
| POST | `/api/chat/tts` | 文字问答 + 返回 TTS WAV（`ChatRequest{text, voice}`） |
| POST | `/api/chat/text` | 仅文字问答（不生成语音） |
| POST | `/api/chat/voice` | 语音上传问答（multipart，字段 `file`，WebM→WAV→ASR） |
| POST | `/api/chat/image` | 图片问答（`text` + 文件字段 `file`，DashScope `qwen-vl-plus`） |
| POST | `/api/chat/clear` | 清空对话历史（调用 `rag.clear_history()`） |
| GET  | `/api/audio/{filename}` | 直接返回合成好的 WAV |

### 配置（音色等）

| 方法 | URL | 说明 |
|------|-----|------|
| POST | `/api/config/set-voice` | 设置 TTS 音色（query: `voice_id`） |
| GET  | `/api/config/voices` | 返回支持的 6 种音色与当前音色 |

### 反馈与访问

| 方法 | URL | 说明 |
|------|-----|------|
| POST | `/api/feedback` | 提交 1-5 星反馈（兼容旧 good/neutral/bad） |
| GET  | `/api/visit` | 记录一次访客 |

### 管理后台

| 方法 | URL | 说明 |
|------|-----|------|
| GET  | `/api/admin/dashboard` | 运营大屏统计 |
| GET  | `/api/admin/recent?limit=20` | 最近交互记录 |
| GET  | `/api/admin/feedbacks` | 用户反馈列表 |
| GET  | `/api/admin/stats/daily` | 近 7 天每日问答量 |
| GET  | `/api/admin/export?format=json|csv` | 导出交互日志 |
| GET  | `/api/admin/documents` | 知识库文档列表 |
| POST | `/api/admin/upload-document` | 上传单篇文档（自动重建索引） |
| POST | `/api/admin/upload-documents` | 上传多篇文档（自动重建索引） |
| POST | `/api/admin/delete-document` | 删除单篇文档（自动重建索引） |
| POST | `/api/admin/rebuild-index` | 重新读入数据库（按 data/raw 全量重建 ChromaDB） |
| GET  | `/api/admin/models` | 数字人模型列表 |
| POST | `/api/admin/models/upload` | 上传模型图片 |
| DELETE | `/api/admin/models/{filename}` | 删除模型图片 |
| POST | `/api/admin/upload-live2d` | 上传 Live2D 模型 ZIP（自动解压并写 `models.json`） |
| DELETE | `/api/admin/delete-live2d/{id}` | 删除自定义 Live2D 模型 |
| GET  | `/api/admin/refresh-models` | 刷新模型列表占位 |
| POST | `/api/admin/upload-avatar` | 形象图上传 |
| DELETE | `/api/admin/avatars/{filename}` | 删除形象图 |
| GET  | `/api/admin/avatars` | 形象图列表 |
| POST | `/api/admin/upload-background` | 背景图上传 |
| DELETE | `/api/admin/delete-background/{filename}` | 删除背景图 |
| GET  | `/api/admin/backgrounds` | 背景图列表 |

### 其他

| 方法 | URL | 说明 |
|------|-----|------|
| GET  | `/health` | 健康检查 |

## 音色列表（Edge TTS Neural）

| ID | 名称 | 性别 | 风格 |
|----|------|------|------|
| zh-CN-XiaoxiaoNeural | 晓晓 | 女 | 温暖亲切 |
| zh-CN-XiaoyiNeural | 小艺 | 女 | 活泼可爱 |
| zh-CN-YunjianNeural | 云健 | 男 | 激情有力 |
| zh-CN-YunxiNeural | 云希 | 男 | 阳光清朗 |
| zh-CN-YunxiaNeural | 云霞 | 男 | 温柔可爱 |
| zh-CN-YunyangNeural | 云阳 | 男 | 专业沉稳 |

## 内置形象（models.json）

系统内置多种 Live2D Cubism 与 2D 形象。`models.json` 结构示例：

```json
{
  "id": "shizuku",
  "name": "雫·优雅女士",
  "type": "live2d",
  "modelUrl": "/static/live2d/.../shizuku.model.json",
  "voice": "zh-CN-XiaoxiaoNeural",
  "custom": false
}
```

上传 ZIP 后的自定义模型会追加一条 `custom: true` 记录。

## 预置快速回答（不走大模型）

为常见问题"你是谁 / 介绍自己 / 你好 / 嗨"设置了固定答复，返回更快，也会继续合成 TTS。可在 `backend/main.py` 的 `PRESET_REPLIES` 中扩充。

## 使用说明

### 游客端

1. 打开 http://localhost:8000/
2. 右上角 **设置** → 当前页跳转到形象管理页，选择形象与音色；**返回主页**继续对话。
3. 输入框输入问题，或点麦克风进行语音输入。
4. 回答返回后：音频自动播放，Live2D 模型会做口型与情绪表情。

### 形象管理页（avatar-manage.html）

- 选择 / 预览 Live2D 形象
- 上传 Live2D ZIP（需含 `.model.json`）
- 上传 / 删除 PNG/JPG 形象与背景
- 切换 TTS 音色

### 管理后台（/admin）

- 数据大屏：今日服务、近 7 天、五星评价分布（1-5 星柱子 + 平均星数）、交互历史、导出 JSON/CSV
- 知识库：拖拽 / 点击选文件（支持 txt / md / pdf / docx / doc / xlsx / xls，可多选）→ 选完立即自动上传并重建索引；每一行含「删除」按钮；「重新读入数据库」按钮手动强制全量重建
- 形象管理：上传 PNG/JPG 模型图；上传 / 删除 Live2D ZIP

## 知识库文档管理

### 支持格式

| 格式 | 扩展名 | 解析库 | 说明 |
|------|--------|--------|------|
| 纯文本 | `.txt` / `.md` | Python 原生 | UTF-8 / GBK 自动尝试 |
| PDF | `.pdf` | `pypdf` | 文本型 PDF；扫描版需 OCR（未启用） |
| Word | `.docx` / `.doc` | `python-docx` | 老版 `.doc` 需后端装 `textract`/`antiword` |
| Excel | `.xlsx` / `.xls` | `openpyxl` / `xlrd` | 所有 sheet 合并读取 |

```bash
# 如尚未安装这些解析库
pip install python-docx openpyxl xlrd pypdf
```

### 上传流程（管理后台 `/admin` → 知识库）

1. 拖拽 / 点击选择文件（支持多选） → **选完立即自动上传 + 重建索引**（无需点按钮）
2. 后端保存到 `data/raw/`
3. 解析 → 切分（512 token / 100 重叠） → 生成 embedding
4. ChromaDB 里 `delete_collection('lingshan_knowledge')` 再重建（避免 Windows 文件锁导致的 shutil.rmtree 静默失败）
5. 清空 RAG 回答 LRU 缓存（`rag.clear_history()`）
6. 管理后台自动刷新文档列表

### 删除流程

1. 点某文件行的「删除」按钮 → 后端 `POST /api/admin/delete-document`
2. 删除 `data/raw/<filename>`
3. 自动重建 ChromaDB 向量库 + 清 RAG 缓存
4. **RAG 的 system prompt 明确禁止输出文件名 / 来源**，仅用参考资料内容回答

### 手动重建

知识库页面「重新读入数据库」按钮 → `POST /api/admin/rebuild-index`，相当于强制按 `data/raw/` 当前所有文件重建。

### 常见坑

- **删了文件但回答没变**：Windows 下 `shutil.rmtree(chroma_storage)` 遇到 Chroma 文件被运行中的 Python 进程占用会静默失败。本项目已改为先调 `chromadb.PersistentClient().delete_collection("lingshan_knowledge")` 走 Chroma 官方的集合删除 API。
- **新文档没生效**：上传后看页面上的「向量化 chunk 数」是否变大；可以在游客端 `http://localhost:8000/api/chat/text` 里直接用 HTTP GET 试一个相关问题。
- **回答里还带旧内容**：如果文档确实已被修改但还回答旧内容，先点「重新读入数据库」；仍然不行则重启后端（让 Chroma 彻底释放锁）。

## 五星评价反馈

### 游客端

- `http://localhost:8000/` 每条回答下方有 5 颗星星，hover 高亮，点击选定
- localStorage 记住最近一次评分，下次进入自动高亮
- POST `/api/feedback` 接受 `rating: 1|2|3|4|5`

### 管理后台

- `/admin` → 数据大屏：五个星级柱子 + 平均星数
- 情感趋势（近 7 天）折线图：每条星级一条线（1~5）
- 用户反馈页面：列表含评星、问题、时间

### 旧数据兼容

历史三级反馈（满意 / 一般 / 不满意）被**映射迁移**为五星，保留已有记录不删除：

```
old "good"    → 5
old "neutral" → 3
old "bad"     → 1
```

实现见 [logger.py](file:///d:/softwarecup/softwarecup/backend/core/logger.py) 的 `_rating_to_stars()` / `_stars_to_category()`。

### API

`POST /api/feedback` 请求体可接受 `rating` 为数字（1-5）或字符串（"1"~"5" / "good" / "neutral" / "bad"）。

## 拍照识图（多模态图片问答）

### 功能说明

主页左下"拍照识图"按钮提供图片问答能力：上传一张照片，即可让小灵结合景区知识描述图中景物、回答相关问题。底层使用阿里云百炼的 **DashScope `qwen-vl-plus`** 多模态大模型（视觉+文本双模态）。

### 交互流程

1. 点击"拍照识图"按钮（`input[type=file]`，accept=`image/*`，移动端自动调起摄像头，PC 端打开文件选择器）
2. 选中图片后，底部对话输入栏左侧自动出现**小缩略图 + ✕ 取消**，输入框 placeholder 变为"想问图片里什么？直接回车就能识别"
3. 用户可输入自定义问题（例如"这是灵山的哪个景点？有什么历史？"）或直接回车
4. 后端把图片 + 问题一起 POST 到 `/api/chat/image`，调用 `qwen-vl-plus` 生成回答
5. 回答返回后自动合成 TTS WAV，Live2D 数字人做口型与表情
6. 输入栏缩略图自动清除，回到纯文字对话态

> 全部走**同一个**底部输入框，不再出现独立的图片对话框。

### 后端实现

路由位于 [main.py #L185-L233](file:///d:/softwarecup/softwarecup/backend/main.py#L185-L233)：

```python
@app.post("/api/chat/image")
async def image_chat(text: str = Form(""), file: UploadFile = File(...)):
    img_bytes = await file.read()
    img_path = f"../data/processed/img_{uuid.uuid4().hex[:8]}.jpg"
    ...
    from dashscope import MultiModalConversation
    response = MultiModalConversation.call(
        model="qwen-vl-plus",
        messages=[
            {"role":"system","content":[{"text":"你是灵山胜境景区的AI导游小灵..."}]},
            {"role":"user","content":[
                {"image": f"file://{os.path.abspath(img_path)}"},
                {"text": text or "请描述这张图片"}
            ]}
        ],
        api_key=os.getenv("DASHSCOPE_API_KEY")
    )
```

返回 JSON：`{"answer": "...", "audioUrl": "/api/audio/reply_xxx.wav"}`

**异常降级**：若 DashScope 调用失败，会自动退化为用 RAG 只回答文字问题（无图），保证用户不会收到空白。

### 前端实现（index.html）

| 元素 / 函数 | 作用 |
|---|---|
| `#visionFileInput`（隐藏 input[type=file]） | 触发文件选择，accept=`image/*` |
| `#visionThumbs`（输入栏左侧缩略图条） | 选中图片后出现，含 ✕ 取消 |
| `pendingVisionFile`（全局变量） | 暂存选中的图片 File 对象 |
| `onVisionFile(input)` | 选中图片 → 写缩略图 src + 聚焦输入框 + 改 placeholder |
| `sendVisionMessage(question)` | POST `/api/chat/image`，成功后清 pending / 清缩略图 |
| `cancelVisionQuestion()` | 清 pending + 清缩略图 + 还原 placeholder |
| `sendMessage()` | 若 `pendingVisionFile !== null` 则走 `sendVisionMessage`，否则走普通文字分支 |

图片大小限制 ≤ 15MB（超过会 toast 提示）。

### 文本清洗（去 emoji）

多模态大模型偶尔会在回答里夹带 emoji / 符号（如 😊 ✨ 等），TTS 无法正确朗读。[rag_engine.py #remove_emoji](file:///d:/softwarecup/softwarecup/backend/core/rag_engine.py#L10-L23) 使用 **Unicode 类别**过滤：

- `So`（Symbol, Other）— emoji
- `Sk`（Symbol, Modifier）— emoji 修饰符
- `Cf`（Format）里码位 ≥ `0xFE00` 的变体选择符

**不会删除中文**（汉字归类于 `Lo` / `Ll` / `Lt` 等，均保留）。`main.py` 也有一份相同逻辑供直接 import。

### 依赖

```bash
pip install dashscope python-multipart
```

并设置环境变量 `DASHSCOPE_API_KEY`（见上文"配置 API Key"）。账号需要开通百炼控制台里的 **qwen-vl-plus** 模型权限（通常默认已开通）。

### 日志记录

每次图片问答都会被 `logger.add(text, clean_answer, source="image")` 记入 [interaction_log.json](file:///d:/softwarecup/softwarecup/data/interaction_log.json)，在管理后台 `/admin` 的"实时交互动态"和导出 JSON/CSV 中可以看到 `source: "image"` 的来源标记。

## 端到端延迟优化

### 现状

语音问答端到端流程（用户说完话 → 听到回答），串行链路：

```
用户录音（前端 MediaRecorder）
  → 音频文件写入 / 转码  →  FunASR 语音识别  →  RAG 向量检索 + DashScope LLM  →  Edge TTS 合成  →  播放
     IO / ffmpeg               2~3s              4~6s                         1~2s
```

冷缓存原耗时约 7~9s（高峰排队更长）。以下为已落地的优化，实测冷缓存 **4~7s**（白天非高峰 ~4s），热缓存稳定 **2s 左右**。

### 实测数据（qwen-plus，直连 DashScope）

| 场景 | 耗时 |
|---|---|
| TEXT_ONLY 冷缓存（向量检索 0.3s + DashScope） | 4.0~4.7s |
| TEXT+TTS 冷缓存（向量 + LLM + Edge TTS） | 6.4~7.5s |
| TEXT+TTS 热缓存（RAG 答案 + TTS 双命中） | **2.0s 稳定** |
| 预设问答（你是谁 / 你好 ...） | **2.1s** |

### 优化清单

#### 1. LLM：直连 DashScope HTTP（跳过 OpenAI SDK）

**文件**：[rag_engine.py](file:///d:/softwarecup/softwarecup/backend/core/rag_engine.py)

- 用 `requests.Session().post()` 直连 `https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions`
- 不走 OpenAI SDK（首次调用额外握手）
- 实测直连 qwen-plus **1.36s**，qwen-turbo **0.62s**（纯 HTTP，含排队）
- 环境变量可切换模型：`RAG_MODEL=qwen-plus`（默认，稳定）/ `qwen-turbo`（极快但高峰排队）

#### 2. ASR：ONNXRuntime + INT8 量化 + Paraformer Small

**文件**：[asr_tts.py](file:///d:/softwarecup/softwarecup/backend/core/asr_tts.py)

- FunASR `AutoModel(quantize=True)` → INT8 量化，CPU 推理快 2~3x
- ONNXRuntime 后端（启动日志会打印 `ASR backend=onnxruntime quantize=on`）
- 默认模型从 Paraformer-large 改为 Paraformer-small（省 0.5GB 内存 + 识别快 1s）
- 可选 `ASR_MODEL=sensevoice`（FunASR 新模型，tiny，识别 10s 音频 CPU 1~2s）

```powershell
# 切换 ASR 模型（可选）
$env:ASR_MODEL="paraformer-small"   # 默认
$env:ASR_MODEL="sensevoice"          # 更轻量，可能更准
$env:ASR_MODEL="paraformer-large"    # 更准，更慢
```

#### 3. 前端：Web Audio API 重采样（跳过 FFmpeg）

**文件**：[index.html](file:///d:/softwarecup/softwarecup/backend/static/index.html) — `blobTo16kWav()`

- `AudioContext.decodeAudioData` 解码 WebM OPUS → Float32 PCM
- 重采样到 16kHz mono → Int16 PCM → 手拼标准 WAV 头
- POST `/api/chat/voice16`（新端点，[main.py](file:///d:/softwarecup/softwarecup/backend/main.py)），后端直接喂 ASR
- **砍掉 FFmpeg 转码 0.4~0.6s**；失败时 fallback 旧 `/api/chat/voice`

#### 4. 前端：VAD 自动结束录音

**文件**：[index.html](file:///d:/softwarecup/softwarecup/backend/static/index.html) — `_startVAD()`

- `AnalyserNode` 实时检测音频能量（平均振幅 < 8 即静音）
- 用户说完话后 **静音 1.5s 自动停止** 发送请求
- 最短录音 1.2s（防误触发），最长 25s
- 省掉用户手动点结束按钮的时间，录音更短 → ASR 更快
- 同时开启 `echoCancellation / noiseSuppression / autoGainControl`

#### 5. 后端：asyncio 并行 + 不阻塞事件循环

**文件**：[main.py](file:///d:/softwarecup/softwarecup/backend/main.py)

- ffmpeg / edge-tts 用 `asyncio.create_subprocess_exec` + `await proc.communicate()`
- FunASR（同步 torch 模型）放到 `run_in_executor(None, asr.transcribe)` 线程池
- DashScope HTTP（同步）放到 `run_in_executor(None, rag.answer, ...)`
- **多游客并发互不阻塞**；Edge TTS 合成不再卡其他请求

#### 6. RAG 答案 LRU 缓存

**文件**：[rag_engine.py](file:///d:/softwarecup/softwarecup/backend/core/rag_engine.py)

- `md5(question.strip().lower())` 作为缓存 key，上限 256 条
- 命中时跳过 **向量检索 (~0.3s) + DashScope LLM (~1-5s)**，直接返回答案
- 景区问答高频问题（"你是谁 / 门票 / 大佛有多高"）极易命中 → 延迟从 5-8s 降到 **2s**

#### 7. TTS 磁盘持久化缓存

**文件**：[asr_tts.py](file:///d:/softwarecup/softwarecup/backend/core/asr_tts.py)

- `data/tts_cache/` 目录，`md5(voice|text)` 作为 key，缓存 Edge TTS WAV 产物
- 内存 + 磁盘两级缓存，进程重启后仍能命中
- 预设回答（你是谁 / 你好 / 嗨 ...）所有游客共享同一个缓存文件
- 命中缓存时 **跳过 Edge TTS (~1-2s)**

### 延迟分解（冷缓存，白天非高峰）

```
前端 blobTo16kWav        ~0.1s
POST 上传                ~0.05s
FunASR Paraformer        ~1.5s  （quantize + onnxruntime 已启用）
ChromaDB 向量检索        ~0.3s
DashScope qwen-plus      ~1.5~2.5s（高峰排队更长）
Edge TTS                 ~0.8~1.2s（高峰排队更长）
──────────────────────────────────────
总计                     ~4~5s   （高峰排队时 ~7-9s）
```

### 可选进一步加速（高峰排队时）

1. **`pip install onnxruntime-gpu`**（如有 GPU）→ ASR 再快 3~5x
2. **`RAG_MODEL=qwen-turbo`**（实测快 2x，但高峰排队不稳定）
3. **本地 LLM**：下载 `Qwen2.5-0.5B-Instruct-Q4_K_M.gguf` (~300MB)，用 llama-cpp-python 本地推理 → 0 排队 + 1~2s 推理（需把景区知识 prompt 改小以减少上下文）
4. **llama-cpp-python**：`pip install llama-cpp-python`，本地模型笔记本 CPU 回答也能 2s 以内

## 常见问题

**Q: 没有 requirements.txt？**
项目未随代码附带依赖清单，请按"快速开始"中的 pip 命令安装。

**Q: 为什么语音输入失败？**
需要本机安装 `ffmpeg` 并在 PATH 中（或前端已启用 Web Audio API 重采样走 `/api/chat/voice16`，此时无需 ffmpeg）。

**Q: 数字人口型不匹配 / 音频不播放？**
使用 Chrome / Edge / Firefox 最新版，建议用 HTTPS 或 `localhost`（浏览器音频策略对非安全源有限制）。

**Q: 响应时间较长？**
FunASR + ONNXRuntime 1.5s，ChromaDB 向量检索 0.3s，DashScope qwen-plus 1.5-5s（高峰排队），Edge TTS 0.8-1.2s。冷缓存约 4-7s，热缓存（RAG+TTS 双命中）约 2s。详见"端到端延迟优化"章节。

**Q: 如何新增知识库内容？**
把 `.txt / .pdf / .docx` 放到 `data/raw/`，访问管理后台 → 知识库 → 重建向量索引。

**Q: 可以用 https 部署吗？**
可以。推荐 Nginx 反向代理到 `http://127.0.0.1:8000`，并给静态资源（`/static/`）开启缓存。

## 许可证

MIT License
