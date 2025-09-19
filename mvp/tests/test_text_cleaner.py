#!/usr/bin/env python3
"""文本清洗模块测试"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# 添加上级目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.text_cleaner import TextCleaner


class TestTextCleaner:
    """文本清洗器测试类"""

    @pytest.fixture
    def cleaner(self):
        """创建清洗器实例"""
        cleaner = TextCleaner(
            model="deepseek-r1:14b",
            batch_size=3,
            max_workers=2
        )
        return cleaner

    @patch('services.text_cleaner.ollama.Client')
    def test_initialization(self, mock_client):
        """测试初始化"""
        cleaner = TextCleaner(
            model="test-model",
            batch_size=10,
            max_workers=5
        )

        assert cleaner.model == "test-model"
        assert cleaner.batch_size == 10
        assert cleaner.max_workers == 5

    @patch('services.text_cleaner.ollama.Client')
    def test_check_ollama_success(self, mock_client):
        """测试 Ollama 检查成功"""
        mock_instance = mock_client.return_value
        mock_instance.list.return_value = {
            'models': [
                {'name': 'deepseek-r1:14b'},
                {'name': 'qwen:7b'}
            ]
        }

        cleaner = TextCleaner(model="deepseek-r1:14b")
        result = cleaner.check_ollama()

        assert result is True

    @patch('services.text_cleaner.ollama.Client')
    def test_check_ollama_model_not_found(self, mock_client):
        """测试模型未找到"""
        mock_instance = mock_client.return_value
        mock_instance.list.return_value = {
            'models': [
                {'name': 'other-model'}
            ]
        }

        cleaner = TextCleaner(model="deepseek-r1:14b")
        result = cleaner.check_ollama()

        assert result is False

    @patch('services.text_cleaner.ollama.Client')
    def test_clean_single_batch(self, mock_client):
        """测试清洗单批文本"""
        mock_instance = mock_client.return_value
        mock_instance.chat.return_value = {
            'message': {
                'content': '这是清洗后的文本。'
            }
        }

        cleaner = TextCleaner()
        segments = [
            {'text': '嗯这个'},
            {'text': '就是说'},
            {'text': '测试文本'}
        ]

        result = cleaner.clean_single_batch(segments)
        assert result == '这是清洗后的文本。'

    @patch('services.text_cleaner.ollama.Client')
    def test_clean_single_batch_empty(self, mock_client):
        """测试清洗空批次"""
        cleaner = TextCleaner()
        result = cleaner.clean_single_batch([])
        assert result == ""

    @patch('services.text_cleaner.ollama.Client')
    def test_clean_single_batch_error(self, mock_client):
        """测试清洗失败时的回退"""
        mock_instance = mock_client.return_value
        mock_instance.chat.side_effect = Exception("API Error")

        cleaner = TextCleaner()
        segments = [{'text': '原始文本'}]

        result = cleaner.clean_single_batch(segments)
        assert result == "原始文本"

    @patch('services.text_cleaner.ollama.Client')
    def test_clean_transcript(self, mock_client):
        """测试清洗整个转录结果"""
        mock_instance = mock_client.return_value
        mock_instance.chat.return_value = {
            'message': {
                'content': '清洗后的段落。'
            }
        }

        cleaner = TextCleaner(batch_size=2)
        transcript = {
            'segments': [
                {'id': 0, 'text': '第一段', 'start': 0, 'end': 1},
                {'id': 1, 'text': '第二段', 'start': 1, 'end': 2},
                {'id': 2, 'text': '第三段', 'start': 2, 'end': 3},
            ]
        }

        result = cleaner.clean_transcript(transcript, parallel=False)

        assert 'paragraphs' in result
        assert 'cleaned_text' in result
        assert len(result['paragraphs']) == 2  # 3 个 segments 分成 2 批
        assert result['paragraphs'][0]['source_segments'] == [0, 1]
        assert result['paragraphs'][1]['source_segments'] == [2]

    @patch('services.text_cleaner.ollama.Client')
    def test_clean_text_simple(self, mock_client):
        """测试简单文本清洗"""
        mock_instance = mock_client.return_value
        mock_instance.chat.return_value = {
            'message': {
                'content': '这是清洗后的简单文本。'
            }
        }

        cleaner = TextCleaner()
        result = cleaner.clean_text_simple("嗯就是说这个测试")

        assert result == '这是清洗后的简单文本。'

    def test_clean_transcript_empty(self, cleaner):
        """测试清洗空转录结果"""
        result = cleaner.clean_transcript({})
        assert result == {}

        result = cleaner.clean_transcript({'segments': []})
        assert result == {'segments': []}

    def test_prompt_template(self):
        """测试提示词模板"""
        prompt = TextCleaner.CLEANING_PROMPT
        assert "文本格式整理助手" in prompt
        assert "语气词" in prompt
        assert "标点符号" in prompt


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])