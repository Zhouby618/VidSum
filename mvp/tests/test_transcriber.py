#!/usr/bin/env python3
"""Whisper 转录模块测试"""

import pytest
import json
import tempfile
from pathlib import Path
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# 添加上级目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.transcriber import WhisperTranscriber


class TestWhisperTranscriber:
    """Whisper 转录器测试类"""

    @pytest.fixture
    def transcriber(self):
        """创建转录器实例"""
        with tempfile.TemporaryDirectory() as tmpdir:
            transcriber = WhisperTranscriber(
                whisper_env="~/whisper-env/bin/activate",
                model="tiny",  # 使用最小的模型进行测试
                language="zh",
                output_dir=tmpdir
            )
            yield transcriber

    def test_initialization(self):
        """测试初始化"""
        with tempfile.TemporaryDirectory() as tmpdir:
            transcriber = WhisperTranscriber(
                whisper_env="~/test-env/bin/activate",
                model="base",
                language="en",
                output_dir=tmpdir
            )

            assert transcriber.model == "base"
            assert transcriber.language == "en"
            assert Path(tmpdir).exists()

    def test_check_whisper(self, transcriber):
        """测试 Whisper 环境检查"""
        result = transcriber.check_whisper()
        assert isinstance(result, bool), "check_whisper 应返回布尔值"

        if result:
            print("✓ Whisper 环境已配置")
        else:
            print("✗ Whisper 环境未配置")

    def test_format_timestamp(self, transcriber):
        """测试时间戳格式化"""
        # 测试各种时间值
        assert transcriber._format_timestamp(0) == "00:00:00"
        assert transcriber._format_timestamp(65) == "00:01:05"
        assert transcriber._format_timestamp(3665) == "01:01:05"
        assert transcriber._format_timestamp(7265.5) == "02:01:05"

    def test_parse_whisper_output(self, transcriber):
        """测试 Whisper 输出解析"""
        # 模拟 Whisper 的 JSON 输出
        mock_whisper_data = {
            "text": "这是测试文本",
            "segments": [
                {
                    "id": 0,
                    "start": 0.0,
                    "end": 2.5,
                    "text": " 这是第一段"
                },
                {
                    "id": 1,
                    "start": 2.5,
                    "end": 5.0,
                    "text": " 这是第二段"
                }
            ],
            "language": "zh",
            "duration": 5.0
        }

        audio_path = Path("/test/audio.mp3")
        result = transcriber._parse_whisper_output(mock_whisper_data, audio_path)

        assert result is not None
        assert result['audio_file'] == "audio.mp3"
        assert result['language'] == "zh"
        assert result['duration'] == 5.0
        assert len(result['segments']) == 2
        assert result['segments'][0]['text'] == "这是第一段"
        assert result['model'] == transcriber.model

    def test_format_transcript_text(self, transcriber):
        """测试转录文本格式化"""
        # 创建测试数据
        transcript = {
            "segments": [
                {
                    "start": 0.0,
                    "end": 2.5,
                    "text": "第一段文本"
                },
                {
                    "start": 2.5,
                    "end": 5.0,
                    "text": "第二段文本"
                }
            ]
        }

        # 测试不带时间戳
        text_only = transcriber.format_transcript_text(transcript, include_timestamps=False)
        assert text_only == "第一段文本\n 第二段文本"

        # 测试带时间戳
        with_timestamps = transcriber.format_transcript_text(transcript, include_timestamps=True)
        assert "[00:00:00 --> 00:00:02]" in with_timestamps
        assert "第一段文本" in with_timestamps

    def test_save_transcript(self, transcriber):
        """测试保存转录结果"""
        transcript = {
            "audio_file": "test.mp3",
            "text": "测试文本",
            "segments": []
        }

        audio_path = Path("test.mp3")
        transcriber._save_transcript(transcript, audio_path)

        # 检查文件是否创建
        expected_file = transcriber.output_dir / "test_transcript.json"
        assert expected_file.exists()

        # 验证文件内容
        with open(expected_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
            assert saved_data['audio_file'] == "test.mp3"
            assert saved_data['text'] == "测试文本"

    @patch('subprocess.run')
    def test_transcribe_audio_mock(self, mock_run, transcriber):
        """测试转录音频（模拟）"""
        # 创建临时音频文件
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_audio:
            audio_path = Path(tmp_audio.name)

        try:
            # 模拟 subprocess 成功返回
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            # 创建模拟的 JSON 输出文件
            json_output = transcriber.output_dir / f"{audio_path.stem}.json"
            mock_data = {
                "text": "模拟转录文本",
                "segments": [{"id": 0, "start": 0, "end": 1, "text": "测试"}],
                "language": "zh",
                "duration": 1.0
            }
            with open(json_output, 'w') as f:
                json.dump(mock_data, f)

            # 执行转录
            result = transcriber.transcribe_audio(audio_path)

            # 验证结果
            assert result is not None
            assert result['text'] == "模拟转录文本"
            assert len(result['segments']) == 1

        finally:
            # 清理临时文件
            if audio_path.exists():
                audio_path.unlink()

    def test_transcribe_nonexistent_audio(self, transcriber):
        """测试转录不存在的音频文件"""
        fake_path = Path("/fake/audio.mp3")
        result = transcriber.transcribe_audio(fake_path)
        assert result is None

    def test_batch_transcribe_empty_list(self, transcriber):
        """测试批量转录空列表"""
        results = transcriber.transcribe_batch([])
        assert results == []


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])