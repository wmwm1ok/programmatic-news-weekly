#!/usr/bin/env python3
"""
周报自动化系统 - 主程序入口
"""

import os
import sys
import argparse
from datetime import datetime

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from config.settings import get_date_window, format_date, OUTPUT_CONFIG
from fetchers import CompetitorFetcher, IndustryFetcher
from fetchers.async_fetcher import AsyncCompetitorFetcher, AsyncIndustryFetcher
from fetchers.competitor_fetcher_v2 import CompetitorFetcherV2
from fetchers.hybrid_fetcher import HybridCompetitorFetcher
from summarizer import Summarizer, MockSummarizer
from validator import Validator, ValidationError
from renderer import HTMLRenderer, save_report_outputs
from mailer import Mailer, MockMailer


def main(run_date: datetime = None, test_mode: bool = False, dry_run: bool = False) -> dict:
    """
    主程序入口
    :param run_date: 运行日期，默认为今天
    :param test_mode: 测试模式（使用模拟组件）
    :param dry_run: 演示模式（生成示例报告）
    :return: 执行结果
    """
    print("=" * 60)
    print("周报自动化系统")
    print("=" * 60)
    
    # 1. 确定时间窗口
    window_start, window_end = get_date_window(run_date)
    start_date_str = format_date(window_start)
    end_date_str = format_date(window_end)
    
    print(f"\n时间窗口: {start_date_str} ~ {end_date_str}")
    
    # 2. 初始化组件
    print("\n[1/6] 初始化组件...")
    
    if dry_run:
        print("  运行模式: 演示模式（生成示例报告）")
        return generate_demo_report(start_date_str, end_date_str)
    
    # 使用混合抓取器 (HTTP + Playwright)
    competitor_fetcher = HybridCompetitorFetcher()
    industry_fetcher = AsyncIndustryFetcher()
    
    if test_mode:
        summarizer = MockSummarizer()
        mailer = MockMailer()
        print("  运行模式: 测试模式（使用模拟组件）")
    else:
        try:
            summarizer = Summarizer()
            print("  摘要生成器: DeepSeek API")
        except ValueError as e:
            print(f"  ⚠️ {e}")
            print("  切换至模拟摘要生成器")
            summarizer = MockSummarizer()
        
        mailer = Mailer()
    
    validator = Validator()
    renderer = HTMLRenderer()
    
    # 3. 抓取竞品资讯
    try:
        competitor_items = competitor_fetcher.fetch_all(window_start, window_end)
        total_competitor = sum(len(items) for items in competitor_items.values())
        print(f"\n  抓取完成，共 {len(competitor_items)} 家公司，{total_competitor} 条内容")
        for company, items in competitor_items.items():
            print(f"    - {company}: {len(items)} 条")
    except Exception as e:
        return {
            "success": False,
            "error": f"抓取竞品资讯失败: {e}",
            "failures": [f"竞品资讯整体抓取失败: {e}"]
        }
    
    # 4. 抓取行业资讯
    print("\n[3/6] 抓取行业资讯...")
    try:
        industry_items = industry_fetcher.fetch_all(window_start, window_end)
        total_industry = sum(len(items) for items in industry_items.values())
        print(f"  抓取完成，共 {len(industry_items)} 个子模块，{total_industry} 条内容")
        for module, items in industry_items.items():
            print(f"    - {module}: {len(items)} 条")
    except Exception as e:
        return {
            "success": False,
            "error": f"抓取行业资讯失败: {e}",
            "failures": [f"行业资讯整体抓取失败: {e}"]
        }
    
    # 5. 生成摘要
    print("\n[4/6] 生成中文摘要...")
    
    # 竞品资讯摘要
    for company, items in competitor_items.items():
        if items:
            print(f"  处理 {company} ({len(items)} 条)...")
            competitor_items[company] = summarizer.summarize_batch(items)
    
    # 行业资讯摘要
    for module, items in industry_items.items():
        if items:
            print(f"  处理 {module} ({len(items)} 条)...")
            industry_items[module] = summarizer.summarize_batch(items)
    
    print("  摘要生成完成")
    
    # 6. 验证内容
    print("\n[5/6] 验证内容...")
    
    validated_competitor, competitor_errors = validator.validate_competitor_items(
        competitor_items, window_start, window_end
    )
    validated_industry, industry_errors = validator.validate_industry_items(
        industry_items, window_start, window_end
    )
    
    all_errors = competitor_errors + industry_errors
    
    if all_errors:
        error_report = validator.generate_error_report(all_errors)
        print(f"\n  ⚠️ 验证失败，共 {len(all_errors)} 个错误:\n")
        print(error_report)
        return {
            "success": False,
            "error": "内容验证失败",
            "failures": [
                {
                    "module": e.module,
                    "title": e.title,
                    "reason": e.reason,
                    "url": e.url
                } for e in all_errors
            ]
        }
    
    print("  ✓ 所有内容验证通过")
    
    # 7. 渲染 HTML
    print("\n[6/6] 渲染并保存 HTML...")
    html_content = renderer.render(
        validated_competitor,
        validated_industry,
        start_date_str,
        end_date_str
    )
    
    # 验证 PR 区块为空
    pr_valid, pr_error = validator.validate_pr_section_empty(html_content)
    if not pr_valid:
        return {
            "success": False,
            "error": f"PR 区块验证失败: {pr_error}",
            "failures": [f"PR 区块验证失败: {pr_error}"]
        }
    
    # 保存文件
    outputs = save_report_outputs(
        validated_competitor,
        validated_industry,
        start_date_str,
        end_date_str,
        html_content=html_content,
        html_renderer=renderer,
    )
    output_path = outputs["html_path"]
    print(f"  ✓ HTML 文件已保存: {output_path}")
    print(f"  ✓ Markdown 文件已保存: {outputs['markdown_path']}")
    
    # 8. 发送邮件
    print("\n[邮件发送]")
    mailer.send(html_content, start_date_str, end_date_str, output_path)
    
    # 返回成功结果
    return {
        "success": True,
        "output_path": output_path,
        "markdown_output_path": outputs["markdown_path"],
        "competitor_count": sum(len(items) for items in validated_competitor.values()),
        "industry_count": sum(len(items) for items in validated_industry.values()),
        "start_date": start_date_str,
        "end_date": end_date_str
    }


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='周报自动化系统')
    parser.add_argument(
        '--date', 
        type=str,
        help='运行日期 (YYYY-MM-DD)，默认为今天'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='测试模式（使用模拟组件，不调用真实 API）'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='演示模式（生成示例报告，不抓取真实数据）'
    )
    return parser.parse_args()


def generate_demo_report(start_date: str, end_date: str) -> dict:
    """生成演示报告"""
    print("\n[演示模式] 生成示例周报...")
    
    from fetchers.base import ContentItem
    
    # 示例竞品数据
    competitor_items = {
        "TTD": [
            ContentItem(
                title="TTD 推出全新广告定向功能，助力品牌精准触达目标受众",
                summary="TTD 于本周宣布推出基于 AI 的广告定向新功能，通过机器学习算法分析用户行为数据，可实现 95% 的定向准确率。该功能已在美国市场上线，预计 Q2 将扩展至欧洲和亚太地区，帮助广告主提升 ROI 约 30%。",
                date=end_date,
                url="https://www.thetradedesk.com/press-room/example",
                source="TTD"
            )
        ],
        "AppLovin": [
            ContentItem(
                title="AppLovin 发布 Q4 财报：营收同比增长 45% 超预期",
                summary="AppLovin 公布 2025 年 Q4 财报，营收达 12.5 亿美元，同比增长 45%，超出市场预期 8%。其中广告平台收入占比 78%，达 9.75 亿美元。公司预计 2026 年 Q1 营收将保持在 11-12 亿美元区间。",
                date=end_date,
                url="https://www.applovin.com/en/newsroom/example",
                source="AppLovin"
            )
        ]
    }
    
    # 示例行业数据
    industry_items = {
        "Artificial Intelligence": [
            ContentItem(
                title="Google 发布新一代 AI 广告引擎，竞价效率提升 40%",
                summary="Google 在本周 Marketing Live 大会上发布新一代 AI 驱动的广告竞价引擎，采用深度学习模型实时预测转化率，竞价效率较上一代提升 40%。新引擎将于 3 月向全球广告主开放，支持搜索、展示和视频广告。",
                date=end_date,
                url="https://www.adexchanger.com/artificial-intelligence/example",
                source="Artificial Intelligence"
            ),
            ContentItem(
                title="Meta 推出 AI 创意助手，可自动生成广告素材",
                summary="Meta 宣布推出 AI 创意助手工具，支持根据品牌指引自动生成图片和视频广告素材。该工具集成于 Ads Manager，目前向北美广告主开放测试，预计 6 月全面上线，可降低创意制作成本约 50%。",
                date=end_date,
                url="https://www.adexchanger.com/artificial-intelligence/example2",
                source="Artificial Intelligence"
            )
        ],
        "Platform": [
            ContentItem(
                title="亚马逊广告平台推出全渠道归因功能",
                summary="Amazon Ads 本周上线全渠道归因分析工具，可追踪从展示到购买的完整用户旅程，支持线下门店转化追踪。该功能目前对美国站卖家免费开放，帮助品牌优化跨渠道广告预算分配。",
                date=end_date,
                url="https://www.adexchanger.com/platforms/example",
                source="Platform"
            )
        ]
    }
    
    # 渲染 HTML
    renderer = HTMLRenderer()
    html_content = renderer.render(competitor_items, industry_items, start_date, end_date)
    
    # 保存文件
    outputs = save_report_outputs(
        competitor_items,
        industry_items,
        start_date,
        end_date,
        html_content=html_content,
        html_renderer=renderer,
    )
    output_path = outputs["html_path"]
    print(f"  ✓ HTML 示例报告已生成: {output_path}")
    print(f"  ✓ Markdown 示例报告已生成: {outputs['markdown_path']}")
    
    return {
        "success": True,
        "output_path": output_path,
        "markdown_output_path": outputs["markdown_path"],
        "competitor_count": sum(len(items) for items in competitor_items.values()),
        "industry_count": sum(len(items) for items in industry_items.values()),
        "start_date": start_date,
        "end_date": end_date,
        "demo": True
    }


if __name__ == "__main__":
    args = parse_args()
    
    # 解析日期
    run_date = None
    if args.date:
        try:
            run_date = datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            print(f"错误: 日期格式错误，应为 YYYY-MM-DD")
            sys.exit(1)
    
    # 运行主程序
    result = main(run_date=run_date, test_mode=args.test, dry_run=args.dry_run)
    
    # 输出结果
    print("\n" + "=" * 60)
    if result["success"]:
        print("✓ 执行成功")
        print(f"  输出文件: {result['output_path']}")
        print(f"  竞品资讯: {result['competitor_count']} 条")
        print(f"  行业资讯: {result['industry_count']} 条")
        sys.exit(0)
    else:
        print("✗ 执行失败")
        print(f"  错误: {result['error']}")
        if "failures" in result and result["failures"]:
            print(f"\n失败原因清单:")
            for i, failure in enumerate(result["failures"], 1):
                if isinstance(failure, dict):
                    print(f"  [{i}] {failure['module']} - {failure['reason']}")
                    print(f"      标题: {failure['title'][:50]}...")
                    print(f"      URL: {failure['url']}")
                else:
                    print(f"  [{i}] {failure}")
        sys.exit(1)
