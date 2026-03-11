#!/usr/bin/env python3
"""
竞品周报自动化脚本
- 抓取竞品资讯和行业资讯
- 生成 HTML 报告
- 发送邮件（HTML 正文形式）

环境变量:
- DEEPSEEK_API_KEY: DeepSeek API 密钥（用于生成中文摘要）
- SMTP_SERVER: SMTP 服务器（默认: smtp.gmail.com）
- SMTP_PORT: SMTP 端口（默认: 587）
- EMAIL_USERNAME: 发件邮箱用户名
- EMAIL_PASSWORD: 发件邮箱密码
- EMAIL_FROM: 发件人地址（默认与用户名相同）
- EMAIL_TO: 收件人地址（默认: wangmeng42@baidu.com）

定时任务:
- 北京时间每周一早上 8:00
- GitHub Actions: 0 0 * * 1 (UTC 周一 00:00 = 北京周一 08:00)
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
from email_sender import send_weekly_report


def main():
    print("=" * 70)
    print("竞品周报自动化系统")
    print("=" * 70)
    
    # 计算日期窗口（最近7天）
    window_end = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
    window_start = (window_end - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
    start_str = str(window_start.date())
    end_str = str(window_end.date())
    
    print(f"\n📅 日期窗口: {start_str} ~ {end_str}")
    
    # 检查必要的环境变量
    email_username = os.getenv('EMAIL_USERNAME')
    email_password = os.getenv('EMAIL_PASSWORD')
    
    if not email_username or not email_password:
        print("\n⚠️ 警告: 未设置 EMAIL_USERNAME 或 EMAIL_PASSWORD，将只生成报告不发送邮件")
        send_email = False
    else:
        print(f"✓ 邮件配置: {email_username}")
        send_email = True
    
    # 检查 DeepSeek API Key（可选）
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if api_key:
        print(f"✓ DeepSeek API 已配置")
        use_ai_summary = True
    else:
        print(f"⚠️ 未设置 DEEPSEEK_API_KEY，将使用原文摘要")
        use_ai_summary = False
    
    # 1. 抓取竞品资讯（总超时 8 分钟）
    print("\n[1/4] 抓取竞品资讯...")
    competitor_results = {}
    competitor_items = []
    
    try:
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("抓取总超时")
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(480)  # 8分钟总超时
        
        fetcher = HybridCompetitorFetcher()
        competitor_results = fetcher.fetch_all(window_start, window_end)
        
        signal.alarm(0)  # 取消超时
        
        for company, items in competitor_results.items():
            competitor_items.extend(items)
            print(f"  {company}: {len(items)} 条")
        
        print(f"  竞品总计: {len(competitor_items)} 条")
        
    except TimeoutError:
        print("⚠️ 竞品抓取超时，使用已获取的数据")
        for company, items in competitor_results.items():
            competitor_items.extend(items)
    except Exception as e:
        print(f"❌ 抓取竞品失败: {e}")
        traceback.print_exc()
    
    # 2. 抓取行业资讯
    print("\n[2/4] 抓取行业资讯...")
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
        print(f"❌ 抓取行业资讯失败: {e}")
        traceback.print_exc()
    
    # 3. 生成中文摘要（可选）
    if use_ai_summary and (competitor_items or total_ind > 0):
        print("\n[3/4] 使用 DeepSeek 生成中文摘要...")
        
        try:
            summarizer = Summarizer()
            
            # 竞品摘要
            for i, item in enumerate(competitor_items, 1):
                print(f"  [竞品 {i}/{len(competitor_items)}] {item.title[:35]}...")
                try:
                    item.summary = summarizer.summarize(item.title, item.summary)
                    print(f"      ✓ {len(item.summary)} 字")
                except Exception as e:
                    print(f"      ✗ 摘要生成失败: {e}")
                    item.summary = item.summary[:100] if item.summary else "摘要生成失败"
            
            # 行业摘要
            for module, items in industry_items.items():
                for item in items:
                    print(f"  [行业-{module}] {item.title[:35]}...")
                    try:
                        item.summary = summarizer.summarize(item.title, item.summary)
                        print(f"      ✓ {len(item.summary)} 字")
                    except Exception as e:
                        print(f"      ✗ 摘要生成失败: {e}")
                        item.summary = item.summary[:100] if item.summary else "摘要生成失败"
        
        except Exception as e:
            print(f"❌ 摘要生成模块失败: {e}")
            traceback.print_exc()
    else:
        print("\n[3/4] 跳过 AI 摘要生成")
    
    # 4. 生成 HTML 报告
    print("\n[4/4] 生成 HTML 报告...")
    
    try:
        renderer = HTMLRenderer()
        html = renderer.render(competitor_results, industry_items, start_str, end_str)
        
        # 保存到本地
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
        
        # 5. 发送邮件
        if send_email:
            print("\n📧 正在发送邮件...")
            success = send_weekly_report(html, start_str, end_str)
            
            if success:
                print("\n" + "=" * 70)
                print("✅ 周报生成并发送成功!")
                print("=" * 70)
            else:
                print("\n" + "=" * 70)
                print("⚠️ 报告已生成但邮件发送失败")
                print("=" * 70)
                sys.exit(1)
        else:
            print("\n" + "=" * 70)
            print("✅ 周报已生成（未发送邮件）")
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
