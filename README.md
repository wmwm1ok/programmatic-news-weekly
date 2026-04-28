# 周报自动化系统

自动化竞品周报系统，自动抓取指定来源在"近 7 日窗口"内发布的内容，同步生成固定模板的 HTML 页面和机器可读的 Markdown 周报，并将 HTML 作为邮件正文发送至指定收件人。

## 功能特性

- **竞品资讯抓取**：支持 13 家公司的公告/新闻/博客
- **行业资讯抓取**：支持 5 个子模块（Publisher/Technology/Platform/AI/Others）
- **智能摘要生成**：使用 Claude Sonnet 4 生成 80-100 字中文摘要
- **内容验证**：链接可用性、日期窗口、摘要长度、摘要质量验证
- **双格式输出**：固定模板 HTML 页面 + 机器可读 Markdown 周报
- **邮件发送**：自动发送 HTML 周报至指定收件人

## 项目结构

```
weekly-report-automation/
├── config/
│   └── settings.py          # 配置文件
├── src/
│   ├── fetchers/
│   │   ├── __init__.py
│   │   ├── base.py           # 抓取器基类
│   │   ├── competitor_fetcher.py  # 竞品抓取器（13家公司）
│   │   └── industry_fetcher.py    # 行业抓取器（5个子模块）
│   ├── summarizer.py         # Claude 摘要生成
│   ├── validator.py          # 内容验证
│   ├── renderer.py           # HTML / Markdown 渲染
│   ├── mailer.py             # 邮件发送
│   └── main.py               # 主程序入口
├── templates/
│   └── report_template.html  # HTML 模板
├── output/                   # 输出目录
├── requirements.txt          # 依赖列表
└── README.md                 # 说明文档
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置环境变量

```bash
# Claude API 配置
export CLAUDE_API_KEY="your-api-key"
export CLAUDE_ENDPOINT="http://osagw.simeji.me/gbu/rest/v1/ai_chat/claude_service"
export CLAUDE_HOST="gbu.jp02-a30-apisix-online.baidu-int.com"
export CLAUDE_MODEL="us.anthropic.claude-sonnet-4-20250514-v1:0"

# 邮件配置（可选，用于发送邮件）
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="587"
export EMAIL_USERNAME="your-email@gmail.com"
export EMAIL_PASSWORD="your-password"
export EMAIL_FROM="your-email@gmail.com"
export EMAIL_TO="wangmeng42@baidu.com"
```

## 使用方法

### 正常运行

```bash
cd weekly-report-automation
python src/main.py
```

### 指定运行日期

```bash
python src/main.py --date 2026-02-12
```

### 测试模式（不调用真实 API）

```bash
python src/main.py --test
```

## 输出文件

- HTML 文件：`output/weekly-report-YYYY-MM-DD_YYYY-MM-DD.html`
- Markdown 文件：`output/weekly-report-YYYY-MM-DD_YYYY-MM-DD.md`
- GitHub Pages 会同步发布最新 Markdown：`/latest.md`

## 数据来源

### 竞品资讯（13 家公司）

| 公司 | URL |
|------|-----|
| TTD | https://www.thetradedesk.com/press-room |
| Criteo | https://criteo.investorroom.com/releases |
| Taboola | https://www.taboola.com/press-releases/ |
| Teads | https://www.teads.com/press-releases/ |
| AppLovin | https://www.applovin.com/en/newsroom |
| mobvista | https://www.mobvista.com/en/community/blog |
| Moloco | https://www.moloco.com/press-releases |
| BIGO Ads | https://www.bigoads.com/resources/blog |
| Unity | https://unity.com/news |
| Viant Technology | https://www.viantinc.com/company/news/press-releases/ |
| Zeta Global | https://investors.zetaglobal.com/news/default.aspx |
| PubMatic | https://investors.pubmatic.com/news-events/news-releases/ |
| Magnite | https://investor.magnite.com/press-releases |

### 行业资讯（5 个子模块）

| 子模块 | URL |
|--------|-----|
| Publisher | https://www.adexchanger.com/publishers/ |
| Technology | https://www.adexchanger.com/technology/ |
| Platform | https://www.adexchanger.com/platforms/ |
| Artificial Intelligence | https://www.adexchanger.com/artificial-intelligence/ |
| Others | https://searchengineland.com/latest-posts |

## 校验规则

- 链接可用性：HTTP 状态码 < 400
- 日期窗口：发布日期在 [run_date - 7 days, run_date] 范围内
- 日期格式：YYYY-MM-DD
- 摘要长度：80-100 中文字符
- 摘要质量：必须包含关键指标/事实
- PR 区块：必须为空

## 失败处理

若生成失败或任一校验不通过：
- 不输出 HTML 文件
- 不发送邮件
- 返回失败原因清单（包含模块、标题、原因、URL）

## 注意事项

1. 请确保已设置 `CLAUDE_API_KEY` 环境变量
2. 如需发送邮件，请配置邮件相关环境变量
3. 首次运行建议先使用 `--test` 模式测试
4. 抓取过程可能需要几分钟，请耐心等待
