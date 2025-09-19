# VidSum 产品需求文档 & 任务清单

## 项目愿景
打造一个本地优先的视频智能处理系统，让用户能够快速理解和导航长视频内容，将视频转化为可搜索、可交互的结构化知识。

## 用户画像
- **主要用户**：需要学习在线课程、技术教程的开发者和学生
- **次要用户**：需要整理会议录像、访谈视频的工作人员
- **痛点**：长视频难以快速浏览、无法搜索、重要内容难以定位

## 核心功能清单

### Phase 0: 项目初始化 ✅
- [x] 创建项目结构
- [x] 编写 plan.md
- [x] 编写 README.md
- [x] 配置 .gitignore
- [ ] 初始化 Git 仓库并首次提交

### Phase 1: 基础架构搭建 [预计: 2 天]

#### 1.1 环境配置
- [ ] 创建 Python 虚拟环境 (venv)
- [ ] 创建项目目录结构
  - [ ] backend/app/{api,services,utils}
  - [ ] frontend/{css,js,pages}
  - [ ] data/{videos,audio,transcripts}
  - [ ] database/
  - [ ] models/whisper/
- [ ] 创建 .gitkeep 占位文件
- [ ] 编写 requirements.txt
  ```
  fastapi==0.104.1
  uvicorn[standard]==0.24.0
  sqlalchemy==2.0.23
  alembic==1.12.1
  pydantic==2.5.2
  pydantic-settings==2.1.0
  python-dotenv==1.0.0
  aiofiles==23.2.1
  websockets==12.0
  ```
- [ ] 编写 .env.example
- [ ] 创建 setup.sh 安装脚本

#### 1.2 FastAPI 基础框架
- [ ] 创建 main.py
  - [ ] FastAPI 应用初始化
  - [ ] CORS 配置（允许前端访问）
  - [ ] 静态文件服务配置
  - [ ] 健康检查端点 `/health`
  - [ ] API 版本管理 `/api/v1`
- [ ] 创建 config.py
  - [ ] Settings 类定义
  - [ ] 环境变量加载
  - [ ] 配置验证
  - [ ] 默认值设置
- [ ] 错误处理中间件
  - [ ] 全局异常捕获
  - [ ] 统一错误响应格式
  - [ ] 日志记录

#### 1.3 数据库设计与实现
- [ ] 创建 database.py
  - [ ] SQLAlchemy 引擎配置
  - [ ] Session 管理
  - [ ] 数据库初始化函数
- [ ] 创建 models.py
  - [ ] Video 模型
    - id, url, platform, title, duration, file_path, thumbnail_path, status, created_at, updated_at
  - [ ] Transcript 模型
    - id, video_id, json_path, language, provider, status, created_at
  - [ ] Summary 模型
    - id, transcript_id, content, provider, model_name, created_at
  - [ ] Settings 模型
    - key, value, updated_at
- [ ] 创建 schemas.py (Pydantic)
  - [ ] VideoCreate, VideoResponse
  - [ ] TranscriptResponse
  - [ ] SummaryResponse
  - [ ] SettingsUpdate
- [ ] 数据库迁移
  - [ ] Alembic 初始化
  - [ ] 初始迁移脚本
  - [ ] 数据库创建脚本

### Phase 2: 视频下载功能 [预计: 2 天]

#### 2.1 下载服务实现
- [ ] 创建 services/downloader.py
  - [ ] YtDlpDownloader 类
  - [ ] 平台检测（YouTube/Bilibili）
  - [ ] 视频信息获取
    - [ ] 标题、时长、缩略图
    - [ ] 可用格式列表
  - [ ] 下载功能
    - [ ] 进度回调
    - [ ] 断点续传支持
    - [ ] 错误重试机制
  - [ ] 文件命名策略
    - [ ] 安全文件名生成
    - [ ] 避免重复

#### 2.2 下载 API
- [ ] 创建 api/video.py
  - [ ] POST `/api/v1/video/analyze` - 分析 URL
    - 输入: {url: string}
    - 输出: {title, duration, thumbnail, formats}
  - [ ] POST `/api/v1/video/download` - 开始下载
    - 输入: {url: string, format?: string}
    - 输出: {task_id, status}
  - [ ] GET `/api/v1/video/progress/{task_id}` - 获取进度
    - 输出: {progress: 0-100, status, message}
  - [ ] GET `/api/v1/video/list` - 视频列表
    - 分页支持
    - 状态筛选

#### 2.3 WebSocket 进度推送
- [ ] WebSocket 端点 `/ws/progress`
- [ ] 进度事件格式定义
  ```json
  {
    "type": "download_progress",
    "task_id": "xxx",
    "progress": 45.5,
    "speed": "1.2MB/s",
    "eta": "00:02:30"
  }
  ```
- [ ] 客户端重连机制
- [ ] 心跳检测

### Phase 3: 音频处理 [预计: 2 天]

#### 3.1 音频提取服务
- [ ] 创建 services/audio_extractor.py
  - [ ] FFmpegExtractor 类
  - [ ] 音频提取功能
    - [ ] 格式转换（统一为 wav）
    - [ ] 采样率标准化（16kHz for Whisper）
  - [ ] 临时文件管理
  - [ ] 音频时长获取

#### 3.2 语音识别服务
- [ ] 创建 services/transcriber.py
  - [ ] TranscriberBase 抽象类
  - [ ] WhisperLocalTranscriber
    - [ ] 模型加载（懒加载）
    - [ ] 模型缓存管理
    - [ ] 语言自动检测
    - [ ] 转录功能
    - [ ] 时间戳对齐
  - [ ] OpenAITranscriber（API 模式）
    - [ ] API 调用封装
    - [ ] 错误处理和重试
  - [ ] 结果格式统一
    ```json
    {
      "segments": [
        {"id": 0, "text": "...", "start": 0.0, "end": 2.5}
      ],
      "language": "zh",
      "duration": 300.5
    }
    ```

#### 3.3 转录 API
- [ ] POST `/api/v1/transcribe/{video_id}` - 开始转录
  - [ ] 参数验证
  - [ ] 任务队列提交
  - [ ] 状态更新
- [ ] GET `/api/v1/transcribe/status/{video_id}` - 获取状态
- [ ] GET `/api/v1/transcribe/result/{video_id}` - 获取结果

### Phase 4: 文本处理核心 [预计: 3 天]

#### 4.1 文本清洗服务
- [ ] 创建 services/text_cleaner.py
  - [ ] TextCleaner 类
  - [ ] 批次划分逻辑
    ```python
    def create_batches(segments, batch_size=5):
        # 根据模型能力动态调整
        pass
    ```
  - [ ] 并行清洗实现
    ```python
    async def clean_parallel(batches):
        # 使用 asyncio 并行处理所有批次
        pass
    ```
  - [ ] Prompt 模板管理
    - [ ] 清洗 Prompt
    - [ ] Few-shot 示例
  - [ ] LLM 调用封装
    - [ ] Ollama 集成
    - [ ] API 模式支持
  - [ ] 结果合并

#### 4.2 智能分段服务
- [ ] 创建 services/text_segmenter.py
  - [ ] 段落边界检测
    - [ ] 基于转折词
    - [ ] 基于标点符号
    - [ ] 基于时间间隔
    - [ ] （可选）基于语义相似度
  - [ ] 段落组合策略
    - [ ] 最小段落长度
    - [ ] 最大段落长度
    - [ ] 时间戳映射保持
  - [ ] 输出格式
    ```json
    {
      "paragraphs": [
        {
          "id": 0,
          "text": "清洗后的段落",
          "segments": [0, 1, 2],
          "start_time": 0.0,
          "end_time": 30.0
        }
      ]
    }
    ```

#### 4.3 文本处理 API
- [ ] POST `/api/v1/process/clean/{transcript_id}` - 文本清洗
- [ ] POST `/api/v1/process/segment/{transcript_id}` - 智能分段
- [ ] GET `/api/v1/process/status/{task_id}` - 处理状态

### Phase 5: LLM 总结功能 [预计: 2 天]

#### 5.1 总结服务
- [ ] 创建 services/summarizer.py
  - [ ] SummarizerBase 抽象类
  - [ ] OllamaSummarizer
    - [ ] 模型检查和下载提示
    - [ ] 流式输出支持
  - [ ] OpenAISummarizer
  - [ ] 分批策略
    ```python
    def batch_by_tokens(paragraphs, max_tokens=2000):
        # 在自然段边界分批
        pass
    ```
  - [ ] 总结 Prompt 设计
    - [ ] 保留时间戳要求
    - [ ] 格式化要求
  - [ ] 时间戳注入
    ```python
    def inject_timestamps(summary, paragraphs):
        # 在总结中添加时间戳标记
        # 格式: "一、概述 [00:00:15]"
        pass
    ```

#### 5.2 总结 API
- [ ] POST `/api/v1/summarize/{transcript_id}` - 生成总结
  - [ ] 参数: {detail_level: "brief"|"detailed"}
- [ ] GET `/api/v1/summarize/{video_id}/result` - 获取总结
- [ ] PATCH `/api/v1/summarize/{summary_id}` - 手动编辑总结

### Phase 6: 前端界面开发 [预计: 3 天]

#### 6.1 基础页面结构
- [ ] 创建 frontend/index.html
  - [ ] 响应式布局
  - [ ] 导航栏
    - [ ] Logo 和标题
    - [ ] 设置按钮
    - [ ] 历史记录按钮
  - [ ] 主要区域划分
    - [ ] URL 输入区
    - [ ] 视频播放区
    - [ ] 总结文本区

#### 6.2 视频播放器
- [ ] 集成 Video.js
  - [ ] 播放器初始化
  - [ ] 自定义控制栏
  - [ ] 快捷键支持
- [ ] 时间跳转功能
  ```javascript
  function jumpToTime(seconds) {
    player.currentTime(seconds);
    player.play();
  }
  ```
- [ ] 进度同步
  - [ ] 播放时高亮对应段落
  - [ ] 段落滚动跟随

#### 6.3 URL 输入组件
- [ ] URL 输入框
  - [ ] 格式验证
  - [ ] 平台图标显示
- [ ] 下载按钮
  - [ ] 加载状态
  - [ ] 进度显示
- [ ] 历史记录下拉
  - [ ] 最近 10 个 URL
  - [ ] 快速选择

#### 6.4 总结文本展示
- [ ] 文本渲染
  - [ ] Markdown 支持
  - [ ] 时间戳标记高亮
- [ ] 点击交互
  ```javascript
  document.addEventListener('click', (e) => {
    if (e.target.dataset.timestamp) {
      jumpToTime(parseTimestamp(e.target.dataset.timestamp));
    }
  });
  ```
- [ ] 搜索功能
  - [ ] 关键词高亮
  - [ ] 结果定位
- [ ] 段落折叠/展开

#### 6.5 设置页面
- [ ] 创建 frontend/pages/settings.html
- [ ] STT 配置界面
  - [ ] 模式切换（本地/API）
  - [ ] 模型选择
  - [ ] API 配置输入
- [ ] LLM 配置界面
  - [ ] 模式切换
  - [ ] 模型选择
  - [ ] API 配置输入
- [ ] 高级设置
  - [ ] 清洗强度
  - [ ] 批处理大小
  - [ ] 并发数
- [ ] 配置保存和验证

#### 6.6 进度反馈系统
- [ ] 进度条组件
  - [ ] 多阶段显示
    - [ ] 下载中
    - [ ] 转录中
    - [ ] 清洗中
    - [ ] 总结中
  - [ ] 时间估算
- [ ] 通知系统
  - [ ] 成功/失败提示
  - [ ] 错误详情显示
- [ ] 日志面板（可折叠）

### Phase 7: API 集成与状态管理 [预计: 2 天]

#### 7.1 前端 API 客户端
- [ ] 创建 js/api.js
  - [ ] API 基类
    ```javascript
    class APIClient {
      constructor(baseURL) {}
      async request(method, path, data) {}
    }
    ```
  - [ ] 视频相关 API
  - [ ] 转录相关 API
  - [ ] 总结相关 API
  - [ ] 设置相关 API
- [ ] 错误处理
  - [ ] 统一错误提示
  - [ ] 重试机制

#### 7.2 WebSocket 客户端
- [ ] 创建 js/websocket.js
  - [ ] 连接管理
  - [ ] 自动重连
  - [ ] 事件分发
  ```javascript
  class WSClient {
    on(event, handler) {}
    emit(event, data) {}
  }
  ```

#### 7.3 状态管理
- [ ] 创建 js/store.js
  - [ ] 全局状态
    ```javascript
    const store = {
      currentVideo: null,
      transcript: null,
      summary: null,
      settings: {},
      processing: {
        stage: null,
        progress: 0
      }
    };
    ```
  - [ ] 状态更新通知
  - [ ] 本地存储同步

### Phase 8: 端到端流程测试 [预计: 2 天]

#### 8.1 单元测试
- [ ] 下载服务测试
  - [ ] URL 解析测试
  - [ ] 文件保存测试
- [ ] 转录服务测试
  - [ ] 模型加载测试
  - [ ] 结果格式测试
- [ ] 文本处理测试
  - [ ] 清洗效果测试
  - [ ] 分段准确性测试
- [ ] 总结服务测试
  - [ ] 时间戳保持测试
  - [ ] 批处理测试

#### 8.2 集成测试
- [ ] 完整流程测试
  - [ ] YouTube 视频测试
  - [ ] B 站视频测试
  - [ ] 长视频（>1 小时）测试
  - [ ] 短视频（<5 分钟）测试
- [ ] 并发测试
  - [ ] 多任务并行处理
  - [ ] 资源占用监控
- [ ] 错误恢复测试
  - [ ] 网络中断恢复
  - [ ] 进程重启恢复

#### 8.3 性能优化
- [ ] 内存优化
  - [ ] 模型懒加载
  - [ ] 垃圾回收优化
- [ ] 速度优化
  - [ ] 批处理大小调优
  - [ ] 并发数调优
- [ ] 存储优化
  - [ ] 临时文件清理
  - [ ] 数据压缩

### Phase 9: 用户体验优化 [预计: 2 天]

#### 9.1 界面美化
- [ ] UI 框架集成（可选）
  - [ ] 评估 Tailwind CSS
  - [ ] 或自定义 CSS
- [ ] 主题设计
  - [ ] 颜色方案
  - [ ] 字体选择
  - [ ] 图标设计
- [ ] 动画效果
  - [ ] 平滑过渡
  - [ ] 加载动画
- [ ] 响应式适配
  - [ ] 移动端布局
  - [ ] 平板布局

#### 9.2 交互优化
- [ ] 快捷键系统
  - [ ] 空格: 播放/暂停
  - [ ] ←/→: 快进/快退
  - [ ] Ctrl+F: 搜索
- [ ] 拖放支持
  - [ ] 拖放 URL
  - [ ] 拖放视频文件
- [ ] 右键菜单
  - [ ] 复制时间戳
  - [ ] 导出段落

#### 9.3 辅助功能
- [ ] 首次使用引导
  - [ ] 功能介绍
  - [ ] 操作提示
- [ ] 工具提示
- [ ] 键盘导航支持
- [ ] 高对比度模式

### Phase 10: 部署与文档 [预计: 1 天]

#### 10.1 部署准备
- [ ] 生产环境配置
  - [ ] 环境变量分离
  - [ ] 日志配置
  - [ ] 性能配置
- [ ] Docker 支持（可选）
  - [ ] Dockerfile
  - [ ] docker-compose.yml
- [ ] 启动脚本
  - [ ] run.sh (Linux/Mac)
  - [ ] run.bat (Windows)

#### 10.2 文档完善
- [ ] API 文档
  - [ ] Swagger/OpenAPI 集成
  - [ ] 接口说明
  - [ ] 示例请求
- [ ] 用户手册
  - [ ] 安装指南
  - [ ] 使用教程
  - [ ] 常见问题
- [ ] 开发文档
  - [ ] 架构说明
  - [ ] 扩展指南
  - [ ] 贡献指南

#### 10.3 发布
- [ ] 版本号管理
- [ ] 更新日志
- [ ] 发布说明
- [ ] 示例视频准备

## 非功能性需求

### 性能要求
- [ ] 视频下载：支持 1080p 视频
- [ ] 转录速度：30 分钟视频 < 5 分钟处理
- [ ] 总结生成：< 30 秒
- [ ] 并发处理：支持 3 个任务并行
- [ ] 内存占用：< 4GB (含模型)

### 可用性要求
- [ ] 错误恢复：自动重试失败任务
- [ ] 数据持久化：进程重启不丢失
- [ ] 离线支持：无网络可处理本地视频

### 安全要求
- [ ] 输入验证：防止注入攻击
- [ ] 文件安全：防止路径遍历
- [ ] API 安全：速率限制
- [ ] 数据隐私：本地处理，不上传

### 兼容性要求
- [ ] Python 3.9+
- [ ] Chrome/Firefox/Safari 最新版
- [ ] Windows/macOS/Linux
- [ ] 4GB+ RAM

## 验收标准

### 核心功能验收
1. **视频下载**
   - ✓ 能成功下载 YouTube 视频
   - ✓ 能成功下载 B 站视频
   - ✓ 显示实时下载进度

2. **语音转录**
   - ✓ 准确识别中文内容
   - ✓ 准确识别英文内容
   - ✓ 保持时间戳准确性

3. **文本清洗**
   - ✓ 去除语气词
   - ✓ 添加标点符号
   - ✓ 形成自然段落
   - ✓ 不改变原意

4. **智能总结**
   - ✓ 总结包含主要观点
   - ✓ 保留时间戳标记
   - ✓ 可点击跳转

5. **交互体验**
   - ✓ 点击总结跳转视频
   - ✓ 播放时高亮文本
   - ✓ 响应速度 < 200ms

## 项目里程碑

- **M1**: 基础架构完成（Day 2）
- **M2**: 视频下载和转录功能完成（Day 6）
- **M3**: 文本处理核心完成（Day 9）
- **M4**: LLM 总结功能完成（Day 11）
- **M5**: 前端界面完成（Day 14）
- **M6**: 测试和优化完成（Day 16）
- **M7**: 1.0 版本发布（Day 17）

## 风险管理

### 技术风险
1. **Whisper 模型过大**
   - 缓解：提供 tiny/base 选项
   - 备选：使用 faster-whisper

2. **LLM 幻觉问题**
   - 缓解：小批量处理
   - 备选：增加验证步骤

3. **视频下载限制**
   - 缓解：支持本地文件
   - 备选：浏览器扩展

### 资源风险
1. **内存不足**
   - 缓解：模型懒加载
   - 备选：云端 API

2. **处理时间过长**
   - 缓解：显示详细进度
   - 备选：后台队列处理

## 后续迭代计划

### V1.1 功能增强
- [ ] 支持更多视频平台
- [ ] 支持播放列表
- [ ] 批量处理模式
- [ ] 导出功能（PDF/Markdown）

### V1.2 智能升级
- [ ] 自动章节检测
- [ ] 关键帧提取
- [ ] 多语言混合支持
- [ ] 自定义总结模板

### V2.0 重大更新
- [ ] 多人协作功能
- [ ] 云端同步
- [ ] 移动端支持
- [ ] 插件系统

---

*最后更新: 2025-01-18*
*预计完成时间: 17 个工作日*
*团队规模建议: 1-2 人*