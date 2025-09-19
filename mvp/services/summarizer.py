#!/usr/bin/env python3
"""总结生成模块 - 使用 Ollama 生成智能总结"""

import json
from typing import List, Dict, Optional
from pathlib import Path
import logging
from tqdm import tqdm
import ollama

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Summarizer:
    """基于 LLM 的视频内容总结器"""

    # 总结提示词模板
    SUMMARY_PROMPT = """你是一个专业的内容总结助手。请根据提供的视频转录文本，生成一个结构化的总结。

要求：
1. 总结应该包含主要话题和关键信息
2. 使用清晰的层级结构（一、二、三...或 1、2、3...）
3. 每个要点都要简洁明了
4. 保留重要的细节和数据
5. 必须包含时间戳标记，格式为 [HH:MM:SS]
6. 时间戳应该对应到该内容开始的位置

示例格式：
一、项目介绍 [00:00:15]
    本视频介绍了 React 框架的基础知识...

二、核心概念 [00:05:30]
    1. 组件系统 [00:05:45]
       - 函数组件的使用方法
       - 类组件的特点

    2. Hooks 机制 [00:12:20]
       - useState 的基本用法
       - useEffect 的生命周期管理

三、实战演示 [00:25:00]
    演示了如何创建一个待办事项应用...

现在请总结以下内容：

【视频时长】{duration}
【转录文本】
{text}

【开始时间】{start_time}

请生成结构化总结："""

    def __init__(self,
                 model: str = "deepseek-r1:14b",
                 ollama_host: str = "http://localhost:11434"):
        """
        初始化总结器

        Args:
            model: Ollama 模型名称
            ollama_host: Ollama 服务地址
        """
        self.model = model
        self.client = ollama.Client(host=ollama_host)

    def format_timestamp(self, seconds: float) -> str:
        """格式化时间戳"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def summarize_paragraph(self, paragraph: Dict, total_duration: float) -> Dict:
        """
        总结单个段落

        Args:
            paragraph: 段落数据
            total_duration: 视频总时长

        Returns:
            包含总结的段落数据
        """
        text = paragraph.get('text', '')
        start_time = paragraph.get('start_time', 0)
        end_time = paragraph.get('end_time', 0)

        if not text.strip():
            return {
                **paragraph,
                'summary': '（无内容）'
            }

        # 构建提示词
        prompt = self.SUMMARY_PROMPT.format(
            duration=self.format_timestamp(total_duration),
            text=text,
            start_time=self.format_timestamp(start_time)
        )

        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                options={
                    'temperature': 0.5,
                    'top_p': 0.9,
                }
            )

            summary = response['message']['content'].strip()
            return {
                **paragraph,
                'summary': summary
            }

        except Exception as e:
            logger.error(f"生成总结失败: {e}")
            return {
                **paragraph,
                'summary': f"[总结生成失败] {text[:100]}..."
            }

    def summarize_transcript(self, transcript: Dict) -> Dict:
        """
        生成完整的视频总结

        Args:
            transcript: 包含清洗后文本的转录结果

        Returns:
            包含总结的完整结果
        """
        if not transcript or 'paragraphs' not in transcript:
            logger.warning("转录结果不包含段落信息")
            return transcript

        paragraphs = transcript.get('paragraphs', [])
        duration = transcript.get('duration', 0)

        if not paragraphs:
            return transcript

        logger.info(f"开始生成总结，共 {len(paragraphs)} 个段落")

        # 逐段生成总结
        summarized_paragraphs = []
        for para in tqdm(paragraphs, desc="生成总结"):
            summarized = self.summarize_paragraph(para, duration)
            summarized_paragraphs.append(summarized)

        # 合并所有段落的总结
        full_summary_parts = []
        summary_with_timestamps = []

        for i, para in enumerate(summarized_paragraphs):
            summary_text = para.get('summary', '')
            if summary_text and summary_text != '（无内容）':
                full_summary_parts.append(f"【段落 {i+1}】\n{summary_text}")

                # 解析总结中的时间戳结构
                self._extract_timestamped_sections(
                    summary_text,
                    para.get('start_time', 0),
                    summary_with_timestamps
                )

        # 更新转录结果
        result = transcript.copy()
        result['paragraphs'] = summarized_paragraphs
        result['full_summary'] = "\n\n".join(full_summary_parts)
        result['summary_with_timestamps'] = summary_with_timestamps

        logger.info(f"总结生成完成，共 {len(summary_with_timestamps)} 个章节")
        return result

    def _extract_timestamped_sections(self, summary_text: str, base_time: float, sections_list: List):
        """
        从总结文本中提取带时间戳的章节

        Args:
            summary_text: 总结文本
            base_time: 基础时间偏移
            sections_list: 章节列表（输出）
        """
        import re

        # 匹配格式：一、标题 [00:00:00] 或 1. 标题 [00:00:00]
        pattern = r'([一二三四五六七八九十\d]+[、.]\s*[^[]+)\s*\[(\d{2}:\d{2}:\d{2})\]'
        matches = re.findall(pattern, summary_text)

        for title, timestamp in matches:
            # 解析时间戳为秒
            parts = timestamp.split(':')
            if len(parts) == 3:
                seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])

                # 提取该章节的内容（到下一个章节或结束）
                start_idx = summary_text.find(f"{title} [{timestamp}]")
                if start_idx != -1:
                    # 查找下一个章节的位置
                    next_match = re.search(pattern, summary_text[start_idx + len(title) + 10:])
                    if next_match:
                        end_idx = start_idx + len(title) + 10 + next_match.start()
                        content = summary_text[start_idx + len(title) + 10:end_idx].strip()
                    else:
                        content = summary_text[start_idx + len(title) + 10:].strip()

                    sections_list.append({
                        'title': title.strip(),
                        'timestamp': timestamp,
                        'start_seconds': seconds,
                        'content': content[:200] + '...' if len(content) > 200 else content
                    })

    def generate_simple_summary(self, text: str) -> str:
        """
        生成简单的文本总结（不含时间戳）

        Args:
            text: 输入文本

        Returns:
            总结文本
        """
        if not text.strip():
            return ""

        prompt = f"""请简洁地总结以下内容的要点：

{text}

要求：
1. 提取 3-5 个关键要点
2. 每个要点一行
3. 简洁明了，不超过 50 字

总结："""

        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                options={
                    'temperature': 0.3,
                    'top_p': 0.9,
                }
            )

            return response['message']['content'].strip()

        except Exception as e:
            logger.error(f"生成简单总结失败: {e}")
            return text[:200] + "..."


if __name__ == "__main__":
    # 简单测试
    summarizer = Summarizer(model="deepseek-r1:14b")

    # 测试简单总结
    test_text = """
    今天我们要讲解 Python 编程的基础知识。首先介绍变量和数据类型，
    包括整数、浮点数、字符串等。然后会讲解控制流程，比如 if 语句和循环。
    最后会通过几个实例来演示这些概念的实际应用。
    """

    print("测试文本:")
    print(test_text)
    print("\n 生成的总结:")
    summary = summarizer.generate_simple_summary(test_text)
    print(summary)