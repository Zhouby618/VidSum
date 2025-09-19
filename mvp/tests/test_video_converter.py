#!/usr/bin/env python3
"""视频转音频模块测试"""

import pytest
import tempfile
import subprocess
from pathlib import Path
import sys
import os

# 添加上级目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.video_converter import VideoToAudioConverter


class TestVideoToAudioConverter:
    """视频转音频转换器测试类"""

    @pytest.fixture
    def converter(self):
        """创建转换器实例"""
        with tempfile.TemporaryDirectory() as tmpdir:
            converter = VideoToAudioConverter(output_dir=tmpdir)
            yield converter

    @pytest.fixture
    def sample_video(self):
        """创建测试用的视频文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = Path(tmpdir) / "test.flv"
            # 使用 FFmpeg 创建一个简单的测试视频（1 秒静音）
            cmd = [
                "ffmpeg",
                "-f", "lavfi",
                "-i", "anullsrc=r=16000:cl=mono:d=1",
                "-f", "lavfi",
                "-i", "color=c=black:s=320x240:d=1",
                "-c:v", "flv1",
                "-c:a", "mp3",
                "-y",
                str(video_path)
            ]
            try:
                subprocess.run(cmd, capture_output=True, check=True)
                yield video_path
            except subprocess.CalledProcessError:
                # 如果创建失败，返回 None
                yield None

    def test_check_ffmpeg(self, converter):
        """测试 FFmpeg 检查功能"""
        result = converter.check_ffmpeg()
        assert isinstance(result, bool), "check_ffmpeg 应返回布尔值"
        # 在大多数开发环境中，FFmpeg 应该是安装的
        if result:
            print("✓ FFmpeg 已安装")
        else:
            print("✗ FFmpeg 未安装")

    def test_output_dir_creation(self):
        """测试输出目录创建"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "test_audio_output"
            converter = VideoToAudioConverter(output_dir=str(output_dir))
            assert output_dir.exists(), "输出目录应该被创建"
            assert output_dir.is_dir(), "输出路径应该是目录"

    def test_convert_nonexistent_video(self, converter):
        """测试转换不存在的视频文件"""
        fake_path = Path("/fake/path/video.flv")
        result = converter.convert_single_video(fake_path)
        assert result is None, "转换不存在的文件应返回 None"

    def test_convert_single_video(self, converter, sample_video):
        """测试单个视频转换"""
        if sample_video is None or not converter.check_ffmpeg():
            pytest.skip("FFmpeg 未安装或测试视频创建失败")

        # 转换视频
        audio_path = converter.convert_single_video(sample_video)

        # 验证结果
        assert audio_path is not None, "转换应该成功"
        assert audio_path.exists(), "音频文件应该存在"
        assert audio_path.suffix == ".mp3", "音频文件应该是 MP3 格式"
        assert audio_path.stat().st_size > 0, "音频文件不应为空"

    def test_get_video_duration(self, converter, sample_video):
        """测试获取视频时长"""
        if sample_video is None or not converter.check_ffmpeg():
            pytest.skip("FFmpeg 未安装或测试视频创建失败")

        duration = converter.get_video_duration(sample_video)
        assert duration > 0, "视频时长应大于 0"
        assert 0.5 <= duration <= 2, "测试视频时长应在 1 秒左右"

    def test_convert_directory_empty(self, converter):
        """测试转换空目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            results = converter.convert_directory(tmpdir, "*.flv")
            assert results == [], "空目录应返回空列表"

    def test_convert_directory_nonexistent(self, converter):
        """测试转换不存在的目录"""
        results = converter.convert_directory("/fake/directory", "*.flv")
        assert results == [], "不存在的目录应返回空列表"

    def test_real_flv_files(self, converter):
        """测试真实的 FLV 文件（如果存在）"""
        test_dir = "/Users/zhou/Documents/Projects_DevEnv/temp/opt/bili_rec/7531557-未明子"
        if not Path(test_dir).exists():
            pytest.skip(f"测试目录不存在: {test_dir}")

        if not converter.check_ffmpeg():
            pytest.skip("FFmpeg 未安装")

        # 获取第一个 FLV 文件进行测试
        flv_files = list(Path(test_dir).glob("*.flv"))
        if not flv_files:
            pytest.skip("未找到 FLV 文件")

        # 只测试第一个文件
        first_video = flv_files[0]
        print(f"\n 测试文件: {first_video.name}")
        print(f"文件大小: {first_video.stat().st_size / (1024*1024*1024):.2f} GB")

        # 获取视频时长
        duration = converter.get_video_duration(first_video)
        if duration > 0:
            hours = int(duration // 3600)
            minutes = int((duration % 3600) // 60)
            seconds = int(duration % 60)
            print(f"视频时长: {hours:02d}:{minutes:02d}:{seconds:02d}")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])