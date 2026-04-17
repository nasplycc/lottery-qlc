#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
七乐彩历史开奖数据更新脚本
- 从 500.com 获取历史开奖数据
- 保存到 data/qlc_history.csv
"""

import csv
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / 'data' / 'qlc_history.csv'
SOURCE_URL = 'https://datachart.500.com/qlc/history/newinc/history.php?start=03001&end=99999'
DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
ISSUE_RE = re.compile(r'^\d{5,7}$')
BALL_RE = re.compile(r'^\d{2}$')


def fetch_html():
    """获取网页内容"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://datachart.500.com/qlc/history/history.shtml',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }
    r = requests.get(SOURCE_URL, headers=headers, timeout=30)
    r.raise_for_status()
    r.encoding = 'gb2312'
    return r.text


def normalized_lines(html):
    """解析 HTML 并提取文本行"""
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text('\n').replace('\xa0', '')
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines


def parse_rows(lines):
    """解析开奖数据行"""
    rows = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # 期号匹配（5 位数字，如 26041）
        if not ISSUE_RE.fullmatch(line):
            i += 1
            continue
        
        issue = line
        
        # 期号后面是红球 + 特别号（可能连在一起如 '02 06 11 16 17 29 3012' 或分开）
        # 先找包含 7 个红球 + 特别号的行
        balls_line = None
        for j in range(i + 1, min(i + 5, len(lines))):
            candidate = lines[j]
            # 匹配格式：7 个两位数红球 + 2 位特别号（可能连在一起）
            # 如 '02 06 11 16 17 29 3012' 或 '02 03 10 11 12 24 25' + '07'
            parts = candidate.split()
            if len(parts) >= 1:
                # 检查是否包含 7 个红球
                first_part = parts[0]
                # 可能是 '02 06 11 16 17 29 3012' 格式（最后 4 位是 30+12）
                if len(first_part) > 20:  # 长字符串，红球和特别号连在一起
                    balls_line = candidate
                    break
                elif len(parts) >= 7:  # 分开的格式
                    balls_line = candidate
                    break
        
        if not balls_line:
            i += 1
            continue
        
        # 解析红球和特别号
        parts = balls_line.split()
        red_balls = []
        special = None
        
        if len(parts[0]) > 15:  # 连在一起格式：'02 06 11 16 17 29 3012'
            # 最后 4 位是 红球最后一位 + 特别号
            main_part = parts[0]
            # 提取前 6 个红球（每个 2 位）
            for k in range(6):
                red_balls.append(int(main_part[k*2:k*2+2]))
            # 最后 4 位：第 7 红球 + 特别号
            last_red = int(main_part[12:14])
            special = int(main_part[14:16])
            red_balls.append(last_red)
        elif len(parts) >= 8:  # 分开格式：7 红 + 特别号
            red_balls = [int(x) for x in parts[:7]]
            special = int(parts[7])
        elif len(parts) == 7:  # 只有 7 红，特别号在下一行
            red_balls = [int(x) for x in parts[:7]]
            # 特别号在下一行
            if i + 2 < len(lines) and BALL_RE.fullmatch(lines[i + 2]):
                special = int(lines[i + 2])
        
        if not red_balls or len(red_balls) != 7 or special is None:
            i += 1
            continue
        
        # 找开奖日期
        draw_date = None
        for j in range(i + 5, min(i + 15, len(lines))):
            if DATE_RE.fullmatch(lines[j]):
                draw_date = lines[j]
                i = j + 1
                break
        
        if not draw_date:
            i += 1
            continue
        
        # 排序红球
        reds = sorted(red_balls)
        
        rows.append({
            'draw_id': issue,
            'draw_date': draw_date,
            'red_1': reds[0],
            'red_2': reds[1],
            'red_3': reds[2],
            'red_4': reds[3],
            'red_5': reds[4],
            'red_6': reds[5],
            'red_7': reds[6],
            'special_1': special,
        })
    
    # 去重（后期号为准）
    unique = {}
    for row in rows:
        unique[row['draw_id']] = row
    
    return sorted(unique.values(), key=lambda x: x['draw_id'])


def save_csv(rows):
    """保存数据到 CSV"""
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        'draw_id', 'draw_date', 'draw_day',
        'red_1', 'red_2', 'red_3', 'red_4', 'red_5', 'red_6', 'red_7',
        'special_1'
    ]
    with open(DATA_PATH, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    print("🔄 开始更新七乐彩历史数据...")
    print(f"数据源：{SOURCE_URL}")
    
    try:
        html = fetch_html()
        print("✅ 网页获取成功")
    except Exception as e:
        print(f"❌ 网页获取失败：{e}")
        print("ℹ️  请检查网络连接或稍后重试")
        return
    
    lines = normalized_lines(html)
    print(f"📊 规范化文本行数：{len(lines)}")
    
    rows = parse_rows(lines)
    if not rows:
        print("❌ 未解析到七乐彩历史开奖数据")
        print("ℹ️  网页结构可能已变更，请检查数据源")
        return
    
    save_csv(rows)
    print(f"✅ 已写入 {len(rows)} 期历史数据 -> {DATA_PATH}")
    print(f"📌 首期：{rows[0]}")
    print(f"📌 最新一期：{rows[-1]}")


if __name__ == '__main__':
    main()
