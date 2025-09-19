# VidSum - 视频智能总结系统

将视频转化为可搜索、可跳转的结构化知识内容。

## 功能特点

- 🎬 支持 B 站、YouTube 等平台视频下载
- 🎯 自动语音识别和文本转录
- 🤖 智能文本清洗和段落整理
- 📝 AI 驱动的内容总结
- 🔍 点击总结文本即可跳转到对应视频时间点
- 🔒 本地优先，保护隐私

## 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd VidSum
```

### 2. 创建虚拟环境

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

### 3. 安装依赖

```bash
# 安装 Python 依赖
pip install -r backend/requirements.txt

# 安装系统依赖
# macOS:
brew install ffmpeg

# Linux:
sudo apt-get install ffmpeg

# Windows:
# 从 https://ffmpeg.org/download.html 下载并安装
```

### 4. 配置本地模型

```bash
# 安装 Ollama (可选，用于本地 LLM)
curl -fsSL https://ollama.com/install.sh | sh

# 下载推荐的模型
ollama pull qwen2.5:7b

# Whisper 模型会在首次运行时自动下载
```

### 5. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env 文件，配置你的 API 密钥（可选）
```

### 6. 启动服务

```bash
# 在虚拟环境中启动后端服务
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 3201 --reload
```

访问 http://127.0.0.1:3201 即可使用。

## 项目结构

```
VidSum/
├── backend/          # FastAPI 后端
├── frontend/         # Web 前端
├── data/            # 数据存储
│   ├── videos/      # 视频文件
│   ├── audio/       # 音频文件
│   └── transcripts/ # 转录文件
├── database/        # SQLite 数据库
├── models/          # 本地模型
└── venv/           # Python 虚拟环境
```

## 技术栈

- **后端**: FastAPI + SQLAlchemy
- **前端**: HTML + JavaScript
- **数据库**: SQLite
- **AI 模型**: Whisper (STT) + Ollama/OpenAI (LLM)
- **视频处理**: yt-dlp + FFmpeg

## 配置说明

### 本地模式（默认）

- STT: Whisper 本地模型
- LLM: Ollama 本地模型
- 无需 API 密钥，完全离线运行

### API 模式（可选）

在设置页面可以配置：
- OpenAI API
- 其他兼容的 API 服务

## 系统要求

- Python 3.9+
- 8GB+ RAM（推荐 16GB）
- 10GB+ 存储空间
- FFmpeg

## 开发

```bash
# 激活虚拟环境
source venv/bin/activate

# 安装开发依赖
pip install -r backend/requirements-dev.txt

# 运行测试
pytest

# 代码格式化
black backend/
```

## 常见问题

1. **Q: 如何处理长视频？**
   A: 系统会自动分段处理，确保不超过 LLM 的 context 限制。

2. **Q: 支持哪些语言？**
   A: Whisper 支持多语言，包括中文、英文等主流语言。

3. **Q: 可以离线使用吗？**
   A: 是的，默认配置完全支持离线使用。

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可

MIT License

---

更多详细信息请参考 [plan.md](./plan.md)