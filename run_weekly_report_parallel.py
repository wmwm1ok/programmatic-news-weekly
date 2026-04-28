#!/usr/bin/env python3
"""
并行周报整合脚本
- 读取各分支抓取的结果（artifacts）
- 抓取 main 负责的公司（TTD, Criteo, Taboola, Teads, 行业资讯）
- 整合生成完整报告并发送邮件
"""

import json
import os
import sys
import traceback
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, 'src')

from fetchers.hybrid_fetcher import HybridCompetitorFetcher
from fetchers.industry_fetcher import IndustryFetcher
from summarizer import Summarizer
from renderer import HTMLRenderer, save_report_outputs
from email_sender import send_weekly_report
from fetchers.base import ContentItem


def load_artifacts():
    """加载各分支抓取的结果"""
    artifacts_dir = Path('artifacts')
    results = {}
    
    if not artifacts_dir.exists():
        print("⚠️ No artifacts directory found")
        return results
    
    for json_file in artifacts_dir.glob('*_result.json'):
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                company = data.get('company')
                items = data.get('items', [])
                if company and items:
                    results[company] = [ContentItem(**item) for item in items]
                    print(f"  ✓ Loaded {company}: {len(items)} 条")
        except Exception as e:
            print(f"  ✗ Error loading {json_file}: {e}")
    
    return results


def fetch_main_companies(window_start, window_end):
    """抓取 main 分支负责的公司"""
    # main 负责: TTD, Criteo, Taboola, Teads (已经在 hybrid_fetcher 中)
    # 但前面并行的公司已经通过 artifacts 加载了
    # 这里只需要抓取行业资讯
    
    print("\n抓取行业资讯...")
    industry_items = {}
    total_ind = 0
    
    try:
        ind_fetcher = IndustryFetcher()
        industry_items = ind_fetcher.fetch_all(window_start, window_end)
        total_ind = sum(len(v) for v in industry_items.values())
        
        for module, items in industry_items.items():
            if items:
                print(f"  {module}: {len(items)} 条")
        
        print(f"  行业总计: {total_ind} 条")
    except Exception as e:
        print(f"  ❌ 抓取行业资讯失败: {e}")
        traceback.print_exc()
    
    return industry_items


def main():
    print("=" * 70)
    print("竞品周报整合系统 - 并行版本")
    print("=" * 70)
    
    # 计算日期窗口
    window_end = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
    window_start = (window_end - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
    start_str = str(window_start.date())
    end_str = str(window_end.date())
    
    print(f"\n📅 日期窗口: {start_str} ~ {end_str}")
    
    # 检查邮件配置
    email_username = os.getenv('EMAIL_USERNAME')
    email_password = os.getenv('EMAIL_PASSWORD')
    send_email = bool(email_username and email_password)
    
    if send_email:
        print(f"✓ 邮件配置就绪: {email_username}")
    else:
        print("⚠️ 邮件未配置，将只生成报告")
    
    # 检查 Claude API
    api_key = os.getenv('CLAUDE_API_KEY')
    use_ai_summary = bool(api_key)
    print(f"{'✓' if use_ai_summary else '⚠️'} Claude API: {'已配置' if use_ai_summary else '未配置'}")
    
    # 1. 加载各分支抓取的结果
    print("\n[1/4] 加载各分支抓取结果...")
    competitor_results = load_artifacts()
    competitor_items = []
    for company, items in competitor_results.items():
        competitor_items.extend(items)
    print(f"  从 artifacts 加载: {len(competitor_items)} 条")
    
    # 2. 抓取行业资讯
    print("\n[2/4] 抓取行业资讯...")
    industry_items = fetch_main_companies(window_start, window_end)
    total_ind = sum(len(v) for v in industry_items.values())
    
    # 3. 生成中文摘要
    if use_ai_summary and (competitor_items or total_ind > 0):
        print("\n[3/4] 使用 Claude Sonnet 4 生成中文摘要...")
        try:
            summarizer = Summarizer()
            
            for i, item in enumerate(competitor_items, 1):
                print(f"  [{i}/{len(competitor_items)}] {item.title[:35]}...")
                try:
                    item.summary = summarizer.summarize(item.title, item.summary)
                    print(f"      ✓ {len(item.summary)} 字")
                except Exception as e:
                    print(f"      ✗ 失败: {e}")
            
            for module, items in industry_items.items():
                for item in items:
                    print(f"  [行业-{module}] {item.title[:35]}...")
                    try:
                        item.summary = summarizer.summarize(item.title, item.summary)
                        print(f"      ✓ {len(item.summary)} 字")
                    except Exception as e:
                        print(f"      ✗ 失败: {e}")
        except Exception as e:
            print(f"❌ 摘要生成失败: {e}")
    else:
        print("\n[3/4] 跳过 AI 摘要生成")
    
    # 4. 生成报告并发送
    print("\n[4/4] 生成 HTML 报告...")
    try:
        renderer = HTMLRenderer()
        html = renderer.render(competitor_results, industry_items, start_str, end_str)
        
        # 保存
        outputs = save_report_outputs(
            competitor_results,
            industry_items,
            start_str,
            end_str,
            html_content=html,
            html_renderer=renderer,
        )
        output_path = outputs["html_path"]
        print(f"\n✅ HTML 报告已保存: {output_path}")
        print(f"✅ Markdown 报告已保存: {outputs['markdown_path']}")
        
        # 发送邮件
        if send_email:
            print("\n📧 发送邮件...")
            success = send_weekly_report(html, start_str, end_str)
            if success:
                print("\n" + "=" * 70)
                print("✅ 周报生成并发送成功!")
                print("=" * 70)
            else:
                print("\n⚠️ 邮件发送失败")
        else:
            print("\n" + "=" * 70)
            print("✅ 周报已生成")
            print("=" * 70)
        
        print(f"\n统计:")
        print(f"  竞品资讯: {len(competitor_items)} 条")
        print(f"  行业资讯: {total_ind} 条")
        print(f"  总计: {len(competitor_items) + total_ind} 条")
        
    except Exception as e:
        print(f"❌ 生成报告失败: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
