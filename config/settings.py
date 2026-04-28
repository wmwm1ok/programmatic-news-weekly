"""
周报自动化系统配置文件
"""

import os
from datetime import datetime

# =============================================================================
# API 配置
# =============================================================================

# Claude API 配置
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
CLAUDE_ENDPOINT = os.getenv(
    "CLAUDE_ENDPOINT",
    "http://osagw.simeji.me/gbu/rest/v1/ai_chat/claude_service",
)
CLAUDE_MODEL = os.getenv(
    "CLAUDE_MODEL",
    "us.anthropic.claude-sonnet-4-20250514-v1:0",
)

# =============================================================================
# 邮件配置
# =============================================================================

EMAIL_CONFIG = {
    "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
    "smtp_port": int(os.getenv("SMTP_PORT", "587")),
    "username": os.getenv("EMAIL_USERNAME", ""),
    "password": os.getenv("EMAIL_PASSWORD", ""),
    "from_addr": os.getenv("EMAIL_FROM", ""),
    "to_addr": os.getenv("EMAIL_TO", "wangmeng42@baidu.com"),
    "subject_template": "竞品周报 {start_date} ~ {end_date}",
}

# =============================================================================
# 竞品资讯来源配置（13家公司）
# =============================================================================

COMPETITOR_SOURCES = {
    "TTD": {
        "name": "TTD",
        "url": "https://www.thetradedesk.com/press-room",
        "type": "press_room",
    },
    "Criteo": {
        "name": "Criteo",
        "url": "https://criteo.investorroom.com/releases",
        "type": "investor_room",
    },
    "Taboola": {
        "name": "Taboola",
        "url": "https://www.taboola.com/press-releases/",
        "type": "press_releases",
    },
    "Teads": {
        "name": "Teads",
        "url": "https://www.teads.com/press-releases/",
        "type": "press_releases",
    },
    "AppLovin": {
        "name": "AppLovin",
        "url": "https://investors.applovin.com/",
        "type": "investor",
    },
    "mobvista": {
        "name": "mobvista",
        "url": "https://www.mobvista.com/en/investor-relations/overview",
        "type": "investor",
    },
    "Moloco": {
        "name": "Moloco",
        "url": "https://www.moloco.com/newsroom",
        "type": "newsroom",
    },
    "BIGO Ads": {
        "name": "BIGO Ads",
        "url": "https://www.bigoads.com/resources/blog",
        "type": "blog",
    },
    "TopOn": {
        "name": "TopOn",
        "url": "https://www.toponad.net/en/posts",
        "type": "blog",
    },
    "Unity": {
        "name": "Unity",
        "url": "https://unity.com/news",
        "type": "news",
    },
    "Viant Technology": {
        "name": "Viant Technology",
        "url": "https://www.viantinc.com/company/news/press-releases/",
        "type": "press_releases",
    },
    "Zeta Global": {
        "name": "Zeta Global",
        "url": "https://investors.zetaglobal.com/news/default.aspx",
        "type": "investor_news",
    },
    "PubMatic": {
        "name": "PubMatic",
        "url": "https://investors.pubmatic.com/news-events/news-releases/",
        "type": "news_releases",
    },
    "Magnite": {
        "name": "Magnite",
        "url": "https://investor.magnite.com/press-releases",
        "type": "press_releases",
    },
}

# =============================================================================
# 行业资讯来源配置（2个来源）
# - AdExchanger: 抓 Popular 前 5 条
# - Search Engine Land: 抓最新 3 条
# =============================================================================

INDUSTRY_SOURCES = {
    "AdExchanger": {
        "name": "AdExchanger",
        "url": "https://www.adexchanger.com/",
        "max_items": 5,
    },
    "Search Engine Land": {
        "name": "Search Engine Land",
        "url": "https://searchengineland.com/latest-posts",
        "max_items": 3,
    },
}

# =============================================================================
# 抓取配置
# =============================================================================

SCRAPER_CONFIG = {
    "timeout": 30,  # 增加超时时间
    "retry_times": 3,  # 增加重试次数
    "retry_delay": 2,
    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "headers": {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    },
}

# =============================================================================
# 内容配置
# =============================================================================

CONTENT_CONFIG = {
    "summary_min_length": 80,
    "summary_max_length": 100,
    "industry_max_items": 3,
}

# =============================================================================
# 输出配置
# =============================================================================

OUTPUT_CONFIG = {
    "output_dir": "output",
    "filename_template": "weekly-report-{start_date}_{end-date}.html",
}


def get_date_window(run_date: datetime = None, days: int = 7):
    """
    获取时间窗口
    :param run_date: 运行日期，默认为今天
    :param days: 窗口天数（默认10天，抓取最近10天）
    :return: (window_start, window_end)
    """
    from datetime import timedelta
    
    if run_date is None:
        run_date = datetime.now()
    
    window_end = run_date
    window_start = run_date - timedelta(days=days)
    
    return window_start, window_end


def format_date(date_obj: datetime) -> str:
    """格式化日期为 YYYY-MM-DD"""
    return date_obj.strftime("%Y-%m-%d")
