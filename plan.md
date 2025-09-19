# VidSum - 视频智能总结系统

## 项目概述

VidSum 是一个本地运行的视频智能处理系统，通过 URL 自动下载 B 站、YouTube 等平台的视频，并将其转化为可搜索、可跳转的结构化知识内容。

### 核心价值
- **效率提升**：快速定位视频关键内容，节省观看时间
- **知识管理**：将视频转化为可搜索、可索引的知识库
- **交互创新**：点击总结文本即可跳转到对应视频时间点

### 技术特点
- **本地优先**：默认使用本地模型（Whisper + Ollama），保护隐私
- **API 可选**：支持用户自定义 STT 和 LLM 的 API 服务
- **简洁设计**：基于 Prompt 的文本清洗，避免复杂规则系统

## 技术栈

- **后端**：FastAPI (Python)
- **前端**：HTML + JavaScript (轻量级实现)
- **数据库**：SQLite
- **视频下载**：yt-dlp
- **语音识别**：Whisper (本地) / API 可选
- **文本总结**：Ollama (本地) / API 可选
- **端口**：127.0.0.1:3201

## 核心流程

```
URL 输入 → 视频下载 → 音频提取 → 语音识别 → 文本清洗 → 智能分段 → LLM 总结 → 交互展示
```

### 详细处理流程

1. **视频下载**
   - 使用 yt-dlp 支持 B 站、YouTube 等平台
   - 保存到本地`data/videos/`目录

2. **音频分离**
   - FFmpeg 提取音频轨道
   - 临时保存到`data/audio/`

3. **语音识别 (STT)**
   - 默认：Whisper 本地模型（small/medium）
   - 可选：用户自定义 API
   - 输出：带时间戳的 segments

4. **文本清洗**（核心创新）
   - 使用 LLM + Few-shot Prompt 进行清洗
   - 小批量处理防止幻觉（3-5 个 segments 一批）
   - 只改格式不改内容：去除语气词、添加标点、调整换行
   - **支持并行处理**：多批次同时清洗，大幅提升处理速度

5. **智能分段**
   - 基于语义边界检测话题转换
   - 保持段落完整性
   - 每段保留时间戳映射

6. **LLM 总结**
   - 按段落自然边界分批
   - 每批不超过 LLM context 限制
   - **保留时间戳映射**：总结中标注关键点的时间戳
     - 格式示例：`一、概述 [00:00:15]`
     - 格式示例：`1. React 介绍 [00:01:30]`
     - 格式示例：`2. Hooks 使用 [00:05:45]`
   - 简单拼接各批次总结

7. **数据存储**
   - 生成结构化 JSON 文件
   - SQLite 记录视频-JSON 映射关系
   - 支持历史记录管理

8. **交互展示**
   - 视频播放器 + 总结文本联动
   - 点击文本跳转视频时间点
   - 播放时高亮对应段落

## 数据结构设计

### JSON 文件结构
```json
{
  "video_id": 1,
  "url": "https://...",
  "title": "视频标题",
  "duration": 1234,
  "segments": [
    {
      "id": 0,
      "text": "原始转录文本",
      "start": 0.0,
      "end": 2.5
    }
  ],
  "paragraphs": [
    {
      "id": 0,
      "text": "清洗后的段落文本",
      "source_segments": [0, 1, 2],
      "start_time": 0.0,
      "end_time": 30.0,
      "summary": "段落总结内容"
    }
  ],
  "full_summary": "完整视频总结（带时间戳）",
  "summary_with_timestamps": [
    {
      "title": "一、项目介绍",
      "timestamp": "00:00:15",
      "start_seconds": 15,
      "content": "本节介绍了项目的基本概念..."
    },
    {
      "title": "1. 技术架构",
      "timestamp": "00:02:30",
      "start_seconds": 150,
      "content": "详细讲解了系统的技术架构..."
    }
  ]
}
```

### 数据库表结构
```sql
-- 视频表
CREATE TABLE videos (
    id INTEGER PRIMARY KEY,
    url TEXT NOT NULL,
    platform TEXT,
    title TEXT,
    duration INTEGER,
    file_path TEXT,
    status TEXT,
    created_at TIMESTAMP
);

-- 转录表
CREATE TABLE transcripts (
    id INTEGER PRIMARY KEY,
    video_id INTEGER REFERENCES videos(id),
    json_path TEXT,
    provider TEXT,
    status TEXT,
    created_at TIMESTAMP
);

-- 总结表
CREATE TABLE summaries (
    id INTEGER PRIMARY KEY,
    transcript_id INTEGER REFERENCES transcripts(id),
    content TEXT,
    provider TEXT,
    model_name TEXT,
    created_at TIMESTAMP
);

-- 设置表
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP
);
```

## 文本清洗策略（基于 Prompt）

### 清洗 Prompt 模板
```python
CLEANING_PROMPT = """
你是一个文本格式整理助手。你的任务是将口语化的语音转录文本整理成易读的书面格式。

重要规则：
1. 只能调整格式，不能改变内容含义
2. 可以去除语气词（嗯、啊、呃、这个、那个）
3. 可以添加标点符号让句子更通顺
4. 可以调整换行让段落更清晰
5. 保留所有实质性内容

示例：
【原始文本】
嗯今天我们来讲一下这个 React 的 hooks 啊大家知道...

【整理后】
今天我们来讲一下 React 的 hooks。大家知道...

现在请整理下面的文本：
【原始文本】
{text}

【整理后】
"""
```

### 批处理策略
- Ollama 3B 模型：3 个 segments 一批
- Ollama 7B 模型：5 个 segments 一批
- API 模型：10 个 segments 一批
- **并行处理**：将所有批次同时提交处理，显著提升效率
  - 例如：100 个 segments 分成 20 批，20 批并行处理
  - 使用 asyncio 或 ThreadPoolExecutor 实现并发

## 项目结构

```
VidSum/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI 主应用
│   │   ├── config.py            # 配置管理
│   │   ├── models.py            # 数据模型
│   │   ├── database.py          # 数据库连接
│   │   ├── api/
│   │   │   ├── video.py         # 视频相关 API
│   │   │   ├── process.py       # 处理流程 API
│   │   │   └── settings.py      # 配置 API
│   │   └── services/
│   │       ├── downloader.py    # yt-dlp 封装
│   │       ├── transcriber.py   # STT 服务
│   │       ├── text_cleaner.py  # 文本清洗
│   │       └── summarizer.py    # LLM 总结
│   └── requirements.txt
├── frontend/
│   ├── index.html               # 主页面
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── app.js              # 主逻辑
│       ├── player.js           # 播放器控制
│       └── settings.js         # 设置管理
├── data/
│   ├── videos/                 # 视频文件
│   ├── audio/                  # 音频文件 (临时)
│   └── transcripts/            # JSON 文件
├── database/
│   └── vidsum.db              # SQLite 数据库
├── models/                     # 本地模型
│   └── whisper/
├── .env.example               # 环境变量示例
├── .gitignore
├── README.md
├── setup.sh                   # 安装脚本
└── plan.md                    # 本文档
```

## 配置设计

```python
class Settings:
    # 服务器配置
    host: str = "127.0.0.1"
    port: int = 3201

    # STT 配置
    stt_provider: str = "whisper_local"  # 默认本地
    whisper_model: str = "small"
    stt_api_key: str = ""                # 用户可填
    stt_api_endpoint: str = ""           # 用户可填

    # LLM 配置
    llm_provider: str = "ollama"         # 默认本地
    ollama_model: str = "qwen2.5:7b"
    ollama_host: str = "http://localhost:11434"
    llm_api_key: str = ""                # 用户可填
    llm_api_endpoint: str = ""           # 用户可填

    # 文本清洗
    cleaning_batch_size: int = 5         # 默认 5 个 segments 一批
    use_llm_for_cleaning: bool = True    # 使用 LLM 清洗
```

## 前端界面设计

### 主页面布局
```
┌─────────────────────────────────────────┐
│            URL 输入栏 + 下载按钮           │
├─────────────────────────────────────────┤
│                                         │
│          视频播放器 (60%)               │
│                                         │
├─────────────────────────────────────────┤
│                                         │
│      总结文本区域 (40%)                  │
│      - 可点击跳转                       │
│      - 自动高亮当前段落                  │
│                                         │
└─────────────────────────────────────────┘
```

### 设置页面
```
STT 设置：
├── 模式选择：[本地 Whisper] [API]
├── (本地) 模型大小：[small/medium]
└── (API) Key: [____] Endpoint: [____]

LLM 设置：
├── 模式选择：[Ollama] [API]
├── (Ollama) 模型：[qwen2.5:7b]
└── (API) Key: [____] Endpoint: [____]
```

## 实施步骤

### 第一阶段：基础架构（Day 1-2）
- [ ] 创建项目结构
- [ ] 配置 FastAPI 框架
- [ ] 设置 SQLite 数据库
- [ ] 实现配置管理系统

### 第二阶段：视频处理（Day 3-4）
- [ ] 集成 yt-dlp
- [ ] 实现视频下载功能
- [ ] FFmpeg 音频提取
- [ ] 文件管理系统

### 第三阶段：语音识别（Day 5-6）
- [ ] Whisper 本地集成
- [ ] API 模式支持
- [ ] 时间戳处理
- [ ] 结果存储

### 第四阶段：文本处理（Day 7-9）
- [ ] 实现 Prompt-based 清洗
- [ ] 批处理逻辑
- [ ] 段落边界检测
- [ ] 时间戳映射保持

### 第五阶段：智能总结（Day 10-11）
- [ ] Ollama 集成
- [ ] 分批总结策略
- [ ] API 模式支持
- [ ] 结果整合

### 第六阶段：前端开发（Day 12-14）
- [ ] 基础页面布局
- [ ] 视频播放器
- [ ] 文本展示和交互
- [ ] 设置界面
- [ ] WebSocket 进度推送

### 第七阶段：测试优化（Day 15-16）
- [ ] 端到端测试
- [ ] 性能优化
- [ ] 错误处理
- [ ] 文档完善

## 关键技术要点

### 1. 小批量处理防止 LLM 幻觉
- 控制每批处理的 segments 数量
- 根据模型能力动态调整批大小

### 2. 时间戳映射保持
- 清洗和分段过程中保持原始时间戳
- 建立段落到 segments 的映射关系

### 3. 自然段落边界作为 LLM 分批边界
- 利用段落完整性自然切分
- 避免在语义中间截断

### 4. 本地优先，API 可选
- 降低使用门槛
- 保护数据隐私
- 提供扩展能力

## 依赖清单

### Python 包
```txt
# Core
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23

# Video/Audio
yt-dlp==2024.1.0
ffmpeg-python==0.2.0

# AI/ML
openai-whisper==20231117
ollama==0.1.7
openai==1.6.1  # Optional

# Utils
pydantic==2.5.2
python-dotenv==1.0.0
aiofiles==23.2.1
websockets==12.0
```

### 系统要求
- Python 3.9+
- FFmpeg
- 8GB+ RAM (推荐 16GB)
- 10GB+ 存储空间

### 本地模型
- Whisper small/medium
- Ollama + qwen2.5:7b (或其他 7B 模型)

## 注意事项

1. **隐私保护**：所有处理默认在本地完成
2. **成本控制**：本地模型无 API 费用
3. **灵活配置**：支持切换到 API 服务
4. **简洁设计**：避免过度工程化
5. **用户体验**：重点关注核心功能的流畅性

## 后续优化方向

- 支持更多视频平台
- 批量视频处理
- 更智能的段落划分
- 多语言支持优化
- 导出功能（Markdown/PDF）
- 搜索和标签系统

---

*Last Updated: 2025-01-18*