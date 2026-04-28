#!/usr/bin/env python3
"""
使用 Claude API 生成真实摘要
从环境变量读取 API Key，支持 GitHub Actions 运行
"""

import os
import sys
import traceback

sys.path.insert(0, 'src')

from datetime import datetime, timedelta
from fetchers.hybrid_fetcher import HybridCompetitorFetcher
from fetchers.industry_fetcher import IndustryFetcher
from summarizer import Summarizer
from renderer import HTMLRenderer, save_report_outputs

print("=" * 70)
print("使用 Claude API 生成周报")
print("=" * 70)

# 使用当前日期作为窗口结束日期
window_end = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
window_start = (window_end - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
start_str = str(window_start.date())
end_str = str(window_end.date())

print(f"\n日期窗口: {start_str} ~ {end_str}")

# 检查 API Key
api_key = os.getenv('CLAUDE_API_KEY')
if not api_key:
    print("\n❌ 错误: 未设置 CLAUDE_API_KEY 环境变量")
    sys.exit(1)
else:
    print(f"✓ API Key 已设置")

# 1. 抓取竞品资讯
print("\n[1/4] 抓取竞品资讯...")
competitor_results = {}
try:
    # 设置超时，避免无限等待
    import signal
    
    def timeout_handler(signum, frame):
        raise TimeoutError("抓取超时")
    
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(300)  # 5分钟超时
    
    fetcher = HybridCompetitorFetcher()
    competitor_results = fetcher.fetch_all(window_start, window_end)
    
    signal.alarm(0)  # 取消超时
    
    competitor_items = []
    for company, items in competitor_results.items():
        competitor_items.extend(items)
        print(f"  {company}: {len(items)} 条")
    print(f"  竞品总计: {len(competitor_items)} 条")
    
except TimeoutError:
    print("⚠️ 竞品抓取超时，使用已获取的数据")
    competitor_items = []
    for company, items in competitor_results.items():
        competitor_items.extend(items)
except Exception as e:
    print(f"❌ 抓取竞品失败: {e}")
    traceback.print_exc()
    competitor_results = {}
    competitor_items = []

# 2. 抓取行业资讯
print("\n[2/4] 抓取行业资讯...")
industry_items = {}
total_ind = 0
try:
    ind_fetcher = IndustryFetcher()
    industry_items = ind_fetcher.fetch_all(window_start, window_end)
    total_ind = sum(len(v) for v in industry_items.values())
    print(f"  行业资讯: {total_ind} 条")
    for module, items in industry_items.items():
        if items:
            print(f"    - {module}: {len(items)} 条")
except Exception as e:
    print(f"❌ 抓取行业资讯失败: {e}")
    traceback.print_exc()
    industry_items = {}
    total_ind = 0

# 3. 使用 Claude 生成摘要
print("\n[3/4] 使用 Claude Sonnet 4 生成中文摘要...")

try:
    summarizer = Summarizer()
    
    # 竞品摘要
    if competitor_items:
        for i, item in enumerate(competitor_items, 1):
            print(f"  [竞品 {i}/{len(competitor_items)}] {item.title[:35]}...")
            try:
                item.summary = summarizer.summarize(item.title, item.summary)
                print(f"      ✓ {len(item.summary)} 字")
            except Exception as e:
                print(f"      ✗ 摘要生成失败: {e}")
                item.summary = item.summary[:100] if item.summary else "摘要生成失败"
    else:
        print("  没有竞品内容需要生成摘要")
    
    # 行业摘要
    if total_ind > 0:
        for module, items in industry_items.items():
            for item in items:
                print(f"  [行业-{module}] {item.title[:35]}...")
                try:
                    item.summary = summarizer.summarize(item.title, item.summary)
                    print(f"      ✓ {len(item.summary)} 字")
                except Exception as e:
                    print(f"      ✗ 摘要生成失败: {e}")
                    item.summary = item.summary[:100] if item.summary else "摘要生成失败"
    else:
        print("  没有行业内容需要生成摘要")
        
except Exception as e:
    print(f"❌ 摘要生成模块失败: {e}")
    traceback.print_exc()

# 4. 生成报告
print("\n[4/4] 生成 HTML...")
try:
    renderer = HTMLRenderer()
    html = renderer.render(competitor_results, industry_items, start_str, end_str)
    outputs = save_report_outputs(
        competitor_results,
        industry_items,
        start_str,
        end_str,
        html_content=html,
        html_renderer=renderer,
    )
    output_path = outputs["html_path"]
    
    print(f"\n{'=' * 70}")
    print(f"✅ HTML 周报已生成: {output_path}")
    print(f"✅ Markdown 周报已生成: {outputs['markdown_path']}")
    print(f"  竞品: {len(competitor_items)} 条")
    print(f"  行业: {total_ind} 条")
    print(f"  总计: {len(competitor_items) + total_ind} 条")
    print('=' * 70)
    
    if os.path.exists(output_path):
        file_size = os.path.getsize(output_path)
        print(f"✓ 文件大小: {file_size} bytes")
    else:
        print("❌ 警告: 输出文件未找到")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ 生成 HTML 失败: {e}")
    traceback.print_exc()
    sys.exit(1)
