#!/usr/bin/env python3
"""
抓取 TopOn - 用于 topon-only 分支
"""
import json
import sys
import os
sys.path.insert(0, 'src')

from datetime import datetime, timedelta
from fetchers.stealth_fetcher import StealthFetcher

window_end = datetime.now()
window_start = window_end - timedelta(days=7)

print("="*70)
print("抓取 TopOn")
print(f"时间窗口: {window_start.date()} ~ {window_end.date()}")
print("="*70)

stealth = StealthFetcher()
items = stealth.fetch_company("TopOn", window_start, window_end)
stealth.close()

result = {
    'company': 'TopOn',
    'items': [{'title': i.title, 'summary': i.summary, 'date': i.date, 'url': i.url, 'source': i.source} for i in items],
    'count': len(items)
}

os.makedirs('output', exist_ok=True)
output_file = 'output/topon_result.json'
with open(output_file, 'w') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"\n✅ 完成: {len(items)} 条")
print(f"保存到: {output_file}")
