#!/usr/bin/env python3
"""VidSum MVP - 视频转录和总结主程序"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
import logging
from typing import List, Dict, Optional

# 添加服务模块
from services.video_converter import VideoToAudioConverter
from services.transcriber import WhisperTranscriber
from services.text_cleaner import TextCleaner
from services.summarizer import Summarizer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime) s - %(name) s - %(levelname) s - %(message) s'
)
logger = logging.getLogger(__name__)


class VidSumPipeline:
    """VidSum 处理流水线"""

    def __init__(self,
                 video_dir: str,
                 output_dir: str = "output",
                 whisper_model: str = "small",
                 ollama_model: str = "deepseek-r1:14b",
                 batch_size: int = 5):
        """
        初始化流水线

        Args:
            video_dir: 视频文件目录
            output_dir: 输出目录
            whisper_model: Whisper 模型大小
            ollama_model: Ollama 模型名称
            batch_size: 文本清洗批大小
        """
        self.video_dir = Path(video_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 创建子目录
        self.audio_dir = self.output_dir / "audio"
        self.transcript_dir = self.output_dir / "transcripts"
        self.summary_dir = self.output_dir / "summaries"

        # 初始化各个服务
        self.video_converter = VideoToAudioConverter(output_dir=str(self.audio_dir))
        self.transcriber = WhisperTranscriber(
            model=whisper_model,
            output_dir=str(self.transcript_dir)
        )
        self.text_cleaner = TextCleaner(
            model=ollama_model,
            batch_size=batch_size
        )
        self.summarizer = Summarizer(model=ollama_model)

    def check_dependencies(self) -> bool:
        """检查所有依赖是否就绪"""
        logger.info("检查系统依赖...")

        # 检查 FFmpeg
        if not self.video_converter.check_ffmpeg():
            logger.error("❌ FFmpeg 未安装，请先安装 FFmpeg")
            return False
        logger.info("✓ FFmpeg 已就绪")

        # 检查 Whisper
        if not self.transcriber.check_whisper():
            logger.error("❌ Whisper 环境未配置")
            logger.info("请运行: source ~/whisper-env/bin/activate")
            return False
        logger.info("✓ Whisper 已就绪")

        # 检查 Ollama
        if not self.text_cleaner.check_ollama():
            logger.error("❌ Ollama 服务不可用或模型未安装")
            logger.info("请确保 Ollama 正在运行并安装了 deepseek-r1:14b 模型")
            return False
        logger.info("✓ Ollama 已就绪")

        return True

    def process_single_video(self, video_path: Path) -> Optional[Dict]:
        """
        处理单个视频文件

        Args:
            video_path: 视频文件路径

        Returns:
            处理结果字典
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"开始处理: {video_path.name}")
        logger.info(f"文件大小: {video_path.stat().st_size / (1024*1024*1024):.2f} GB")

        result = {
            'video_file': video_path.name,
            'video_path': str(video_path),
            'start_time': datetime.now().isoformat(),
            'status': 'processing'
        }

        try:
            # 步骤 1: 视频转音频
            logger.info("\n[1/4] 转换视频到音频...")
            audio_path = self.video_converter.convert_single_video(video_path)
            if not audio_path:
                raise Exception("视频转音频失败")
            result['audio_file'] = audio_path.name

            # 步骤 2: 语音转录
            logger.info("\n[2/4] 进行语音转录...")
            transcript = self.transcriber.transcribe_audio(audio_path)
            if not transcript:
                raise Exception("语音转录失败")
            result['transcript'] = transcript

            # 步骤 3: 文本清洗
            logger.info("\n[3/4] 清洗转录文本...")
            cleaned_transcript = self.text_cleaner.clean_transcript(transcript, parallel=True)
            result['cleaned_transcript'] = cleaned_transcript

            # 步骤 4: 生成总结
            logger.info("\n[4/4] 生成内容总结...")
            final_result = self.summarizer.summarize_transcript(cleaned_transcript)
            result['final_result'] = final_result

            # 保存结果
            self._save_result(result, video_path)

            result['status'] = 'success'
            result['end_time'] = datetime.now().isoformat()

            logger.info(f"\n✅ 处理完成: {video_path.name}")

        except Exception as e:
            logger.error(f"处理失败: {e}")
            result['status'] = 'failed'
            result['error'] = str(e)
            result['end_time'] = datetime.now().isoformat()

        return result

    def _save_result(self, result: Dict, video_path: Path):
        """保存处理结果到 JSON 文件"""
        output_file = self.summary_dir / f"{video_path.stem}_result.json"
        self.summary_dir.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        logger.info(f"结果已保存: {output_file}")

        # 同时保存一个纯文本版本的总结
        if 'final_result' in result and 'full_summary' in result['final_result']:
            summary_text_file = self.summary_dir / f"{video_path.stem}_summary.txt"
            with open(summary_text_file, 'w', encoding='utf-8') as f:
                f.write(f"视频: {video_path.name}\n")
                f.write(f"{'='*60}\n\n")
                f.write(result['final_result']['full_summary'])

            logger.info(f"总结文本已保存: {summary_text_file}")

    def process_batch(self, pattern: str = "*.flv") -> List[Dict]:
        """
        批量处理视频文件

        Args:
            pattern: 文件匹配模式

        Returns:
            处理结果列表
        """
        if not self.video_dir.exists():
            logger.error(f"视频目录不存在: {self.video_dir}")
            return []

        # 查找匹配的视频文件
        video_files = list(self.video_dir.glob(pattern))
        if not video_files:
            logger.warning(f"未找到匹配的视频文件: {pattern}")
            return []

        logger.info(f"找到 {len(video_files)} 个视频文件")

        # 检查依赖
        if not self.check_dependencies():
            logger.error("依赖检查失败，请先解决上述问题")
            return []

        # 处理每个视频
        results = []
        for i, video_file in enumerate(video_files, 1):
            logger.info(f"\n 处理进度: {i}/{len(video_files)}")
            result = self.process_single_video(video_file)
            results.append(result)

        # 生成汇总报告
        self._generate_report(results)

        return results

    def _generate_report(self, results: List[Dict]):
        """生成处理报告"""
        report_file = self.output_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        success_count = sum(1 for r in results if r.get('status') == 'success')
        failed_count = sum(1 for r in results if r.get('status') == 'failed')

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("VidSum 处理报告\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*60}\n\n")

            f.write(f"处理总数: {len(results)}\n")
            f.write(f"成功: {success_count}\n")
            f.write(f"失败: {failed_count}\n\n")

            f.write("详细结果:\n")
            f.write("-" * 60 + "\n")

            for result in results:
                f.write(f"\n 文件: {result.get('video_file', 'Unknown')}\n")
                f.write(f"状态: {result.get('status', 'Unknown')}\n")

                if result.get('status') == 'failed':
                    f.write(f"错误: {result.get('error', 'Unknown error')}\n")
                elif result.get('status') == 'success':
                    if 'final_result' in result and 'summary_with_timestamps' in result['final_result']:
                        sections = result['final_result']['summary_with_timestamps']
                        f.write(f"章节数: {len(sections)}\n")
                        f.write("主要章节:\n")
                        for section in sections[:5]:  # 只显示前 5 个章节
                            f.write(f"  - {section.get('title', '')} [{section.get('timestamp', '')}]\n")

        logger.info(f"\n📊 处理报告已生成: {report_file}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="VidSum MVP - 视频转录和总结工具")
    parser.add_argument(
        "video_dir",
        help="视频文件目录路径"
    )
    parser.add_argument(
        "-o", "--output",
        default="output",
        help="输出目录 (默认: output)"
    )
    parser.add_argument(
        "-p", "--pattern",
        default="*.flv",
        help="视频文件匹配模式 (默认: *.flv)"
    )
    parser.add_argument(
        "--whisper-model",
        default="small",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper 模型大小 (默认: small)"
    )
    parser.add_argument(
        "--ollama-model",
        default="deepseek-r1:14b",
        help="Ollama 模型名称 (默认: deepseek-r1:14b)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="文本清洗批大小 (默认: 5)"
    )
    parser.add_argument(
        "--single",
        help="只处理单个视频文件（提供完整路径）"
    )

    args = parser.parse_args()

    # 创建流水线
    pipeline = VidSumPipeline(
        video_dir=args.video_dir,
        output_dir=args.output,
        whisper_model=args.whisper_model,
        ollama_model=args.ollama_model,
        batch_size=args.batch_size
    )

    # 处理视频
    if args.single:
        # 处理单个视频
        video_path = Path(args.single)
        if not video_path.exists():
            logger.error(f"视频文件不存在: {args.single}")
            sys.exit(1)

        if not pipeline.check_dependencies():
            sys.exit(1)

        result = pipeline.process_single_video(video_path)
        if result['status'] == 'success':
            logger.info("\n🎉 处理成功完成!")
        else:
            logger.error("\n❌ 处理失败")
            sys.exit(1)
    else:
        # 批量处理
        results = pipeline.process_batch(args.pattern)

        # 显示最终统计
        success_count = sum(1 for r in results if r.get('status') == 'success')
        failed_count = sum(1 for r in results if r.get('status') == 'failed')

        logger.info("\n" + "="*60)
        logger.info(f"🎉 批量处理完成!")
        logger.info(f"✅ 成功: {success_count}")
        logger.info(f"❌ 失败: {failed_count}")


if __name__ == "__main__":
    main()