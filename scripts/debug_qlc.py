#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
七乐彩历史开奖数据更新脚本（调试版）
- 先输出原始数据格式，用于分析
"""

import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

SOURCE_URL = 'https://datachart.500.com/qlc/history/newinc/history.php?start=03001&end=99999'


def fetch_html():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://datachart.500.com/qlc/history/history.shtml',
    }
    r = requests.get(SOURCE_URL, headers=headers, timeout=30)
    r.raise_for_status()
    r.encoding = 'gb2312'
    return r.text


def main():
    print("🔍 获取七乐彩数据页面...")
    html = fetch_html()
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # 查找表格
    tables = soup.find_all('table')
    print(f"找到 {len(tables)} 个表格")
    
    # 找包含开奖数据的表格（通常有 class="table" 或 id="tdata"）
    for i, table in enumerate(tables):
        rows = table.find_all('tr')
        if len(rows) > 10:  # 数据表格通常有很多行
            print(f"\n表格 {i}: {len(rows)} 行")
            
            # 输出前 5 行看看格式
            for j, row in enumerate(rows[:5]):
                cells = row.find_all('td')
                if cells:
                    cell_texts = [c.get_text(strip=True) for c in cells]
                    print(f"  行 {j}: {cell_texts[:15]}")  # 只显示前 15 列
            
            # 尝试解析这个表格
            print(f"\n  尝试解析表格 {i}...")
            break
    
    # 也输出一些原始文本
    text = soup.get_text('\n')
    lines = [line.strip() for line in text.splitlines() if line.strip() and len(line.strip()) < 50]
    print(f"\n前 100 个短文本行:")
    for line in lines[:100]:
        print(f"  '{line}'")


if __name__ == '__main__':
    main()
