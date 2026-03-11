#!/usr/bin/env python3
"""
快速周报生成 - 只抓取，使用模拟摘要
"""

import os
import sys
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from datetime import datetime, timedelta
from config.settings import get_date_window, format_date
from fetchers.competitor_fetcher_v2 import CompetitorFetcherV2
from fetchers.industry_fetcher import IndustryFetcher
from summarizer import MockSummarizer
from validator import Validator
from renderer import HTMLRenderer, save_report_outputs
from mailer import MockMailer

def generate_quick_report():
    """生成快速报告（使用模拟摘要）"""
    print("=" * 60)
    print("周报生成（快速模式）")
    print("=" * 60)
    
    # 使用 30 天窗口抓取更多内容
    window_end = datetime(2026, 2, 12)
    window_start = window_end - timedelta(days=30)
    start_str = format_date(window_start)
    end_str = format_date(window_end)
    
    print(f"\n时间窗口: {start_str} ~ {end_str}\n")
    
    # 1. 抓取竞品
    print("[1/4] 抓取竞品资讯...")
    competitor_fetcher = CompetitorFetcherV2()
    competitor_items = competitor_fetcher.fetch_all(window_start, window_end)
    comp_count = sum(len(v) for v in competitor_items.values())
    print(f"  抓到 {len(competitor_items)} 家公司，{comp_count} 条")
    for company, items in competitor_items.items():
        print(f"    - {company}: {len(items)} 条")
    
    # 2. 抓取行业
    print("\n[2/4] 抓取行业资讯...")
    industry_fetcher = IndustryFetcher()
    industry_items = industry_fetcher.fetch_all(window_start, window_end)
    ind_count = sum(len(v) for v in industry_items.values())
    print(f"  抓到 {ind_count} 条")
    
    # 3. 生成模拟摘要
    print("\n[3/4] 生成摘要（模拟模式）...")
    summarizer = MockSummarizer()
    
    for company, items in competitor_items.items():
        for item in items:
            item.summary = summarizer.summarize(item.title, item.summary)
    
    for module, items in industry_items.items():
        for item in items:
            item.summary = summarizer.summarize(item.title, item.summary)
    
    print(f"  已生成 {comp_count + ind_count} 条摘要")
    
    # 4. 验证
    print("\n[4/4] 验证并生成 HTML...")
    validator = Validator()
    competitor_valid, _ = validator.validate_competitor_items(competitor_items, window_start, window_end)
    industry_valid, _ = validator.validate_industry_items(industry_items, window_start, window_end)
    
    # 5. 生成 HTML
    renderer = HTMLRenderer()
    html = renderer.render(competitor_valid, industry_valid, start_str, end_str)
    outputs = save_report_outputs(
        competitor_valid,
        industry_valid,
        start_str,
        end_str,
        html_content=html,
        html_renderer=renderer,
    )
    output_path = outputs["html_path"]
    
    # 6. 模拟发送邮件
    mailer = MockMailer()
    mailer.send(html, start_str, end_str, output_path)
    
    print(f"\n{'=' * 60}")
    print(f"✅ 周报生成成功!")
    print(f"  HTML 文件: {output_path}")
    print(f"  Markdown 文件: {outputs['markdown_path']}")
    print(f"  竞品: {sum(len(v) for v in competitor_valid.values())} 条")
    print(f"  行业: {sum(len(v) for v in industry_valid.values())} 条")
    print('=' * 60)
    
    return {
        "success": True,
        "output_path": output_path,
        "markdown_output_path": outputs["markdown_path"],
        "competitor_count": sum(len(v) for v in competitor_valid.values()),
        "industry_count": sum(len(v) for v in industry_valid.values()),
    }

if __name__ == "__main__":
    result = generate_quick_report()
    sys.exit(0 if result["success"] else 1)
