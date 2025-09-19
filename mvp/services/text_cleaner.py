#!/usr/bin/env python3
"""文本清洗模块 - 使用 Ollama 进行智能文本清洗"""

import json
from typing import List, Dict, Optional
from pathlib import Path
import logging
from tqdm import tqdm
import ollama
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TextCleaner:
    """基于 LLM 的文本清洗器"""

    # 清洗提示词模板
    CLEANING_PROMPT = """你是一个文本格式整理助手。你的任务是将口语化的语音转录文本整理成易读的书面格式。

重要规则：
1. 只能调整格式，不能改变内容含义
2. 可以去除语气词（嗯、啊、呃、这个、那个、就是说、然后）
3. 可以添加标点符号让句子更通顺
4. 可以调整换行让段落更清晰
5. 保留所有实质性内容
6. 修正明显的语音识别错误（如同音字错误）

示例：
【原始文本】
嗯今天我们来讲一下这个 React 的 hooks 啊大家知道就是说这个 hooks 呢它其实是一个非常强大的功能

【整理后】
今天我们来讲一下 React 的 hooks。大家知道，hooks 是一个非常强大的功能。

【原始文本】
那个我觉得吧这个事情呢其实也没有那么复杂就是说你只要理解了它的原理啊然后多练习练习就可以了

【整理后】
我觉得这个事情其实也没有那么复杂，只要理解了它的原理，然后多练习就可以了。

现在请整理下面的文本：
【原始文本】
{text}

请直接输出整理后的文本，不要包含任何额外说明："""

    def __init__(self,
                 model: str = "deepseek-r1:14b",
                 batch_size: int = 5,
                 max_workers: int = 3,
                 ollama_host: str = "http://localhost:11434"):
        """
        初始化文本清洗器

        Args:
            model: Ollama 模型名称
            batch_size: 每批处理的 segments 数量
            max_workers: 并行处理的最大线程数
            ollama_host: Ollama 服务地址
        """
        self.model = model
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.client = ollama.Client(host=ollama_host)

    def check_ollama(self) -> bool:
        """检查 Ollama 服务是否可用"""
        try:
            # 直接使用 ollama 包的 list 函数
            import ollama
            response = ollama.list()

            model_names = []
            # 新版本 API 返回对象属性格式
            if hasattr(response, 'models'):
                for m in response.models:
                    if hasattr(m, 'model'):
                        model_names.append(m.model)
                    elif hasattr(m, 'name'):
                        model_names.append(m.name)
            # 旧版本 API 返回字典格式
            elif isinstance(response, dict) and 'models' in response:
                for m in response['models']:
                    model_names.append(m.get('name', m.get('model', '')))

            if self.model in model_names:
                logger.info(f"✓ Ollama 模型 {self.model} 已就绪")
                return True
            else:
                logger.warning(f"模型 {self.model} 未找到")
                logger.info(f"可用模型: {', '.join(model_names)}")
                return False
        except Exception as e:
            logger.error(f"Ollama 服务不可用: {e}")
            return False

    def clean_single_batch(self, segments: List[Dict]) -> str:
        """
        清洗单批 segments

        Args:
            segments: 转录片段列表

        Returns:
            清洗后的文本
        """
        if not segments:
            return ""

        # 合并 segments 的文本
        raw_text = " ".join([seg.get('text', '') for seg in segments])

        if not raw_text.strip():
            return ""

        # 构建提示词
        prompt = self.CLEANING_PROMPT.format(text=raw_text)

        try:
            # 调用 Ollama
            response = self.client.chat(
                model=self.model,
                messages=[
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                options={
                    'temperature': 0.3,  # 降低温度以获得更一致的输出
                    'top_p': 0.9,
                }
            )

            # 提取清洗后的文本
            cleaned_text = response['message']['content'].strip()
            return cleaned_text

        except Exception as e:
            logger.error(f"调用 Ollama 失败: {e}")
            # 失败时返回原始文本
            return raw_text

    def clean_transcript(self, transcript: Dict, parallel: bool = True) -> Dict:
        """
        清洗整个转录结果

        Args:
            transcript: 转录结果字典
            parallel: 是否并行处理

        Returns:
            包含清洗后文本的转录结果
        """
        if not transcript or 'segments' not in transcript:
            return transcript

        segments = transcript['segments']
        if not segments:
            return transcript

        logger.info(f"开始清洗转录文本，共 {len(segments)} 个片段")

        # 将 segments 分批
        batches = []
        for i in range(0, len(segments), self.batch_size):
            batch = segments[i:i + self.batch_size]
            batches.append((i, batch))

        # 处理每批
        cleaned_paragraphs = []

        if parallel and len(batches) > 1:
            # 并行处理
            logger.info(f"并行清洗 {len(batches)} 批文本...")

            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # 提交所有任务
                future_to_batch = {
                    executor.submit(self.clean_single_batch, batch): (idx, batch)
                    for idx, batch in batches
                }

                # 收集结果
                results = {}
                for future in tqdm(as_completed(future_to_batch), total=len(batches), desc="清洗进度"):
                    idx, batch = future_to_batch[future]
                    try:
                        cleaned_text = future.result()
                        results[idx] = {
                            'text': cleaned_text,
                            'source_segments': [s['id'] for s in batch if 'id' in s],
                            'start_time': batch[0].get('start', 0) if batch else 0,
                            'end_time': batch[-1].get('end', 0) if batch else 0
                        }
                    except Exception as e:
                        logger.error(f"批次 {idx} 清洗失败: {e}")
                        # 使用原始文本作为后备
                        raw_text = " ".join([s.get('text', '') for s in batch])
                        results[idx] = {
                            'text': raw_text,
                            'source_segments': [s['id'] for s in batch if 'id' in s],
                            'start_time': batch[0].get('start', 0) if batch else 0,
                            'end_time': batch[-1].get('end', 0) if batch else 0
                        }

                # 按原始顺序排序
                for idx in sorted(results.keys()):
                    cleaned_paragraphs.append(results[idx])

        else:
            # 串行处理
            logger.info(f"串行清洗 {len(batches)} 批文本...")

            for idx, batch in tqdm(batches, desc="清洗进度"):
                cleaned_text = self.clean_single_batch(batch)
                cleaned_paragraphs.append({
                    'id': idx // self.batch_size,
                    'text': cleaned_text,
                    'source_segments': [s['id'] for s in batch if 'id' in s],
                    'start_time': batch[0].get('start', 0) if batch else 0,
                    'end_time': batch[-1].get('end', 0) if batch else 0
                })

        # 更新转录结果
        result = transcript.copy()
        result['paragraphs'] = cleaned_paragraphs
        result['cleaned_text'] = "\n\n".join([p['text'] for p in cleaned_paragraphs])

        logger.info(f"文本清洗完成，生成 {len(cleaned_paragraphs)} 个段落")
        return result

    def clean_text_simple(self, text: str) -> str:
        """
        简单的文本清洗（不分批）

        Args:
            text: 原始文本

        Returns:
            清洗后的文本
        """
        if not text.strip():
            return text

        prompt = self.CLEANING_PROMPT.format(text=text)

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
            logger.error(f"文本清洗失败: {e}")
            return text


if __name__ == "__main__":
    # 简单测试
    cleaner = TextCleaner(model="deepseek-r1:14b")

    # 检查 Ollama
    if not cleaner.check_ollama():
        print("请确保 Ollama 服务正在运行并安装了 deepseek-r1:14b 模型")
        exit(1)

    # 测试清洗单个文本
    test_text = "嗯这个呢就是说我们今天要讲的这个内容啊其实也不是很复杂就是说你只要理解了这个概念然后呢多练习练习就可以了"

    print("原始文本:")
    print(test_text)
    print("\n 清洗后:")
    cleaned = cleaner.clean_text_simple(test_text)
    print(cleaned)