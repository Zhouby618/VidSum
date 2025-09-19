#!/usr/bin/env python3
"""Whisper 转录模块 - 使用本地 Whisper 模型进行语音识别"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WhisperTranscriber:
    """Whisper 语音转录器"""

    def __init__(self,
                 whisper_env: str = "~/whisper-env/bin/activate",
                 model: str = "small",
                 language: str = "zh",
                 output_dir: str = "data/transcripts"):
        """
        初始化转录器

        Args:
            whisper_env: Whisper 环境的激活脚本路径
            model: Whisper 模型大小 (tiny, base, small, medium, large)
            language: 语言代码
            output_dir: 转录结果输出目录
        """
        self.whisper_env = Path(whisper_env).expanduser()
        self.model = model
        self.language = language
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def check_whisper(self) -> bool:
        """检查 Whisper 是否可用"""
        try:
            # 构建激活环境并检查 whisper 的命令
            cmd = f"source {self.whisper_env} && which whisper"
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                executable="/bin/bash"
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"检查 Whisper 失败: {e}")
            return False

    def transcribe_audio(self, audio_path: Path, output_format: str = "json") -> Optional[Dict]:
        """
        转录音频文件

        Args:
            audio_path: 音频文件路径
            output_format: 输出格式 (json, txt, vtt, srt, tsv)

        Returns:
            转录结果字典，失败返回 None
        """
        if not audio_path.exists():
            logger.error(f"音频文件不存在: {audio_path}")
            return None

        if not self.check_whisper():
            logger.error("Whisper 不可用，请检查环境配置")
            return None

        logger.info(f"开始转录: {audio_path.name}")
        logger.info(f"使用模型: {self.model}, 语言: {self.language}")

        # 生成输出文件名（不带扩展名）
        output_base = self.output_dir / audio_path.stem

        # 构建 Whisper 命令
        cmd = f"""
        source {self.whisper_env} && \
        whisper "{audio_path}" \
            --model {self.model} \
            --language {self.language} \
            --output_format {output_format} \
            --output_dir "{self.output_dir}" \
            --verbose False \
            --task transcribe
        """

        try:
            # 执行转录
            logger.info("正在转录中，请耐心等待...")
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                executable="/bin/bash",
                check=True
            )

            # 读取 JSON 结果
            json_file = Path(f"{output_base}.{output_format}")
            if json_file.exists():
                with open(json_file, 'r', encoding='utf-8') as f:
                    transcript_data = json.load(f)

                logger.info(f"转录成功: {json_file.name}")

                # 解析并返回结构化数据
                return self._parse_whisper_output(transcript_data, audio_path)
            else:
                logger.error(f"未找到转录结果文件: {json_file}")
                return None

        except subprocess.CalledProcessError as e:
            logger.error(f"转录失败: {audio_path.name}")
            logger.error(f"错误信息: {e.stderr}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"解析 JSON 失败: {e}")
            return None

    def _parse_whisper_output(self, whisper_data: Dict, audio_path: Path) -> Dict:
        """
        解析 Whisper 输出为统一格式

        Args:
            whisper_data: Whisper 原始输出
            audio_path: 音频文件路径

        Returns:
            格式化的转录结果
        """
        segments = []

        # 提取每个片段
        for seg in whisper_data.get('segments', []):
            segment = {
                'id': seg.get('id', 0),
                'start': seg.get('start', 0.0),
                'end': seg.get('end', 0.0),
                'text': seg.get('text', '').strip(),
                'words': seg.get('words', [])  # 如果有词级别时间戳
            }
            segments.append(segment)

        # 构建完整的转录结果
        result = {
            'audio_file': audio_path.name,
            'language': whisper_data.get('language', self.language),
            'duration': whisper_data.get('duration', 0),
            'text': whisper_data.get('text', ''),
            'segments': segments,
            'model': self.model
        }

        return result

    def transcribe_batch(self, audio_files: List[Path]) -> List[Dict]:
        """
        批量转录音频文件

        Args:
            audio_files: 音频文件路径列表

        Returns:
            转录结果列表
        """
        results = []

        for audio_file in tqdm(audio_files, desc="转录音频"):
            result = self.transcribe_audio(audio_file)
            if result:
                results.append(result)
                # 保存单个结果
                self._save_transcript(result, audio_file)

        logger.info(f"批量转录完成: 成功 {len(results)}/{len(audio_files)}")
        return results

    def _save_transcript(self, transcript: Dict, audio_path: Path):
        """
        保存转录结果到 JSON 文件

        Args:
            transcript: 转录结果
            audio_path: 音频文件路径
        """
        output_file = self.output_dir / f"{audio_path.stem}_transcript.json"

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(transcript, f, ensure_ascii=False, indent=2)
            logger.info(f"转录结果已保存: {output_file.name}")
        except Exception as e:
            logger.error(f"保存转录结果失败: {e}")

    def format_transcript_text(self, transcript: Dict, include_timestamps: bool = False) -> str:
        """
        格式化转录文本为可读格式

        Args:
            transcript: 转录结果
            include_timestamps: 是否包含时间戳

        Returns:
            格式化的文本
        """
        if not transcript or 'segments' not in transcript:
            return ""

        lines = []
        for seg in transcript['segments']:
            if include_timestamps:
                start = self._format_timestamp(seg['start'])
                end = self._format_timestamp(seg['end'])
                line = f"[{start} --> {end}] {seg['text']}"
            else:
                line = seg['text']
            lines.append(line)

        return "\n".join(lines)

    def _format_timestamp(self, seconds: float) -> str:
        """
        格式化时间戳为 HH:MM:SS 格式

        Args:
            seconds: 秒数

        Returns:
            格式化的时间戳
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"


if __name__ == "__main__":
    # 简单测试
    transcriber = WhisperTranscriber(
        whisper_env="~/whisper-env/bin/activate",
        model="small",
        language="zh"
    )

    # 检查 Whisper
    if transcriber.check_whisper():
        print("✓ Whisper 环境已配置")
    else:
        print("✗ Whisper 环境未配置，请检查路径")
        exit(1)

    # 测试转录单个文件
    test_audio = Path("data/audio/test.mp3")
    if test_audio.exists():
        result = transcriber.transcribe_audio(test_audio)
        if result:
            print(f"转录成功，共 {len(result['segments'])} 个片段")
            # 打印格式化文本
            formatted = transcriber.format_transcript_text(result, include_timestamps=True)
            print(formatted[:500])  # 只打印前 500 字符