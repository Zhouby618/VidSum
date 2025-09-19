#!/usr/bin/env python3
"""视频转音频模块 - 使用 FFmpeg 处理 FLV 视频文件"""

import os
import subprocess
from pathlib import Path
from typing import Optional, List
from tqdm import tqdm
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VideoToAudioConverter:
    """视频转音频转换器"""

    def __init__(self, output_dir: str = "data/audio"):
        """
        初始化转换器

        Args:
            output_dir: 音频输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def check_ffmpeg(self) -> bool:
        """检查 FFmpeg 是否安装"""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True,
                check=False
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def convert_single_video(self, video_path: Path, output_path: Optional[Path] = None) -> Optional[Path]:
        """
        转换单个视频文件为音频

        Args:
            video_path: 视频文件路径
            output_path: 输出音频文件路径（可选）

        Returns:
            音频文件路径，失败返回 None
        """
        if not video_path.exists():
            logger.error(f"视频文件不存在: {video_path}")
            return None

        if not self.check_ffmpeg():
            logger.error("FFmpeg 未安装，请先安装 FFmpeg")
            return None

        # 生成输出文件名
        if output_path is None:
            output_filename = video_path.stem + ".mp3"
            output_path = self.output_dir / output_filename

        logger.info(f"开始转换: {video_path.name}")

        # FFmpeg 命令：提取音频，转换为 MP3 格式
        cmd = [
            "ffmpeg",
            "-i", str(video_path),          # 输入文件
            "-vn",                           # 不处理视频流
            "-acodec", "libmp3lame",         # 使用 MP3 编码器
            "-ar", "16000",                  # 采样率 16kHz（适合语音识别）
            "-ac", "1",                      # 单声道
            "-ab", "64k",                    # 比特率 64kbps
            "-y",                            # 覆盖输出文件
            str(output_path)
        ]

        try:
            # 执行转换
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            logger.info(f"转换成功: {output_path.name}")
            return output_path

        except subprocess.CalledProcessError as e:
            logger.error(f"转换失败: {video_path.name}")
            logger.error(f"错误信息: {e.stderr}")
            return None

    def convert_directory(self, directory: str, pattern: str = "*.flv") -> List[Path]:
        """
        批量转换目录中的视频文件

        Args:
            directory: 视频文件目录
            pattern: 文件匹配模式

        Returns:
            成功转换的音频文件路径列表
        """
        video_dir = Path(directory)
        if not video_dir.exists():
            logger.error(f"目录不存在: {directory}")
            return []

        # 查找所有匹配的视频文件
        video_files = list(video_dir.glob(pattern))
        if not video_files:
            logger.warning(f"未找到匹配的视频文件: {pattern}")
            return []

        logger.info(f"找到 {len(video_files)} 个视频文件")

        # 批量转换
        audio_files = []
        for video_file in tqdm(video_files, desc="转换视频"):
            audio_path = self.convert_single_video(video_file)
            if audio_path:
                audio_files.append(audio_path)

        logger.info(f"转换完成: 成功 {len(audio_files)}/{len(video_files)}")
        return audio_files

    def get_video_duration(self, video_path: Path) -> float:
        """
        获取视频时长（秒）

        Args:
            video_path: 视频文件路径

        Returns:
            视频时长（秒），失败返回 0
        """
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video_path)
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return float(result.stdout.strip())
        except (subprocess.CalledProcessError, ValueError):
            return 0.0


if __name__ == "__main__":
    # 简单测试
    converter = VideoToAudioConverter(output_dir="data/audio")

    # 检查 FFmpeg
    if converter.check_ffmpeg():
        print("✓ FFmpeg 已安装")
    else:
        print("✗ FFmpeg 未安装，请先安装 FFmpeg")
        exit(1)

    # 测试目录转换
    test_dir = "/Users/zhou/Documents/Projects_DevEnv/temp/opt/bili_rec/7531557-未明子"
    if Path(test_dir).exists():
        audio_files = converter.convert_directory(test_dir, "*.flv")
        print(f"转换完成，生成了 {len(audio_files)} 个音频文件")