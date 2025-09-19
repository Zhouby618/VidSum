# VidSum MVP - 使用指南

## 🎯 项目简介

VidSum MVP 是一个视频智能转录和总结系统，能够：
- 🎥 将视频文件（FLV 等格式）转换为音频
- 🎤 使用 Whisper 进行高质量语音转录
- ✨ 使用 Ollama + deepseek-r1:14b 进行文本清洗
- 📝 生成结构化的内容总结，包含时间戳标记

## 📋 前置要求

### 1. 系统依赖

```bash
# 安装 FFmpeg (macOS)
brew install ffmpeg

# 安装 FFmpeg (Ubuntu/Debian)
sudo apt-get install ffmpeg

# 验证安装
ffmpeg -version
```

### 2. Whisper 环境

```bash
# 创建 Whisper 虚拟环境（如果还没有）
python3 -m venv ~/whisper-env

# 激活环境
source ~/whisper-env/bin/activate

# 安装 Whisper
pip install openai-whisper

# 验证安装
whisper --help
```

### 3. Ollama 配置

```bash
# 安装 Ollama（访问 https://ollama.ai）
# macOS: brew install ollama

# 启动 Ollama 服务
ollama serve

# 在新终端中拉取 deepseek-r1:14b 模型
ollama pull deepseek-r1:14b

# 验证模型
ollama list
```

### 4. Python 环境

```bash
# 进入 MVP 目录
cd /Users/zhou/Documents/Projects_DevEnv/VidSum/VidSum/mvp

# 激活虚拟环境
source venv/bin/activate

# 安装依赖（如果还没安装）
pip install -r requirements.txt
```

## 🚀 快速开始

### 基础用法：处理单个视频

```bash
# 激活虚拟环境
cd mvp
source venv/bin/activate

# 处理单个视频文件
python main.py /path/to/videos --single /path/to/video.flv
```

### 批量处理：处理整个目录

```bash
# 处理指定目录下的所有 FLV 文件
python main.py "/Users/zhou/Documents/Projects_DevEnv/temp/opt/bili_rec/7531557-未明子"

# 指定输出目录
python main.py /path/to/videos -o my_output

# 处理其他格式的视频
python main.py /path/to/videos --pattern "*.mp4"
```

## 🎮 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `video_dir` | 视频文件目录路径 | 必需参数 |
| `-o, --output` | 输出目录 | `output` |
| `-p, --pattern` | 视频文件匹配模式 | `*.flv` |
| `--whisper-model` | Whisper 模型大小 | `small` |
| `--ollama-model` | Ollama 模型名称 | `deepseek-r1:14b` |
| `--batch-size` | 文本清洗批大小 | `5` |
| `--single` | 处理单个视频文件 | - |

### Whisper 模型选择

- `tiny`: 最快，精度最低（39M）
- `base`: 较快，精度一般（74M）
- `small`: 平衡选择（244M）✅ 推荐
- `medium`: 较慢，精度较高（769M）
- `large`: 最慢，精度最高（1550M）

## 📂 输出结构

处理完成后，会在输出目录生成以下结构：

```
output/
├── audio/                 # 转换的音频文件
│   └── *.mp3
├── transcripts/           # Whisper 转录结果
│   └── *.json
├── summaries/             # 最终总结
│   ├── *_result.json      # 完整处理结果
│   └── *_summary.txt      # 纯文本总结
└── report_*.txt           # 批处理报告
```

## 🔧 完整示例

### 示例 1：处理 B 站录播文件

```bash
# 1. 准备环境
cd /Users/zhou/Documents/Projects_DevEnv/VidSum/VidSum/mvp
source venv/bin/activate

# 2. 确保 Ollama 正在运行
# 在另一个终端：ollama serve

# 3. 处理录播目录
python main.py "/Users/zhou/Documents/Projects_DevEnv/temp/opt/bili_rec/7531557-未明子" \
    -o bili_output \
    --whisper-model small \
    --batch-size 5

# 4. 查看结果
ls -la bili_output/summaries/
```

### 示例 2：测试单个小视频

```bash
# 使用 tiny 模型快速测试
python main.py /test/videos \
    --single /test/videos/sample.flv \
    --whisper-model tiny \
    --batch-size 3
```

## 🧪 测试功能

### 运行所有测试

```bash
# 激活环境
source venv/bin/activate

# 运行所有测试
python -m pytest tests/ -v

# 运行特定模块的测试
python -m pytest tests/test_video_converter.py -v
python -m pytest tests/test_transcriber.py -v
python -m pytest tests/test_text_cleaner.py -v
python -m pytest tests/test_summarizer.py -v
```

### 测试单个模块

```bash
# 测试视频转换
cd mvp && python services/video_converter.py

# 测试 Whisper（需要先有音频文件）
cd mvp && python services/transcriber.py

# 测试文本清洗
cd mvp && python services/text_cleaner.py

# 测试总结生成
cd mvp && python services/summarizer.py
```

## ⚠️ 常见问题

### 1. FFmpeg 未安装

```
错误: ❌ FFmpeg 未安装，请先安装 FFmpeg
```

**解决方案：**
```bash
# macOS
brew install ffmpeg

# Ubuntu
sudo apt-get install ffmpeg
```

### 2. Whisper 环境未配置

```
错误: ❌ Whisper 环境未配置
```

**解决方案：**
```bash
# 确保 whisper-env 存在
ls ~/whisper-env/

# 如果不存在，创建并安装
python3 -m venv ~/whisper-env
source ~/whisper-env/bin/activate
pip install openai-whisper
```

### 3. Ollama 服务不可用

```
错误: ❌ Ollama 服务不可用或模型未安装
```

**解决方案：**
```bash
# 终端 1：启动 Ollama
ollama serve

# 终端 2：拉取模型
ollama pull deepseek-r1:14b

# 检查模型列表
ollama list
```

### 4. 内存不足

处理大视频文件时可能遇到内存问题。

**解决方案：**
- 使用更小的 Whisper 模型（tiny 或 base）
- 减小批处理大小 `--batch-size 3`
- 分批处理视频文件

### 5. 处理速度慢

**优化建议：**
- 使用 tiny 或 base Whisper 模型进行快速处理
- 调整批大小：`--batch-size 10`（根据内存调整）
- 确保使用 GPU（如果有 CUDA 支持）

## 📊 性能参考

以下是在 M1 MacBook Pro 上的测试数据：

| 视频时长 | Whisper 模型 | 处理时间 | 内存使用 |
|----------|------------|----------|----------|
| 30 分钟 | tiny | ~5 分钟 | ~2GB |
| 30 分钟 | small | ~15 分钟 | ~4GB |
| 2 小时 | tiny | ~20 分钟 | ~3GB |
| 2 小时 | small | ~60 分钟 | ~6GB |

## 🎯 最佳实践

1. **首次使用**：先用一个小视频文件测试整个流程
2. **模型选择**：
   - 快速处理：使用 `tiny` 模型
   - 质量优先：使用 `small` 或 `medium` 模型
3. **批处理**：
   - 大量文件：分批处理，避免内存溢出
   - 批大小：根据内存情况调整，通常 3-10 之间
4. **输出管理**：定期清理 `audio/` 目录下的临时音频文件

## 💡 进阶用法

### 自定义 Ollama 模型

如果想使用其他 LLM 模型：

```bash
# 拉取其他模型
ollama pull qwen2.5:14b

# 使用自定义模型
python main.py /videos --ollama-model qwen2.5:14b
```

### 并行处理优化

编辑 `services/text_cleaner.py`，调整并行参数：

```python
cleaner = TextCleaner(
    model="deepseek-r1:14b",
    batch_size=10,        # 增加批大小
    max_workers=5         # 增加并行线程
)
```

## 📝 输出示例

处理完成后，`*_summary.txt` 文件内容示例：

```
视频: 录制-7531557-20250723-225705-748-随便聊聊.flv
============================================================

【段落 1】
一、开场介绍 [00:00:15]
主播开始今天的直播，和观众打招呼...

二、今日话题 [00:05:30]
1. 游戏讨论 [00:05:45]
   讨论最近玩的新游戏体验

2. 互动环节 [00:15:20]
   回答观众提问...

【段落 2】
三、技术分享 [00:30:00]
分享了一些编程技巧和经验...
```

## 🤝 贡献与反馈

如有问题或建议，欢迎提交 Issue 或 PR。

## 📄 许可证

MIT License

---

*最后更新: 2025-01-19*