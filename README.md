# 灵山胜境 AI 数字人导游（小灵）

> 为灵山胜境景区打造的 AI 数字人导游系统。基于 **Live2D + RAG 知识库**，游客通过文字、语音、图片与可爱的数字人"小灵"对话，即可获得关于灵山大佛、梵宫、五印坛城、九龙灌浴等景点的精准讲解与个性化推荐；回答会合成 TTS 语音，并由 Live2D 数字人做对口型、表情和动作动画。

---

## 目录

- [产品特色](#产品特色)
- [主要功能](#主要功能)
- [总体设计](#总体设计)
- [目录结构](#目录结构)
- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [模型清单](#模型清单)
- [音色列表](#音色列表edge-tts-neural)
- [兴趣偏好标签](#兴趣偏好标签)
- [端到端延迟优化](#端到端延迟优化)
- [部署指南](#部署指南)
- [使用说明](#使用说明)
- [API 接口](#api-接口)
- [知识库文档管理](#知识库文档管理)
- [常见坑 / 注意事项](#常见坑--注意事项)
- [常见问题 FAQ](#常见问题-faq)
- [技术栈一览](#技术栈一览)
- [许可证](#许可证)

---

## 产品特色

- 🎭 **Live2D 数字人形象** — 内置小春（haru）、Nico、Tsumiki、Unitychan、GF、Z16 等多个 Live2D 形象，支持在形象管理页上传自定义 Live2D ZIP 模型；前端 sentiment-analyzer.js 根据回答文本做情绪识别切换开心 / 惊讶 / 生气等表情。
- 🧠 **景区专属 RAG 知识库** — 基于 LangChain + ChromaDB 向量检索 + 通义千问大模型（qwen-plus）精准回答；支持 PDF / DOCX / DOC / TXT / XLSX / XLS / MD 自动解析、切块、向量化。
- 🎤 **全模态交互** — 文字、麦克风语音、上传图片三种提问方式。前端通过 Web Audio API 把录音重采样为 16kHz WAV 直传 `/api/chat/voice16`，**不再需要 ffmpeg 转码**（旧 `/api/chat/voice` 仍保留 WebM→ffmpeg 路径）。
- 🗣️ **端到端语音方案** — FunASR Paraformer-large 本地 ASR（ONNXRuntime + INT8 量化加速）+ Edge-TTS 神经语音合成（6 种中文音色），延迟低至 1~2 秒（热缓存）。
- 💓 **兴趣标签个性化** — 游客勾选 6 个兴趣标签（佛教 / 建筑 / 历史 / 艺术 / 文化 / 自然），系统把标签拼进 RAG system prompt 优先组织相关内容，并附加"您可能也会喜欢…"引导语；标签存 `localStorage['interestTags']` 持久化。
- 📊 **管理员后台** — 数据看板：访问量、满意度、问答热词云（jieba 分词）、每日趋势、意见反馈、五星评分分布，一键导出 CSV / JSON。
- 🖼️ **多模态图片问答** — 集成通义千问 VL Plus，拍摄景点照片即可获得小灵的识别讲解；DashScope 失败时自动降级为纯 RAG 回答，保证不空白。
- ⚡ **多层缓存** — TTS 音频磁盘缓存（`md5(voice|text)` 命名，跨进程复用）+ RAG 答案内存 LRU 缓存 256 条（按 query + tags 维度），热缓存稳定 2 秒返回。
- 🧩 **可扩展文档管理** — 后台一键上传 PDF / DOCX / TXT / XLSX / MD，自动切块入库、重建向量库、清空 RAG 缓存；支持文档删除、一键重建索引，无需改代码即可扩充知识库。

---

## 主要功能

| 模块 | 功能点 |
|------|--------|
| 🎭 数字人 | Live2D 形象加载 / 切换、情绪识别（开心 / 中性 / 惊讶等）、Web Audio 音频能量驱动口型同步、点击互动 |
| 💬 对话 | 文字提问、麦克风语音提问（前端 Web Audio 重采样 16kHz，无需 ffmpeg）、VAD 静音 1.5s 自动结束、预设欢迎语（"你好 / 介绍自己"） |
| 🧠 知识库 | TXT/PDF/DOCX/DOC/XLSX/XLS/MD 解析、LangChain 切块（chunk_size=500 / overlap=60）、ChromaDB 向量存储、相似度 top-5 检索 |
| 🧾 RAG 问答 | 检索增强生成、回答长度 60~120 字、资料缺失回退语、按兴趣标签重写提示词 |
| 🎙️ ASR | FunASR Paraformer-large 模型、FunASR 官方中文 ASR、ONNXRuntime + INT8 量化加速、可选 sensevoice |
| 🔊 TTS | Edge-TTS 6 种中文音色、文本清洗（去 emoji / Markdown）、MP3/WAV 缓存到本地 |
| 🖼️ VL 识别 | 通义千问 VL Plus，上传图片 + 文字描述 → 讲解 + 语音；失败自动降级为纯 RAG |
| 📈 统计 | 访问量 / 互动量 / 满意度 / 五星评分分布 / 关键词云 / 每日趋势 / 情感分析 |
| 🛠️ 管理 | 知识库文档增删 / 索引重建、数字人形象上传 / 切换、静态头像上传、反馈查看、数据导出 |

---

## 总体设计

### 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                      浏览器（前端）                           │
│  index.html · admin.html · avatar-manage.html · Live2D       │
│  Cubism SDK · Pixi.js · Canvas · Web Audio API              │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP / WebSocket
┌──────────────────────────▼──────────────────────────────────┐
│                  FastAPI (uvicorn)  端口 8000                 │
│                                                             │
│   路由层       RAG 引擎        ASR/TTS        日志           │
│   main.py      rag_engine.py   asr_tts.py     logger.py      │
│                                                             │
├──────────────────────┬──────────────────────┬────────────────┤
│   知识库核心          │   大模型 / 云服务      │   本地存储     │
│   knowledge_base.py  │   DashScope HTTP     │   ChromaDB     │
│   LangChain 切块     │   FunASR 本地         │   edge-tts     │
│                      │   Edge-TTS CLI       │   数据/音频    │
└──────────────────────┴──────────────────────┴────────────────┘
```

### 数据流（用户提问 → 语音回答）

```
用户输入
  │
  ├── 文字 ───────────────────────┐
  ├── 语音 (麦克风) ── Web Audio ─► /api/chat/voice16 ─► ASR (FunASR) ─► 文本
  └── 图片 + 文字 ───────────────► /api/chat/image ─► VL (qwen-vl-plus) ─► 文本
                                      │
                                      ▼
                           ┌────── 意图判断（预设欢迎语 / RAG）
                           │
                           ▼
                 知识库检索 (ChromaDB top-5)
                           │
                           ▼
              LLM 生成 (通义千问 qwen-plus)
                           │
                           ▼
                 TTS (Edge-TTS 中文音色)
                           │
                           ▼
                 返回 {answer, audioUrl}
```

---

## 目录结构

```
softwarecup/
├─ backend/                          # FastAPI 服务
│  ├─ main.py                        # 主入口（所有路由）
│  ├─ core/
│  │  ├─ rag_engine.py               # RAG 问答（向量检索 + DashScope HTTP）
│  │  ├─ knowledge_base.py          # 知识库管理（ChromaDB 向量构建）
│  │  ├─ asr_tts.py                  # FunASR（语音识别）+ Edge TTS（语音合成）
│  │  └─ logger.py                   # 交互日志 / 反馈 / 统计 / 词云
│  └─ static/
│     ├─ index.html                  # 游客主页（Live2D + 对话 + 兴趣标签 + 拍照）
│     ├─ admin.html                  # 管理后台
│     ├─ avatar-manage.html          # 形象 / Live2D / 音色管理
│     ├─ avatar.html                 # 形象展示页
│     ├─ js/
│     │  ├─ live2d-manager.js        # Live2D Cubism + PixiJS 渲染与口型
│     │  ├─ sentiment-analyzer.js   # 中文情绪关键词分析
│     │  └─ pixi.min.js
│     ├─ cubism-sdk/                 # Live2D Cubism SDK 官方副本
│     │  ├─ Core/live2dcubismcore(.min).js
│     │  └─ Framework/dist/live2dcubismframework.min.js
│     ├─ live2d-widget/              # 第三方 L2Dwidget 封装
│     ├─ live2d/
│     │  ├─ models.json              # 全部数字人模型清单（自动读写）
│     │  └─ custom_models/*/...      # 上传后的 Live2D ZIP 解压目录
│     └─ (运行时自动生成 avatars/ models/)
├─ data/                             # 知识库与音频产物（与 backend 同级）
│  ├─ raw/                           # 原始知识库文档
│  ├─ processed/                     # 生成的 WAV / 图片临时文件
│  ├─ chroma_storage/                # ChromaDB 向量存储
│  └─ tts_cache/                     # Edge TTS WAV 磁盘缓存（md5(voice|text)）
├─ start.sh / setup.sh               # Linux 一键脚本
├─ docker-compose.yml                # Docker 部署模板
└─ README.md
```

---

## 环境要求

| 类别 | 要求 |
|------|------|
| 操作系统 | Linux / macOS / Windows 10+（推荐 Linux 或 WSL2） |
| Python | 3.10 或以上 |
| CPU | 4 核及以上（ASR 本地推理） |
| 内存 | ≥ 4 GB（推荐 8 GB 以上，FunASR + ChromaDB + 大模型同时驻留） |
| 存储 | ≥ 5 GB（FunASR 模型 ~1.6 GB，向量库 & 文档另算） |
| 网络 | 可访问 `dashscope.aliyuncs.com`（通义千问 / Embedding / VL） |
| 系统工具 | ffmpeg 可选 — 旧 `/api/chat/voice` 路径需要；**新 `/api/chat/voice16` 前端 Web Audio 重采样，无需 ffmpeg** |

### 外部 API Key

| 服务 | 用途 | 环境变量 |
|------|------|---------|
| 阿里云百炼 DashScope | 通义千问 qwen-plus（LLM）+ text-embedding-v4（Embedding）+ qwen-vl-plus（VL） | `DASHSCOPE_API_KEY` |

免费注册：<https://dashscope.console.aliyun.com/>。账号需开通 **qwen-plus** 和 **qwen-vl-plus** 两个模型（通常默认已开通）。

### 其他可配置环境变量

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `DASHSCOPE_API_KEY` | （必填） | 三个云端模型共用 |
| `RAG_MODEL` | `qwen-plus` | 可改 `qwen-turbo`（快 2x）或 `qwen-max`（强） |
| `ASR_MODEL` | `paraformer-large` | FunASR 预设，可选 `sensevoice` |

---

## 快速开始

> Windows PowerShell 建议加 `python -X utf8` 启动以避免控制台中文乱码。

### 方式一：Linux / macOS 一键安装

```bash
cd softwarecup
bash setup.sh
export DASHSCOPE_API_KEY="sk-你的百炼APIKey"
bash start.sh
```

### 方式二：手动安装（通用 / Windows）

```bash
# 1. 创建虚拟环境
cd softwarecup/backend
python -m venv venv

# Windows PowerShell
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate

# 2. 安装依赖
pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install fastapi uvicorn websockets python-multipart httpx numpy pydub
pip install dashscope requests python-dotenv pydantic jieba
pip install chromadb langchain langchain-community langchain-text-splitters
pip install funasr modelscope onnxruntime olefile
pip install edge-tts
pip install pdfplumber python-docx openpyxl xlrd

# 3. 设置 API Key
# Windows PowerShell（临时）
$env:DASHSCOPE_API_KEY="sk-你的百炼APIKey"
# Windows PowerShell（永久）
[Environment]::SetEnvironmentVariable("DASHSCOPE_API_KEY","sk-你的百炼APIKey","User")
# Linux / macOS
export DASHSCOPE_API_KEY="sk-你的百炼APIKey"

# 4. 启动
$env:PYTHONIOENCODING="utf-8"
python -X utf8 main.py
# 或
python -X utf8 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

首次启动 FunASR 会自动从 ModelScope 下载 Paraformer 模型（约 1~1.6 GB），请预留网络。

启动成功控制台会打印：

```
[OK] ASR ready (mode=paraformer)
[OK] Edge TTS ready (Xiaoxiao, cache dir: .../data/tts_cache)
[SERVER] Running at http://localhost:8000 | Admin: http://localhost:8000/admin
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 一键体验流程

1. 浏览器打开 <http://localhost:8000/>
2. 勾选兴趣标签（可选，帮助小灵从你感兴趣的角度回答）
3. 输入框打字对话 → Live2D 小灵会回答、合成语音、做口型
4. 点麦克风 → 语音输入（前端 Web Audio 重采样走 `/api/chat/voice16`，无需 ffmpeg）
5. 点左下"拍照识图" → 选图片 → 输入框问问题 → 回车
6. 点右上"设置" → 换形象、换音色、上传 Live2D
7. 浏览器打开 <http://localhost:8000/admin> → 看运营数据 / 反馈 / 交互历史

### 验证

| URL | 作用 |
|-----|------|
| <http://localhost:8000> | 数字人导游主界面 |
| <http://localhost:8000/admin> | 管理员后台 |
| <http://localhost:8000/static/avatar-manage.html> | 形象 / Live2D / 音色管理 |
| <http://localhost:8000/health> | 健康检查 JSON（含 RAG/TTS 缓存状态） |

---

## 模型清单

| 模块 | 模型 | 平台 / 提供商 | 代码位置 |
|------|------|---------------|----------|
| 文本对话 LLM（RAG 问答核心） | `qwen-plus` | 阿里云百炼 DashScope | [rag_engine.py](file:///d:/softwarecup/softwarecup/backend/core/rag_engine.py#L32) |
| 多模态图文 LLM（图片问答） | `qwen-vl-plus` | 阿里云百炼 DashScope | [main.py](file:///d:/softwarecup/softwarecup/backend/main.py) |
| Embedding 向量模型（RAG 检索用） | `text-embedding-v4` | 阿里云百炼 DashScope | [knowledge_base.py](file:///d:/softwarecup/softwarecup/backend/core/knowledge_base.py#L155) |
| ASR 语音识别 | `paraformer-large`（默认）/ `sensevoice` | 本地 CPU（FunASR） | [asr_tts.py](file:///d:/softwarecup/softwarecup/backend/core/asr_tts.py#L10) |
| 语音合成 TTS | Edge TTS（6 种中文音色，见下） | 微软 Edge TTS CLI | [asr_tts.py](file:///d:/softwarecup/softwarecup/backend/core/asr_tts.py#L48) |

### 替换 Embedding 模型注意事项

Embedding 模型的向量维度会变化（如 v2 → v4），**替换模型后必须**：

1. 重启后端进程
2. 重建向量库（管理后台 → 知识库 → "重新读入数据库"，或 `POST /api/admin/rebuild-index`）

否则旧模型生成的向量和新模型的 query 向量空间不一致，会导致检索失败或结果完全错误。

---

## 音色列表（Edge TTS Neural）

| ID | 名称 | 性别 | 风格 |
|----|------|------|------|
| zh-CN-XiaoxiaoNeural | 晓晓 | 女 | 温暖亲切 |
| zh-CN-XiaoyiNeural | 小艺 | 女 | 活泼可爱 |
| zh-CN-YunjianNeural | 云健 | 男 | 激情有力 |
| zh-CN-YunxiNeural | 云希 | 男 | 阳光清朗 |
| zh-CN-YunxiaNeural | 云霞 | 男 | 温柔可爱 |
| zh-CN-YunyangNeural | 云阳 | 男 | 专业沉稳 |

管理员后台 / 形象管理页点击即可实时切换。

---

## 兴趣偏好标签

游客勾选 6 个标签（佛教 / 建筑 / 历史 / 艺术 / 文化 / 自然）→ 系统把标签拼进 RAG system prompt，回答优先组织相关内容并加"您可能也会喜欢…"引导语。标签存 `localStorage['interestTags']`，切换后所有后续问答自动带标签。

---

## 端到端延迟优化

### 实测

| 场景 | 耗时 |
|------|------|
| TEXT_ONLY 冷缓存 | 4.0 ~ 4.7 s |
| TEXT+TTS 冷缓存 | 6.4 ~ 7.5 s |
| TEXT+TTS 热缓存（RAG+TTS 双命中） | **2.0 s 稳定** |
| 预设问答（你是谁 / 你好 ...） | **2.1 s** |

### 延迟分解（冷缓存，白天非高峰）

```
前端 blobTo16kWav  ~0.1 s
FunASR Paraformer  ~1.5 s
ChromaDB 向量检索  ~0.3 s
DashScope qwen-plus ~1.5~2.5 s
Edge TTS           ~0.8~1.2 s
──────────────────────────────
总计               ~4~5 s（高峰排队时 ~7~9 s）
```

### 已落地优化

1. **LLM 直连 DashScope HTTP**（跳过 OpenAI SDK，qwen-plus ~1.36 s）
2. **FunASR ONNXRuntime + INT8 量化**（CPU 快 2~3x）
3. **前端 Web Audio API 重采样**（砍掉 ffmpeg 转码 0.4~0.6 s，新端点 `/api/chat/voice16`）
4. **VAD 自动结束录音**（静音 1.5 s 自动停止，省掉手动点结束）
5. **asyncio 并行 + run_in_executor**（FunASR / DashScope HTTP 放线程池，Edge TTS 走子进程，多游客不互相阻塞）
6. **RAG 答案 LRU 缓存 256 条**（md5 key，命中跳过检索+LLM）
7. **TTS 磁盘持久化缓存**（`data/tts_cache/`，md5(voice\|text)，进程重启仍命中）

### 可选进一步加速

1. `pip install onnxruntime-gpu`（有 GPU 时 ASR 再快 3~5x）
2. `RAG_MODEL=qwen-turbo`（实测快 2x，高峰排队不稳定）
3. 本地 LLM：`Qwen2.5-0.5B-Instruct-Q4_K_M.gguf` + `llama-cpp-python`，本地推理 0 排队

---

## 部署指南

### Docker 部署（推荐生产环境）

```dockerfile
FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg build-essential curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app/backend

COPY backend/ ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir fastapi uvicorn websockets python-multipart httpx numpy pydub && \
    pip install --no-cache-dir dashscope requests python-dotenv pydantic jieba && \
    pip install --no-cache-dir chromadb langchain langchain-community langchain-text-splitters && \
    pip install --no-cache-dir funasr modelscope onnxruntime olefile && \
    pip install --no-cache-dir edge-tts pdfplumber python-docx openpyxl xlrd

VOLUME ["/app/data"]

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

启动：

```bash
docker run -d -p 8000:8000 \
  -e DASHSCOPE_API_KEY=sk-你的key \
  -v $(pwd)/data:/app/data \
  --name lingshan-guide \
  your-image
```

### systemd 服务（Linux 守护进程）

```ini
# /etc/systemd/system/lingshan.service
[Unit]
Description=Lingshan AI Guide
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/softwarecup/backend
Environment=DASHSCOPE_API_KEY=sk-你的key
ExecStart=/var/www/softwarecup/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable lingshan
sudo systemctl start lingshan
sudo journalctl -u lingshan -f
```

### Nginx 反向代理（HTTPS + WebSocket）

```nginx
server {
    listen 443 ssl http2;
    server_name guide.lingshan.cn;

    ssl_certificate     /etc/letsencrypt/live/guide.lingshan.cn/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/guide.lingshan.cn/privkey.pem;

    client_max_body_size 50m;

    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For  $proxy_add_x_forwarded_for;
        proxy_set_header   Upgrade           $http_upgrade;
        proxy_set_header   Connection        "upgrade";
    }
}
```

---

## 使用说明

### 游客端（首页）

打开 <http://localhost:8000>：

1. **选择数字人形象** — 右上角"设置"或直接下拉切换（小春 / Nico / Tsumiki / Unitychan / GF / Z16 等）。
2. **选择兴趣标签** — 右侧面板 6 个标签（佛教 / 建筑 / 历史 / 艺术 / 文化 / 自然），每行 3 个，勾选后"小灵"回答会优先贴合兴趣。
3. **提问**
   - 📝 文本框直接输入
   - 🎙️ 点击麦克风按钮录音（静音 1.5 s 自动结束，首次需允许浏览器权限；前端 Web Audio 重采样走 `/api/chat/voice16`）
   - 📷 点左下"拍照识图" → 选图片 → 输入文字描述 → 回车走 qwen-vl-plus
4. **收声** — 回答会自动朗读（Edge-TTS），可调节音量；Live2D 数字人会根据音频能量做口型同步，根据回答情绪切换表情。
5. **点赞/点踩 / 星级评分** — 每条回答下方 5 颗星星帮助团队优化；历史三级反馈（good / neutral / bad）自动映射为 5 / 3 / 1 星。

### 管理员后台

打开 <http://localhost:8000/admin>：

**数据看板**
- 今日访客 / 本周访问 / 满意度 / 平均响应时间
- 月度访问趋势 / 每日趋势 / 情感分布
- 关键词云（jieba 分词提取游客高频提问）
- Top 5 问题 / 意见反馈列表 / 五星评分分布

**知识库管理**
- 支持批量上传 `.pdf / .docx / .doc / .txt / .md / .xlsx / .xls`
- 自动解析 → 切块 → 构建 ChromaDB 向量库
- 支持文件删除、一键重建索引
- 所有文档存放在 `data/raw/`

**数字人管理**
- 上传自定义 Live2D 模型（ZIP 包，内含 `.model.json`）
- 上传静态头像（PNG/JPG/GIF）
- 切换不同导游形象

**语音设置**
- 6 种 Edge-TTS 中文音色可选（晓晓 / 小艺 / 云健 / 云希 / 云霞 / 云阳）
- 点击即可实时切换

**数据导出**
- 一键导出交互日志为 CSV 或 JSON

### 预设快速回答（不走大模型）

为常见问题"你是谁 / 介绍自己 / 你好 / 嗨"设置了固定答复，返回更快，也会继续合成 TTS。可在 [main.py](file:///d:/softwarecup/softwarecup/backend/main.py) 的 `PRESET_REPLIES` 中扩充。

---

## API 接口

### 页面

| 方法 | URL | 说明 |
|------|-----|------|
| GET | `/` | 游客主页 |
| GET | `/admin` | 管理后台 |
| GET | `/static/avatar-manage.html` | 形象管理页 |

### 游客端（对话 / 语音 / 图片）

| 方法 | URL | 说明 |
|------|-----|------|
| POST | `/api/chat/tts` | 文字问答 + TTS（`ChatRequest{text, voice, tags}`） |
| POST | `/api/chat/text` | 仅文字问答（不生成语音） |
| POST | `/api/chat/voice` | 语音上传（WebM→ffmpeg→WAV→ASR，旧路径） |
| POST | `/api/chat/voice16` | 语音上传（前端已转 16kHz WAV，跳过 ffmpeg，推荐） |
| POST | `/api/chat/image` | 图片问答（`text` + 文件 `file`，qwen-vl-plus） |
| POST | `/api/chat/clear` | 清空 RAG 缓存 |
| GET  | `/api/audio/{filename}` | 直接返回 WAV 音频 |

### 配置

| 方法 | URL | 说明 |
|------|-----|------|
| POST | `/api/config/set-voice` | 设置 TTS 音色（query: `voice_id`） |
| GET  | `/api/config/voices` | 6 种音色列表 + 当前音色 |

### 反馈与访问

| 方法 | URL | 说明 |
|------|-----|------|
| POST | `/api/feedback` | 1-5 星反馈（兼容 good / neutral / bad） |
| GET  | `/api/visit` | 记录一次访客 |

### 管理后台

| 方法 | URL | 说明 |
|------|-----|------|
| GET  | `/api/admin/dashboard` | 大屏统计 |
| GET  | `/api/admin/recent?limit=20` | 最近交互记录 |
| GET  | `/api/admin/feedbacks` | 用户反馈列表 |
| GET  | `/api/admin/stats/daily` | 近 7 天每日问答量 |
| GET  | `/api/admin/wordcloud` | 热词 Top N |
| GET  | `/api/admin/export?format=json\|csv` | 导出交互日志 |
| GET  | `/api/admin/documents` | 知识库文档列表 |
| POST | `/api/admin/upload-document` | 上传单篇文档（自动重建索引） |
| POST | `/api/admin/upload-documents` | 上传多篇文档（自动重建索引） |
| POST | `/api/admin/delete-document` | 删除单篇文档（自动重建索引） |
| POST | `/api/admin/rebuild-index` | 强制全量重建 ChromaDB |
| GET  | `/api/admin/models` | 数字人列表（2D + Live2D） |
| POST | `/api/admin/models/upload` | 上传 2D 形象图 |
| DELETE | `/api/admin/models/{filename}` | 删除 2D 形象图 |
| POST | `/api/admin/upload-live2d` | 上传 Live2D ZIP（解压 + 写 models.json） |
| DELETE | `/api/admin/delete-live2d/{id}` | 删除自定义 Live2D |
| GET  | `/api/admin/refresh-models` | 刷新模型列表 |
| POST | `/api/admin/upload-avatar` | 形象图上传 |
| DELETE | `/api/admin/avatars/{filename}` | 删除形象图 |
| GET  | `/api/admin/avatars` | 形象图列表 |

### 健康

| 方法 | URL | 说明 |
|------|-----|------|
| GET | `/health` | 健康检查（含 RAG/TTS 缓存状态） |

---

## 知识库文档管理

### 支持格式

| 格式 | 扩展名 | 解析库 |
|------|--------|--------|
| 纯文本 | `.txt` / `.md` | Python 原生（UTF-8 / GBK 自动尝试） |
| PDF | `.pdf` | `pdfplumber` |
| Word | `.docx` / `.doc` | `python-docx`（老版 `.doc` 用 zipfile+正则兜底） |
| Excel | `.xlsx` / `.xls` | `openpyxl` / `xlrd` |

### 上传 / 删除流程

1. 拖拽 / 点击选择文件 → 自动上传 + 自动重建索引
2. 后端保存到 `data/raw/`（同名自动加 `_1` / `_2`）
3. 解析 → 切分（chunk_size=500 / overlap=60）→ 生成 embedding
4. ChromaDB 走 `PersistentClient.delete_collection()` 再重建（避免 Windows 文件锁）
5. 清空 RAG LRU 缓存
6. 管理后台自动刷新文档列表

---

## 常见坑 / 注意事项

- **Windows 文件锁**：删文档后 Chroma 没刷新 → 后端已改为走 Chroma 官方集合删除 API，不再依赖 `shutil.rmtree`。
- **替换 Embedding 模型**：必须重启后端 + 重建索引，否则 query / 文档向量空间不一致导致检索失败（详见"模型清单"章节）。
- **回答带旧内容**：先点"重新读入数据库"；仍然不行则重启后端（让 Chroma 彻底释放锁）。
- **语音输入失败**：浏览器 HTTPS 或 localhost 才能录音；推荐走新 `/api/chat/voice16`（前端 Web Audio 重采样），无需 ffmpeg。
- **数字人口型不匹配 / 音频不播放**：用 Chrome / Edge / Firefox 最新版，建议 HTTPS 或 localhost（浏览器音频策略对非安全源有限制）。
- **控制台中文乱码**：Windows PowerShell 启动时加 `python -X utf8 main.py`，或先执行 `$env:PYTHONIOENCODING="utf-8"`。
- **遗留代码**：[rag_engine.py](file:///d:/softwarecup/softwarecup/backend/core/rag_engine.py#L9) 顶部有一行 Linux 开发机残留 `sys.path.insert(0, '/home/zwy1128/tour-guide-ai/backend')`。Windows / Linux 上都无害（路径不存在 Python 会忽略），后续可安全删掉。

---

## 常见问题 FAQ

**Q1: 启动后第一次对话很慢？**
A: 首次请求 FunASR 会自动下载 Paraformer-large 模型（约 1~1.6 GB），之后走本地推理，延迟降到 <1 s；同时 TTS 也会被首次调用触发。

**Q2: 想扩充景区知识库怎么办？**
A: 打开管理员后台 → "知识库" → 上传 PDF / DOCX / TXT 等 → 系统自动切块并重建向量库。也可以把文件直接放入 `data/raw/` 后访问 `POST /api/admin/rebuild-index`。

**Q3: TTS 音频能换成其它音色吗？**
A: 能。后端内置 6 种 Edge-TTS 神经音色（见"音色列表"章节），管理员后台 / 形象管理页一键切换。

**Q4: 系统返回"抱歉，知识库中暂时没有关于这个问题的资料"？**
A: 说明向量库没有命中任何相关资料：要么知识库文档不全，要么提问超出景区范围。去管理员后台补充相关文档即可。

**Q5: 如何完全重置？**
A: 删除 `data/chroma_storage/`（向量库）、`data/tts_cache/`（音频缓存）、`data/processed/`（上传临时文件）。原始知识库文档保留不动，然后访问 `/api/admin/rebuild-index` 重建。

**Q6: 支持离线部署（无外网）吗？**
A: 目前 RAG LLM + Embedding 依赖阿里云 DashScope，需外网。ASR（FunASR）本地推理无需外网；TTS（Edge-TTS）需联网下载语音。需要离线适配时可把 RAG 模型换成本地 Ollama / Qwen2.5 7B，Embedding 换 BGE-M3 本地模型。

**Q7: Windows 下运行 setup.sh 报错？**
A: setup.sh 是 Linux / macOS Bash 脚本。Windows 请参考"手动安装"章节在 PowerShell 下逐条执行。

**Q8: 响应时间较长？**
A: 实测分解：FunASR ~1.5 s + Chroma ~0.3 s + DashScope 1.5~5 s + Edge TTS 0.8~1.2 s。冷缓存 4~7 s，热缓存 2 s 稳定。详见"端到端延迟优化"章节。

---

## 技术栈一览

| 层 | 技术 |
|----|------|
| 后端框架 | FastAPI · Uvicorn |
| RAG | LangChain · ChromaDB · 通义千问 qwen-plus |
| Embedding | DashScope `text-embedding-v4` |
| 文档解析 | pdfplumber · python-docx · openpyxl · xlrd |
| ASR | FunASR Paraformer-large（FunASR 官方中文 ASR，可选 sensevoice） |
| TTS | Edge-TTS CLI（微软神经语音，6 种音色） |
| VL | 通义千问 VL Plus |
| 语音转码 | 前端 Web Audio API 重采样为主，旧 WebM 路径用 ffmpeg 转码 |
| 前端 | HTML5 · CSS3 · JavaScript |
| 数字人 | Live2D Cubism 4 SDK · Pixi.js · Live2D Widget |
| 情绪分析 | sentiment-analyzer.js（本地规则） |
| 缓存 | TTS 音频 md5 命名本地磁盘缓存 + RAG 答案进程内存 LRU 缓存 256 条 |
| 日志 | JSON 文件 + 文件锁（多线程安全） |

---

## 许可证

本项目仅用于灵山胜境景区 AI 数字导游 Demo / 比赛用途。
