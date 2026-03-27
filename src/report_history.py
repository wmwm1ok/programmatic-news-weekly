"""
历史周报去重辅助工具
"""

import re
from typing import Dict, Iterable, List, Set, Tuple

import requests

from fetchers.base import ContentItem


PUBLISHED_REPORT_URLS = [
    "https://wmwm1ok.github.io/programmatic-news-weekly/latest.md",
    "https://wmwm1ok.github.io/programmatic-news-weekly/index.html",
]


def normalize_title(text: str) -> str:
    return re.sub(r"\W+", "", (text or "").lower())


def normalize_url(url: str) -> str:
    return (url or "").split("?", 1)[0].rstrip("/").lower()


def item_signature(item: ContentItem) -> Tuple[str, str]:
    return normalize_title(item.title), normalize_url(item.url)


def load_previous_report_signatures(timeout: int = 15) -> Set[Tuple[str, str]]:
    """从线上上一期报告中提取标题/链接签名。"""
    session = requests.Session()
    signatures: Set[Tuple[str, str]] = set()

    for url in PUBLISHED_REPORT_URLS:
        try:
            response = session.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
            signatures.update(_extract_signatures(response.text, url))
            if signatures:
                break
        except Exception:
            continue

    return signatures


def filter_historical_duplicates(items: Iterable[ContentItem], previous_signatures: Set[Tuple[str, str]]) -> List[ContentItem]:
    filtered: List[ContentItem] = []
    seen_current: Set[Tuple[str, str]] = set()

    for item in items:
        signature = item_signature(item)
        if signature in previous_signatures or signature in seen_current:
            continue
        filtered.append(item)
        seen_current.add(signature)

    return filtered


def filter_competitor_results(
    competitor_results: Dict[str, List[ContentItem]],
    previous_signatures: Set[Tuple[str, str]],
) -> Dict[str, List[ContentItem]]:
    return {
        company: filter_historical_duplicates(items, previous_signatures)
        for company, items in competitor_results.items()
    }


def _extract_signatures(content: str, source_url: str) -> Set[Tuple[str, str]]:
    if source_url.endswith(".md"):
        return _extract_markdown_signatures(content)
    return _extract_html_signatures(content)


def _extract_markdown_signatures(content: str) -> Set[Tuple[str, str]]:
    signatures: Set[Tuple[str, str]] = set()
    current_title = ""

    for raw_line in content.splitlines():
        line = raw_line.strip()
        title_match = re.match(r"^\d+\.\s+\*\*(.+?)\*\*$", line)
        if title_match:
            current_title = title_match.group(1).strip()
            continue

        link_match = re.match(r"^-+\s+链接：(.+)$", line)
        if current_title and link_match:
            signatures.add((normalize_title(current_title), normalize_url(link_match.group(1).strip())))
            current_title = ""

    return signatures


def _extract_html_signatures(content: str) -> Set[Tuple[str, str]]:
    signatures: Set[Tuple[str, str]] = set()
    rows = re.findall(
        r'<p class="item-title">(.*?)</p>.*?<a href="([^"]+)"',
        content,
        flags=re.S,
    )

    for raw_title, raw_url in rows:
        title = re.sub(r"<[^>]+>", "", raw_title).strip()
        signatures.add((normalize_title(title), normalize_url(raw_url)))

    return signatures
