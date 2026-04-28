"""
Claude 摘要生成模块
用于生成 80-100 字的中文摘要
"""

import re
import time
from typing import List, Optional

import requests

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
from claude_client import ClaudeClient
from fetchers.base import ContentItem
from config.settings import CLAUDE_API_KEY, CLAUDE_ENDPOINT, CLAUDE_MODEL, CONTENT_CONFIG


class Summarizer:
    """Claude 摘要生成器"""
    
    def __init__(self, api_key: str = None, api_base: str = None, model: str = None):
        self.api_key = api_key or CLAUDE_API_KEY
        self.api_base = api_base or CLAUDE_ENDPOINT
        self.model = model or CLAUDE_MODEL
        self.min_length = CONTENT_CONFIG["summary_min_length"]
        self.max_length = CONTENT_CONFIG["summary_max_length"]
        self.client = ClaudeClient(
            api_key=self.api_key,
            endpoint=self.api_base,
            model=self.model,
        )
        
        if not self.api_key:
            raise ValueError("Claude API Key 未设置，请设置 CLAUDE_API_KEY 环境变量")
    
    def summarize(self, title: str, content: str) -> str:
        """
        生成摘要
        :param title: 文章标题
        :param content: 文章内容
        :return: 80-100 字中文摘要
        """
        # 清理内容
        content = self._clean_content(content)
        
        # 截断内容以避免超出 token 限制
        content = content[:3000]
        
        prompt = f"""请根据以下文章标题和内容，生成一段{self.min_length}-{self.max_length}字的中文摘要。

要求：
1. 摘要必须包含原文的关键指标、关键事实（如：增长数据、营收、合作对象、产品/功能要点、时间节点等）
2. 摘要必须基于原文明确事实，禁止推测影响或引入主观判断
3. 摘要字数严格控制在{self.min_length}-{self.max_length}个中文字符（包含标点）
4. 直接输出摘要内容，不要有任何前缀或说明

文章标题：{title}

文章内容：{content}

请生成摘要："""

        try:
            response = self._call_api(prompt)
            if response:
                summary = self._clean_summary(response)
                # 验证长度
                if self._validate_length(summary):
                    return summary
                else:
                    # 如果长度不符合要求，尝试重新生成
                    return self._adjust_summary(summary)
            return ""
        except Exception as e:
            print(f"生成摘要失败: {e}")
            return ""
    
    def summarize_batch(self, items: List[ContentItem]) -> List[ContentItem]:
        """
        批量生成摘要
        :param items: 内容条目列表
        :return: 更新后的内容条目列表
        """
        results = []
        for i, item in enumerate(items):
            print(f"  生成摘要 [{i+1}/{len(items)}]: {item.title[:30]}...")
            summary = self.summarize(item.title, item.summary)
            if summary:
                item.summary = summary
                results.append(item)
            else:
                # 如果生成失败，保留原内容但标记
                print(f"    ⚠️ 摘要生成失败")
                item.summary = "[摘要生成失败]"
                results.append(item)
            # 避免请求过快
            time.sleep(0.5)
        return results
    
    def _call_api(self, prompt: str) -> Optional[str]:
        """
        调用 Claude API
        :param prompt: 提示词
        :return: API 响应内容
        """
        try:
            return self.client.generate(
                prompt,
                max_tokens=300,
                temperature=0.3,
                system="你是一个严格基于原文事实生成中文摘要的助手。",
            )
        except requests.exceptions.RequestException as e:
            print(f"API 请求失败: {e}")
            return None
        except Exception as e:
            print(f"API 调用异常: {e}")
            return None
    
    def _clean_content(self, content: str) -> str:
        """
        清理内容
        :param content: 原始内容
        :return: 清理后的内容
        """
        if not content:
            return ""
        
        # 移除多余空白
        content = re.sub(r'\s+', ' ', content)
        # 移除特殊字符
        content = content.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        # 移除 HTML 标签
        content = re.sub(r'<[^>]+>', '', content)
        
        return content.strip()
    
    def _clean_summary(self, summary: str) -> str:
        """
        清理摘要
        :param summary: 原始摘要
        :return: 清理后的摘要
        """
        if not summary:
            return ""
        
        # 移除前缀如"摘要："、"总结："等
        prefixes = ["摘要：", "摘要:", "总结：", "总结:", "概括：", "概括:", "简介：", "简介:"]
        for prefix in prefixes:
            if summary.startswith(prefix):
                summary = summary[len(prefix):]
        
        # 清理空白
        summary = summary.strip()
        
        # 确保不以标点结尾（除了句号）
        if summary and summary[-1] in ['，', '、', ' ']:
            summary = summary[:-1] + '。'
        
        return summary
    
    def _validate_length(self, summary: str) -> bool:
        """
        验证摘要长度
        :param summary: 摘要内容
        :return: 是否符合要求
        """
        # 只计算中文字符和标点
        length = len(summary)
        return self.min_length <= length <= self.max_length
    
    def _adjust_summary(self, summary: str) -> str:
        """
        调整摘要以符合长度要求
        :param summary: 原始摘要
        :return: 调整后的摘要
        """
        if not summary:
            return summary
        
        length = len(summary)
        
        if length < self.min_length:
            # 如果太短，返回原样（API 应该能生成足够长的内容）
            return summary
        elif length > self.max_length:
            # 如果太长，截断并确保以句号结尾
            summary = summary[:self.max_length]
            # 找到最后一个句号
            last_period = summary.rfind('。')
            if last_period > self.min_length:
                summary = summary[:last_period + 1]
            else:
                summary = summary[:self.max_length - 1] + '。'
        
        return summary
    
    def count_chinese_chars(self, text: str) -> int:
        """
        计算中文字符数（包含标点）
        :param text: 文本
        :return: 字符数
        """
        return len(text)


class MockSummarizer(Summarizer):
    """模拟摘要生成器（用于测试）"""
    
    def __init__(self, *args, **kwargs):
        self.min_length = CONTENT_CONFIG["summary_min_length"]
        self.max_length = CONTENT_CONFIG["summary_max_length"]
    
    def summarize(self, title: str, content: str) -> str:
        """生成模拟摘要"""
        # 提取内容的前 90 个中文字符作为模拟摘要
        mock_summary = content[:90] if len(content) > 90 else content
        if len(mock_summary) < self.min_length:
            mock_summary = mock_summary + "。该内容涉及数字广告行业动态，值得关注其后续发展及市场影响。"
        if len(mock_summary) > self.max_length:
            mock_summary = mock_summary[:self.max_length - 1] + "。"
        return mock_summary
    
    def _call_api(self, prompt: str) -> Optional[str]:
        return None
