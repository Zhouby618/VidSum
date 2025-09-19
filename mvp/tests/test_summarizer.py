#!/usr/bin/env python3
"""总结生成模块测试"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

# 添加上级目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.summarizer import Summarizer


class TestSummarizer:
    """总结器测试类"""

    @pytest.fixture
    def summarizer(self):
        """创建总结器实例"""
        return Summarizer(model="deepseek-r1:14b")

    def test_format_timestamp(self, summarizer):
        """测试时间戳格式化"""
        assert summarizer.format_timestamp(0) == "00:00:00"
        assert summarizer.format_timestamp(65) == "00:01:05"
        assert summarizer.format_timestamp(3665) == "01:01:05"

    @patch('services.summarizer.ollama.Client')
    def test_generate_simple_summary(self, mock_client, summarizer):
        """测试简单总结生成"""
        mock_instance = mock_client.return_value
        mock_instance.chat.return_value = {
            'message': {
                'content': '• Python 基础知识\n• 变量和数据类型\n• 控制流程'
            }
        }

        text = "测试文本内容"
        result = summarizer.generate_simple_summary(text)

        assert '• Python 基础知识' in result

    @patch('services.summarizer.ollama.Client')
    def test_summarize_paragraph(self, mock_client, summarizer):
        """测试段落总结"""
        mock_instance = mock_client.return_value
        mock_instance.chat.return_value = {
            'message': {
                'content': '一、主要内容 [00:00:15]\n 这是一个测试总结。'
            }
        }

        paragraph = {
            'text': '测试段落内容',
            'start_time': 15,
            'end_time': 30
        }

        result = summarizer.summarize_paragraph(paragraph, 300)

        assert 'summary' in result
        assert '主要内容' in result['summary']

    def test_extract_timestamped_sections(self, summarizer):
        """测试时间戳章节提取"""
        summary_text = """
一、项目介绍 [00:00:15]
这是项目的基本介绍内容。

二、技术架构 [00:05:30]
1. 前端框架 [00:05:45]
   使用 React 开发

2. 后端服务 [00:10:20]
   使用 FastAPI
"""
        sections = []
        summarizer._extract_timestamped_sections(summary_text, 0, sections)

        assert len(sections) >= 2
        assert sections[0]['title'] == '一、项目介绍'
        assert sections[0]['timestamp'] == '00:00:15'
        assert sections[0]['start_seconds'] == 15


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])