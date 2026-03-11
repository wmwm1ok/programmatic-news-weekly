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
REPORT_COVER_URL = "https://wmwm1ok.github.io/programmatic-news-weekly/assets/programmatic-news-cover.jpg"


def build_report_title(start_date: str, end_date: str) -> str:
    """构建带日期的报告标题"""
    return f"{REPORT_NAME} {start_date} ~ {end_date}"


def ensure_output_dir() -> str:
    """确保输出目录存在"""
    output_dir = OUTPUT_CONFIG["output_dir"]
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def build_output_path(start_date: str, end_date: str, extension: str) -> str:
    """生成输出文件路径"""
    output_dir = ensure_output_dir()
    filename = f"weekly-report-{start_date}_{end_date}.{extension}"
    return os.path.join(output_dir, filename)


class HTMLRenderer:
    """HTML 渲染器"""

    def __init__(self, template_path: str = None):
        self.template_path = template_path or os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "templates",
            "report_template.html"
        )
        self.template = self._load_template()

    def _load_template(self) -> str:
        """加载 HTML 模板"""
        with open(self.template_path, 'r', encoding='utf-8') as f:
            return f.read()

    def render(self, competitor_items: Dict[str, List[ContentItem]],
               industry_items: Dict[str, List[ContentItem]],
               start_date: str, end_date: str) -> str:
        """
        渲染 HTML 报告
        :param competitor_items: 竞品资讯 {公司名称: 内容列表}
        :param industry_items: 行业资讯 {子模块名称: 内容列表}
        :param start_date: 开始日期 (YYYY-MM-DD)
        :param end_date: 结束日期 (YYYY-MM-DD)
        :return: HTML 内容
        """
        html = self.template

        html = html.replace("{{START_DATE}}", start_date)
        html = html.replace("{{END_DATE}}", end_date)
        html = html.replace("{{GENERATED_AT}}", datetime.now().strftime("%Y-%m-%d %H:%M"))
        html = html.replace("{{REPORT_TITLE}}", build_report_title(start_date, end_date))
        html = html.replace("{{REPORT_DESCRIPTION}}", REPORT_DESCRIPTION)
        html = html.replace("{{REPORT_COVER_URL}}", REPORT_COVER_URL)

        competitor_html = self._render_competitor_section(competitor_items)
        html = html.replace("{{COMPETITOR_SECTION_HTML}}", competitor_html)

        industry_html_map = self._render_industry_section(industry_items)
        for key, value in industry_html_map.items():
            html = html.replace(f"{{{{{key}}}}}", value)

        return html

    def _render_competitor_section(self, items: Dict[str, List[ContentItem]]) -> str:
        """渲染竞品资讯区块"""
        rows = []

        for company, company_items in items.items():
            if not company_items:
                continue

            for item in company_items[:2]:
                row_html = f"""<tr>
  <td class="company">{company}</td>
  <td>
    <p class="item-title">{self._escape_html(item.title)}</p>
    <p class="item-summary">{self._escape_html(item.summary)}</p>
    <p class="item-meta">{item.date} · <a href="{item.url}" target="_blank" rel="noopener">原文链接</a></p>
  </td>
</tr>"""
                rows.append(row_html)

        if not rows:
            return ""

        return "\n".join(rows)

    def _render_industry_section(self, items: Dict[str, List[ContentItem]]) -> Dict[str, str]:
        """渲染行业资讯区块"""
        result = {}

        old_slots = ["INDUSTRY_PUBLISHER", "INDUSTRY_TECHNOLOGY", "INDUSTRY_PLATFORM", "INDUSTRY_AI", "INDUSTRY_OTHERS"]
        for slot_prefix in old_slots:
            result[f"{slot_prefix}_ITEMS_HTML"] = ""
            result[f"{slot_prefix}_HIDDEN_CLASS"] = "hidden"
            result[f"{slot_prefix}_EMPTY_HTML"] = ""

        adex_items = items.get("AdExchanger", [])
        if adex_items:
            cards = []
            for item in adex_items:
                card_html = f"""<div class="industry-item">
  <p class="item-title">{self._escape_html(item.title)}</p>
  <p class="item-summary">{self._escape_html(item.summary)}</p>
  <p class="item-meta">{item.date} · <a href="{item.url}" target="_blank" rel="noopener">原文链接</a></p>
</div>"""
                cards.append(card_html)
            result["ADEXCHANGER_ITEMS_HTML"] = "\n".join(cards)
            result["ADEXCHANGER_HIDDEN_CLASS"] = ""
        else:
            result["ADEXCHANGER_ITEMS_HTML"] = ""
            result["ADEXCHANGER_HIDDEN_CLASS"] = "hidden"

        sel_items = items.get("Search Engine Land", [])
        if sel_items:
            cards = []
            for item in sel_items:
                card_html = f"""<div class="industry-item">
  <p class="item-title">{self._escape_html(item.title)}</p>
  <p class="item-summary">{self._escape_html(item.summary)}</p>
  <p class="item-meta">{item.date} · <a href="{item.url}" target="_blank" rel="noopener">原文链接</a></p>
</div>"""
                cards.append(card_html)
            result["SEL_ITEMS_HTML"] = "\n".join(cards)
            result["SEL_HIDDEN_CLASS"] = ""
        else:
            result["SEL_ITEMS_HTML"] = ""
            result["SEL_HIDDEN_CLASS"] = "hidden"

        return result

    def _escape_html(self, text: str) -> str:
        """HTML 转义"""
        if not text:
            return ""

        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        text = text.replace('"', "&quot;")
        text = text.replace("'", "&#x27;")
        return text

    def save(self, html_content: str, start_date: str, end_date: str) -> str:
        """保存 HTML 文件"""
        filepath = build_output_path(start_date, end_date, "html")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return filepath


class MarkdownRenderer:
    """Markdown 渲染器"""

    def render(self, competitor_items: Dict[str, List[ContentItem]],
               industry_items: Dict[str, List[ContentItem]],
               start_date: str, end_date: str) -> str:
        """
        渲染 Markdown 报告
        :param competitor_items: 竞品资讯 {公司名称: 内容列表}
        :param industry_items: 行业资讯 {来源名称: 内容列表}
        :param start_date: 开始日期 (YYYY-MM-DD)
        :param end_date: 结束日期 (YYYY-MM-DD)
        :return: Markdown 内容
        """
        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
        lines = [
            f"# {build_report_title(start_date, end_date)}",
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
        return "\n".join(lines)

    def _render_competitor_section(self, items: Dict[str, List[ContentItem]]) -> str:
        """渲染竞品资讯区块"""
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

        return "\n".join(sections).strip() if sections else "_暂无内容_"

    def _render_industry_section(self, items: Dict[str, List[ContentItem]]) -> str:
        """渲染行业资讯区块"""
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

        return "\n".join(sections).strip() if sections else "_暂无内容_"

    def _render_item(self, item: ContentItem, index: int) -> List[str]:
        """渲染单条 Markdown 内容"""
        title = self._escape_markdown(item.title)
        summary = self._escape_markdown(item.summary or "无摘要")
        date = item.date or "未知"
        url = item.url or ""

        lines = [
            f"{index}. **{title}**",
            f"   - 摘要：{summary}",
            f"   - 日期：{date}",
        ]

        if url:
            lines.append(f"   - 链接：{url}")

        return lines

    def _escape_markdown(self, text: Optional[str]) -> str:
        """转义 Markdown 特殊字符"""
        if not text:
            return ""

        cleaned = " ".join(str(text).split())
        for char in ["\\", "*", "_", "`"]:
            cleaned = cleaned.replace(char, f"\\{char}")
        return cleaned

    def save(self, markdown_content: str, start_date: str, end_date: str) -> str:
        """保存 Markdown 文件"""
        filepath = build_output_path(start_date, end_date, "md")
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
