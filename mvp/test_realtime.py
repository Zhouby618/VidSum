#!/usr/bin/env python3
"""测试实时输出效果的脚本"""

import sys
from pathlib import Path

# 测试服务模块
from services.transcriber import WhisperTranscriber
from services.text_cleaner import TextCleaner
from services.summarizer import Summarizer


def test_realtime_output():
    """测试实时输出功能"""
    print("=" * 80)
    print("🎯 VidSum MVP - 实时输出测试")
    print("=" * 80)

    # 示例音频文件路径
    audio_file = Path("data/audio/test.mp3")

    if not audio_file.exists():
        print(f"❌ 测试音频文件不存在: {audio_file}")
        print("请先运行视频转音频，生成测试音频文件")
        return

    # 1. 测试 Whisper 实时转录
    print("\n📋 步骤 1: Whisper 实时转录测试")
    print("-" * 60)
    transcriber = WhisperTranscriber(
        model="tiny",  # 使用 tiny 模型快速测试
        language="zh"
    )

    if transcriber.check_whisper():
        print("✓ Whisper 环境已就绪")
        print("\n 开始实时转录测试...")

        # 开启实时输出
        result = transcriber.transcribe_audio(audio_file, show_realtime=True)

        if result:
            print(f"\n 转录完成，共 {len(result.get('segments', []))} 个片段")
        else:
            print("转录失败")
    else:
        print("❌ Whisper 环境未配置")

    # 2. 测试文本清洗实时显示
    if result:
        print("\n📋 步骤 2: 文本清洗实时显示测试")
        print("-" * 60)
        cleaner = TextCleaner(
            model="deepseek-r1:14b",
            batch_size=3  # 小批量以便观察
        )

        if cleaner.check_ollama():
            print("✓ Ollama 已就绪")
            print("\n 开始文本清洗...")

            cleaned = cleaner.clean_transcript(result, parallel=True)
            print(f"\n 清洗完成，生成 {len(cleaned.get('paragraphs', []))} 个段落")

            # 3. 测试总结生成实时显示
            print("\n📋 步骤 3: 总结生成实时显示测试")
            print("-" * 60)
            summarizer = Summarizer(model="deepseek-r1:14b")

            print("开始生成总结...")
            final_result = summarizer.summarize_transcript(cleaned)

            if 'summary_with_timestamps' in final_result:
                print(f"\n 生成完成，共 {len(final_result['summary_with_timestamps'])} 个章节")
        else:
            print("❌ Ollama 服务不可用")

    print("\n" + "=" * 80)
    print("✅ 实时输出测试完成！")
    print("=" * 80)


if __name__ == "__main__":
    test_realtime_output()