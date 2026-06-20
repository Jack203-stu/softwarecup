# 灵山胜境 AI 数字人导游（小灵）

一个基于 **Live2D + RAG 知识库** 的景区智能导游系统。游客可以通过文字、语音或图片向"小灵"提问，系统返回带 TTS 语音的回答，并由 Live2D 数字人做对口型、表情和动作动画。

## 功能概览

- **Live2D 数字人**：支持多个内置形象（小春 haru、Nico、Tsumiki、Unitychan、GF、Z16 等），可在形象管理页上传自定义 Live2D ZIP 模型。
- **RAG 智能问答**：基于灵山胜境景区知识库，融合向量检索（ChromaDB / LangChain）+ 大模型推理。
- **多模态交互**：文字问答 / 语音问答（FunASR ASR）/ 图片问答（DashScope `qwen-vl-plus`）。
- **语音播报 & 对口型**：Edge TTS 合成 WAV 音频，前端 Web Audio 根据音频能量驱动口型动画。
- **表情分析**：前端 sentiment-analyzer.js 根据回答文本分析情绪，切换开心 / 惊讶 / 生气等表情。
- **音色切换**：6 种中文音色（晓晓 / 小艺 / 云健 / 云希 / 云霞 / 云阳）。
- **运营后台**：`/admin` 数据大屏（今日人次、近 7 天、满意度、交互历史、导出 JSON/CSV）、知识库文档管理、形象管理。
- **形象 / 背景管理**：上传 / 删除 PNG/JPG 形象图与背景图；管理 Live2D 模型列表。
- **交互日志**：自动记录每次问答（问题、答案、耗时、来源）与用户反馈。

## 运行要求

- Python 3.10+
- FFmpeg（用于把 webm 转码为 16kHz WAV）
- 8GB+ 内存（FunASR + Chroma + 大模型推理）
- Windows / Linux / macOS
- 网络连接（调用阿里云百炼 / DashScope API）

## 快速开始

### 1. 安装 Python 依赖

项目根目录下没有 `requirements.txt`，请按下面清单安装：

```bash
pip install fastapi uvicorn
pip install edge-tts funasr chromadb langchain openai dashscope pydantic python-multipart
pip install websockets httpx numpy pydub
```

> FunASR 首次启动会自动下载模型（约 1GB），请预留网络。

### 2. 配置 API Key

```powershell
# Windows PowerShell
$env:DASHSCOPE_API_KEY="your-dashscope-key"

# Windows CMD
set DASHSCOPE_API_KEY=your-dashscope-key

# Linux/macOS
export DASHSCOPE_API_KEY="your-dashscope-key"
```

### 3. 启动服务

```bash
cd backend
python main.py
# 或
uvicorn main:app --host 0.0.0.0 --port 8000
```

启动后控制台会打印：

```
[SERVER] Running at http://localhost:8000 | Admin: http://localhost:8000/admin
```

### 4. 访问地址

- 游客主页：http://localhost:8000/
- 管理后台：http://localhost:8000/admin
- 形象管理：http://localhost:8000/static/avatar-manage.html

主页右上角：
- **设置**：当前页跳转到 `/static/avatar-manage.html`（形象 / 音色管理）
- **驾驶舱**：在新标签页打开 `/admin`

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
│  ├─ raw/                     # 原始知识库文档 (.txt / .pdf / .docx)
│  ├─ processed/               # 生成的 WAV / 图片临时文件
│  └─ chroma_storage/          # ChromaDB 向量存储
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
| POST | `/api/feedback` | 提交反馈（`{rating: "good"|"neutral"|"bad"}`） |
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
| POST | `/api/admin/upload-document` | 上传知识库文档 |
| POST | `/api/admin/rebuild-index` | 重建 ChromaDB 向量索引 |
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

- 数据大屏：今日服务、近 7 天、满意度、交互历史、导出 JSON/CSV
- 知识库：上传 `.txt/.pdf/.docx`，手动触发重建向量索引
- 形象管理：上传 PNG/JPG 模型图；上传 / 删除 Live2D ZIP

## 常见问题

**Q: 没有 requirements.txt？**
项目未随代码附带依赖清单，请按"快速开始"中的 pip 命令安装。

**Q: 为什么语音输入失败？**
需要本机安装 `ffmpeg` 并在 PATH 中，用于把浏览器录制的 WebM 转码为 16kHz WAV。

**Q: 数字人口型不匹配 / 音频不播放？**
使用 Chrome / Edge / Firefox 最新版，建议用 HTTPS 或 `localhost`（浏览器音频策略对非安全源有限制）。

**Q: 响应时间较长？**
FunASR ASR 约 1-2 秒，RAG 检索约 1-2 秒，LLM 推理约 2-4 秒，Edge TTS 约 1-2 秒。

**Q: 如何新增知识库内容？**
把 `.txt / .pdf / .docx` 放到 `data/raw/`，访问管理后台 → 知识库 → 重建向量索引。

**Q: 可以用 https 部署吗？**
可以。推荐 Nginx 反向代理到 `http://127.0.0.1:8000`，并给静态资源（`/static/`）开启缓存。

## 许可证

MIT License
