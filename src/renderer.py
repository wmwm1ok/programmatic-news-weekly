"""
HTML 渲染模块
"""

import os
import re
from datetime import datetime
from typing import Dict, List

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
from fetchers.base import ContentItem
from config.settings import OUTPUT_CONFIG


class HTMLRenderer:
    """HTML 渲染器"""

    REPORT_COVER_URL = "https://wmwm1ok.github.io/programmatic-news-weekly/assets/programmatic-news-cover.jpg"
    
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
        
        # 填充日期
        html = html.replace("{{START_DATE}}", start_date)
        html = html.replace("{{END_DATE}}", end_date)
        html = html.replace("{{GENERATED_AT}}", datetime.now().strftime("%Y-%m-%d %H:%M"))
        report_title = f"程序化广告竞品及行业资讯 {start_date} ~ {end_date}"
        report_description = "程序化广告竞品及行业资讯汇总，涵盖 13 家竞品与重点行业动态。"
        html = html.replace("{{REPORT_TITLE}}", report_title)
        html = html.replace("{{REPORT_DESCRIPTION}}", report_description)
        html = html.replace("{{REPORT_COVER_URL}}", self.REPORT_COVER_URL)
        
        # 填充竞品资讯
        competitor_html = self._render_competitor_section(competitor_items)
        html = html.replace("{{COMPETITOR_SECTION_HTML}}", competitor_html)
        
        # 填充行业资讯
        industry_html_map = self._render_industry_section(industry_items)
        for key, value in industry_html_map.items():
            html = html.replace(f"{{{{{key}}}}}", value)
        
        return html
    
    def _render_competitor_section(self, items: Dict[str, List[ContentItem]]) -> str:
        """
        渲染竞品资讯区块
        :param items: {公司名称: 内容列表}
        :return: HTML 字符串
        """
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
        """
        渲染行业资讯区块
        :param items: {来源名称: 内容列表}
        :return: 插槽映射 {插槽名: HTML内容}
        """
        result = {}
        
        # 隐藏旧的模块（Publisher, Technology, Platform, AI, Others）
        old_slots = ["INDUSTRY_PUBLISHER", "INDUSTRY_TECHNOLOGY", "INDUSTRY_PLATFORM", "INDUSTRY_AI", "INDUSTRY_OTHERS"]
        for slot_prefix in old_slots:
            result[f"{slot_prefix}_ITEMS_HTML"] = ""
            result[f"{slot_prefix}_HIDDEN_CLASS"] = "hidden"
            result[f"{slot_prefix}_EMPTY_HTML"] = ""
        
        # 渲染 AdExchanger
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
        
        # 渲染 Search Engine Land
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
        """
        HTML 转义
        :param text: 原始文本
        :return: 转义后的文本
        """
        if not text:
            return ""
        
        # 转义特殊字符
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        text = text.replace('"', "&quot;")
        text = text.replace("'", "&#x27;")
        
        return text
    
    def save(self, html_content: str, start_date: str, end_date: str) -> str:
        """
        保存 HTML 文件
        :param html_content: HTML 内容
        :param start_date: 开始日期
        :param end_date: 结束日期
        :return: 文件路径
        """
        # 创建输出目录
        output_dir = OUTPUT_CONFIG["output_dir"]
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成文件名
        filename = f"weekly-report-{start_date}_{end_date}.html"
        filepath = os.path.join(output_dir, filename)
        
        # 保存文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return filepath
