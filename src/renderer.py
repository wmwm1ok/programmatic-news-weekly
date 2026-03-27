"""
报告渲染模块
"""

import os
from datetime import datetime
from typing import Dict, List, Optional

import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from fetchers.base import ContentItem
from config.settings import OUTPUT_CONFIG


REPORT_NAME = "程序化广告竞品及行业资讯"
REPORT_DESCRIPTION = "程序化广告竞品及行业资讯汇总，涵盖 13 家竞品与重点行业动态。"
EN_REPORT_NAME = "Programmatic Advertising Competitor and Industry News"
EN_REPORT_DESCRIPTION = "A weekly roundup of programmatic advertising competitor moves and key industry developments."
REPORT_COVER_URL = "https://wmwm1ok.github.io/programmatic-news-weekly/assets/programmatic-news-cover.jpg"


def build_report_title(start_date: str, end_date: str, language: str = "zh") -> str:
    """构建带日期的报告标题"""
    report_name = REPORT_NAME if language == "zh" else EN_REPORT_NAME
    return f"{report_name} {start_date} ~ {end_date}"


def ensure_output_dir() -> str:
    """确保输出目录存在"""
    output_dir = OUTPUT_CONFIG["output_dir"]
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def build_output_path(start_date: str, end_date: str, extension: str, prefix: str) -> str:
    """生成输出文件路径"""
    output_dir = ensure_output_dir()
    filename = f"{prefix}-{start_date}_{end_date}.{extension}"
    return os.path.join(output_dir, filename)


class HTMLRenderer:
    """HTML 渲染器"""

    def __init__(self, template_path: str = None, language: str = "zh"):
        self.template_path = template_path or os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "templates",
            "report_template.html"
        )
        self.language = language
        self.template = self._load_template()

    def _load_template(self) -> str:
        """加载 HTML 模板"""
        with open(self.template_path, 'r', encoding='utf-8') as f:
            return f.read()

    def render(self, competitor_items: Dict[str, List[ContentItem]],
               industry_items: Dict[str, List[ContentItem]],
               start_date: str, end_date: str) -> str:
        """渲染 HTML 报告"""
        html = self.template
        labels = self._html_labels()

        html = html.replace("{{START_DATE}}", start_date)
        html = html.replace("{{END_DATE}}", end_date)
        html = html.replace("{{GENERATED_AT}}", datetime.now().strftime("%Y-%m-%d %H:%M"))
        html = html.replace("{{REPORT_TITLE}}", build_report_title(start_date, end_date, self.language))
        html = html.replace(
            "{{REPORT_DESCRIPTION}}",
            REPORT_DESCRIPTION if self.language == "zh" else EN_REPORT_DESCRIPTION,
        )
        html = html.replace("{{REPORT_COVER_URL}}", REPORT_COVER_URL)
        for key, value in labels.items():
            html = html.replace(f"{{{{{key}}}}}", value)

        competitor_html = self._render_competitor_section(competitor_items)
        html = html.replace("{{COMPETITOR_SECTION_HTML}}", competitor_html)

        industry_html_map = self._render_industry_section(industry_items)
        for key, value in industry_html_map.items():
            html = html.replace(f"{{{{{key}}}}}", value)

        return html

    def _html_labels(self) -> Dict[str, str]:
        if self.language == "zh":
            return {
                "LANGUAGE_SWITCHER_HTML": '<a href="/programmatic-news-weekly/en/">English</a>',
                "MAIN_HEADING": REPORT_NAME,
                "COMPETITOR_SECTION_TITLE": "一、竞品资讯",
                "COMPANY_COLUMN_TITLE": "公司",
                "CONTENT_COLUMN_TITLE": "内容",
                "INDUSTRY_SECTION_TITLE": "二、行业资讯",
                "FOOTER_TEXT": "本报告由自动化系统生成",
            }
        return {
            "LANGUAGE_SWITCHER_HTML": '<a href="/programmatic-news-weekly/">中文</a>',
            "MAIN_HEADING": EN_REPORT_NAME,
            "COMPETITOR_SECTION_TITLE": "Competitor News",
            "COMPANY_COLUMN_TITLE": "Company",
            "CONTENT_COLUMN_TITLE": "Coverage",
            "INDUSTRY_SECTION_TITLE": "Industry News",
            "FOOTER_TEXT": "Automatically generated",
        }

    def _render_competitor_section(self, items: Dict[str, List[ContentItem]]) -> str:
        rows = []
        link_label = "原文链接" if self.language == "zh" else "Source"

        for company, company_items in items.items():
            if not company_items:
                continue

            for item in company_items[:2]:
                row_html = f"""<tr>
  <td class="company">{company}</td>
  <td>
    <p class="item-title">{self._escape_html(item.title)}</p>
    <p class="item-summary">{self._escape_html(item.summary)}</p>
    <p class="item-meta">{item.date} · <a href="{item.url}" target="_blank" rel="noopener">{link_label}</a></p>
  </td>
</tr>"""
                rows.append(row_html)

        return "\n".join(rows) if rows else ""

    def _render_industry_section(self, items: Dict[str, List[ContentItem]]) -> Dict[str, str]:
        result = {}
        link_label = "原文链接" if self.language == "zh" else "Source"

        old_slots = ["INDUSTRY_PUBLISHER", "INDUSTRY_TECHNOLOGY", "INDUSTRY_PLATFORM", "INDUSTRY_AI", "INDUSTRY_OTHERS"]
        for slot_prefix in old_slots:
            result[f"{slot_prefix}_ITEMS_HTML"] = ""
            result[f"{slot_prefix}_HIDDEN_CLASS"] = "hidden"
            result[f"{slot_prefix}_EMPTY_HTML"] = ""

        for source_key, slot_prefix in [("AdExchanger", "ADEXCHANGER"), ("Search Engine Land", "SEL")]:
            source_items = items.get(source_key, [])
            if source_items:
                cards = []
                for item in source_items:
                    card_html = f"""<div class="industry-item">
  <p class="item-title">{self._escape_html(item.title)}</p>
  <p class="item-summary">{self._escape_html(item.summary)}</p>
  <p class="item-meta">{item.date} · <a href="{item.url}" target="_blank" rel="noopener">{link_label}</a></p>
</div>"""
                    cards.append(card_html)
                result[f"{slot_prefix}_ITEMS_HTML"] = "\n".join(cards)
                result[f"{slot_prefix}_HIDDEN_CLASS"] = ""
            else:
                result[f"{slot_prefix}_ITEMS_HTML"] = ""
                result[f"{slot_prefix}_HIDDEN_CLASS"] = "hidden"

        return result

    def _escape_html(self, text: str) -> str:
        if not text:
            return ""

        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        text = text.replace('"', "&quot;")
        text = text.replace("'", "&#x27;")
        return text

    def save(self, html_content: str, start_date: str, end_date: str) -> str:
        prefix = "weekly-report" if self.language == "zh" else "weekly-report-en"
        filepath = build_output_path(start_date, end_date, "html", prefix)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return filepath


class MarkdownRenderer:
    """Markdown 渲染器"""

    def __init__(self, language: str = "zh"):
        self.language = language

    def render(self, competitor_items: Dict[str, List[ContentItem]],
               industry_items: Dict[str, List[ContentItem]],
               start_date: str, end_date: str) -> str:
        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
        if self.language == "zh":
            lines = [
                f"# {build_report_title(start_date, end_date, 'zh')}",
                "",
                f"- 报告周期：{start_date} ~ {end_date}",
                f"- 生成时间：{generated_at}",
                "",
                "## 一、竞品资讯",
                "",
                self._render_competitor_section(competitor_items),
                "",
                "## 二、行业资讯",
                "",
                self._render_industry_section(industry_items),
                "",
                f"_本报告由自动化系统生成 · {generated_at}_",
                "",
            ]
        else:
            lines = [
                f"# {build_report_title(start_date, end_date, 'en')}",
                "",
                f"- Reporting period: {start_date} ~ {end_date}",
                f"- Generated at: {generated_at}",
                "",
                "## Competitor News",
                "",
                self._render_competitor_section(competitor_items),
                "",
                "## Industry News",
                "",
                self._render_industry_section(industry_items),
                "",
                f"_Automatically generated · {generated_at}_",
                "",
            ]
        return "\n".join(lines)

    def _render_competitor_section(self, items: Dict[str, List[ContentItem]]) -> str:
        sections = []

        for company, company_items in items.items():
            limited_items = company_items[:2]
            if not limited_items:
                continue

            sections.append(f"### {self._escape_markdown(company)}")
            sections.append("")

            for index, item in enumerate(limited_items, 1):
                sections.extend(self._render_item(item, index))

            sections.append("")

        return "\n".join(sections).strip() if sections else ("_暂无内容_" if self.language == "zh" else "_No content_")

    def _render_industry_section(self, items: Dict[str, List[ContentItem]]) -> str:
        sections = []

        for source_name in ["AdExchanger", "Search Engine Land"]:
            source_items = items.get(source_name, [])
            if not source_items:
                continue

            sections.append(f"### {self._escape_markdown(source_name)}")
            sections.append("")

            for index, item in enumerate(source_items, 1):
                sections.extend(self._render_item(item, index))

            sections.append("")

        return "\n".join(sections).strip() if sections else ("_暂无内容_" if self.language == "zh" else "_No content_")

    def _render_item(self, item: ContentItem, index: int) -> List[str]:
        title = self._escape_markdown(item.title)
        summary = self._escape_markdown(item.summary or ("无摘要" if self.language == "zh" else "No summary"))
        date = item.date or ("未知" if self.language == "zh" else "Unknown")
        url = item.url or ""

        if self.language == "zh":
            lines = [
                f"{index}. **{title}**",
                f"   - 摘要：{summary}",
                f"   - 日期：{date}",
            ]
        else:
            lines = [
                f"{index}. **{title}**",
                f"   - Summary: {summary}",
                f"   - Date: {date}",
            ]

        if url:
            lines.append(f"   - {'链接' if self.language == 'zh' else 'Link'}: {url}")

        return lines

    def _escape_markdown(self, text: Optional[str]) -> str:
        if not text:
            return ""

        cleaned = " ".join(str(text).split())
        for char in ["\\", "*", "_", "`"]:
            cleaned = cleaned.replace(char, f"\\{char}")
        return cleaned

    def save(self, markdown_content: str, start_date: str, end_date: str) -> str:
        prefix = "weekly-report" if self.language == "zh" else "weekly-report-en"
        filepath = build_output_path(start_date, end_date, "md", prefix)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        return filepath


def save_report_outputs(competitor_items: Dict[str, List[ContentItem]],
                        industry_items: Dict[str, List[ContentItem]],
                        start_date: str, end_date: str,
                        html_content: Optional[str] = None,
                        html_renderer: Optional[HTMLRenderer] = None,
                        markdown_renderer: Optional[MarkdownRenderer] = None) -> Dict[str, str]:
    """在同一步里保存 HTML 与 Markdown 两份报告"""
    html_renderer = html_renderer or HTMLRenderer()
    markdown_renderer = markdown_renderer or MarkdownRenderer()

    html_content = html_content or html_renderer.render(
        competitor_items,
        industry_items,
        start_date,
        end_date,
    )
    markdown_content = markdown_renderer.render(
        competitor_items,
        industry_items,
        start_date,
        end_date,
    )

    html_path = html_renderer.save(html_content, start_date, end_date)
    markdown_path = markdown_renderer.save(markdown_content, start_date, end_date)

    return {
        "html": html_content,
        "html_path": html_path,
        "markdown": markdown_content,
        "markdown_path": markdown_path,
    }


def save_bilingual_report_outputs(zh_competitor_items: Dict[str, List[ContentItem]],
                                  zh_industry_items: Dict[str, List[ContentItem]],
                                  en_competitor_items: Dict[str, List[ContentItem]],
                                  en_industry_items: Dict[str, List[ContentItem]],
                                  start_date: str, end_date: str) -> Dict[str, Dict[str, str]]:
    """保存中英文两套 HTML 与 Markdown 报告。"""
    zh_outputs = save_report_outputs(
        zh_competitor_items,
        zh_industry_items,
        start_date,
        end_date,
        html_renderer=HTMLRenderer(language="zh"),
        markdown_renderer=MarkdownRenderer(language="zh"),
    )
    en_outputs = save_report_outputs(
        en_competitor_items,
        en_industry_items,
        start_date,
        end_date,
        html_renderer=HTMLRenderer(language="en"),
        markdown_renderer=MarkdownRenderer(language="en"),
    )
    return {"zh": zh_outputs, "en": en_outputs}
