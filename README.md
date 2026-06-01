# 灵山胜境 AI数字人导游

一个基于 Live2D 数字人和 RAG 知识库的智能导游系统，数字人能够实时语音播报、对口型并展示丰富的表情。

## 系统要求

- Python 3.10+
- 8GB+ 内存
- Windows/Linux/macOS
- 网络连接（用于调用阿里云百炼 API）

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置 API Key

设置阿里云百炼 API Key：

```bash
# Linux/macOS
export DASHSCOPE_API_KEY="your-api-key"

# Windows (PowerShell)
$env:DASHSCOPE_API_KEY="your-api-key"

# Windows (CMD)
set DASHSCOPE_API_KEY=your-api-key
```

### 3. 启动服务

```bash
cd backend
python main.py
# 或使用 uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 4. 访问应用

- 游客端：http://localhost:8000
- 形象管理：http://localhost:8000/static/avatar-manage.html

## 主要功能

### 🎭 数字人形象

- **9个内置形象**：小灵、雫、小春、阳斗、小黑、多罗罗、未来、艾普西隆、响、千岁
- **自定义上传**：支持上传 Live2D 模型（ZIP格式）添加自定义形象
- **实时预览**：在管理页面预览不同形象

### 🔊 语音功能

- **语音播报**：数字人能够实时语音播报回答内容
- **对口型**：语音与口型动画精确同步
- **音色选择**：支持6种中文音色（晓晓、小艺、云健、云希、云霞、云阳）
- **语音输入**：支持语音输入问题

### 😊 表情互动

- **情感分析**：根据回答内容分析情感
- **表情动画**：开心、惊讶、生气等多种表情
- **时间线动画**：表情随回答内容动态变化

### 📚 知识库

- **RAG 问答**：基于灵山胜境景区知识的智能问答
- **向量检索**：使用 ChromaDB 进行语义检索
- **快速回答**：常见问题预设回答，无需调用大模型

## 目录结构

```
backend/
├── main.py              # 主服务入口
├── core/
│   ├── asr_tts.py       # 语音识别与合成
│   ├── rag_engine.py     # RAG 问答引擎
│   ├── knowledge_base.py # 知识库管理
│   └── logger.py         # 交互日志
├── static/
│   ├── index.html        # 主页
│   ├── avatar-manage.html # 形象管理页面
│   └── live2d/           # Live2D 模型资源
├── data/
│   ├── raw/              # 原始知识库文本
│   ├── processed/         # 生成的音频文件
│   └── chroma_storage/   # 向量数据库
└── models.json           # 形象配置
```

## 配置文件

### models.json

每个形象的配置项：

```json
{
  "id": "shizuku",
  "name": "雫·优雅女士",
  "modelUrl": "/static/live2d/node_modules/live2d-widget-model-shizuku/assets/shizuku.model.json",
  "voice": "zh-CN-XiaoxiaoNeural",
  "type": "live2d"
}
```

### 可用音色

| 音色 ID | 名称 | 性别 | 风格 |
|---------|------|------|------|
| zh-CN-XiaoxiaoNeural | 晓晓 | 女 | 温暖亲切 |
| zh-CN-XiaoyiNeural | 小艺 | 女 | 活泼可爱 |
| zh-CN-YunjianNeural | 云健 | 男 | 激情有力 |
| zh-CN-YunxiNeural | 云希 | 男 | 阳光清朗 |
| zh-CN-YunxiaNeural | 云霞 | 男 | 温柔可爱 |
| zh-CN-YunyangNeural | 云阳 | 男 | 专业沉稳 |

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 主页 |
| `/api/chat/tts` | POST | 文字转语音问答 |
| `/api/chat/voice` | POST | 语音输入问答 |
| `/api/config/set-voice` | POST | 设置音色 |
| `/api/config/voices` | GET | 获取音色列表 |
| `/api/admin/upload-live2d` | POST | 上传自定义形象 |
| `/api/admin/delete-live2d/{id}` | DELETE | 删除自定义形象 |

## 技术栈

- **后端**：FastAPI + Uvicorn
- **语音合成**：Edge TTS
- **语音识别**：FunASR
- **知识库**：ChromaDB + LangChain + 阿里云百炼
- **前端**：PixiJS + pixi-live2d-display + Live2D Cubism
- **实时动画**：Web Audio API（口型同步）

## 使用说明

### 游客端使用

1. 打开主页 http://localhost:8000
2. 选择喜欢的数字人形象（通过"管理"按钮）
3. 在输入框输入问题或使用语音输入
4. 数字人将语音播报回答并配合口型和表情

### 形象管理

1. 访问 http://localhost:8000/static/avatar-manage.html
2. **选择形象**：点击卡片上的"选择"按钮
3. **预览形象**：点击"预览"按钮查看效果
4. **上传形象**：拖拽或选择 Live2D 模型 ZIP 文件
5. **选择音色**：在页面顶部选择语音音色

### 添加自定义形象

1. 准备 Live2D 模型文件（需包含 .model.json）
2. 压缩为 ZIP 格式
3. 在管理页面上传
4. 上传成功后自动出现在列表中

## 注意事项

- API Key 需要从阿里云百炼平台申请
- 首次使用会自动下载 ASR 模型（约 1GB）
- 向量知识库只需构建一次，后续启动会复用
- 建议使用 Chrome/Firefox/Edge 等现代浏览器

## 常见问题

**Q: 数字人口型不匹配怎么办？**
A: 确保使用 HTTPS 或 localhost 访问，浏览器音频策略可能限制非安全源。

**Q: 响应时间较长？**
A: RAG 检索约 1-2 秒，LLM 推理约 2-3 秒，TTS 合成约 1-2 秒。

**Q: 如何添加更多知识库内容？**
A: 在 `backend/data/raw/` 目录下添加 .txt 文件，然后重新构建知识库。

## 许可证

MIT License
