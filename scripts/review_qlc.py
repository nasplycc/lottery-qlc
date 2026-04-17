#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
七乐彩开奖后复盘脚本
- 更新历史开奖数据
- 读取最新一期开奖结果
- 对比当期选号结果
- 输出命中情况与规则复盘建议
"""

import csv
import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / 'data' / 'qlc_history.csv'
OUTPUTS_DIR = ROOT / 'outputs'


def load_latest_draw():
    """加载最新开奖结果"""
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    
    if not rows:
        return None
    
    row = rows[-1]
    reds = sorted([int(row[f'red_{i}']) for i in range(1, 8)])
    special = int(row['special_1'])
    
    return {
        'draw_id': row['draw_id'],
        'draw_date': row['draw_date'],
        'draw_day': row['draw_day'],
        'reds': reds,
        'special': special
    }


def load_latest_picks():
    """加载最新选号结果"""
    files = sorted(OUTPUTS_DIR.glob('qlc-picks-*.json'))
    if not files:
        return None, None
    
    target = files[-1]
    with open(target, 'r', encoding='utf-8') as f:
        return json.load(f), target


def calculate_prize(red_hits, special_hit, config):
    """计算中奖金额"""
    prize_rules = config['prize_rules']
    default_prizes = config['default_prize_amounts']
    
    # 七乐彩中奖规则
    if red_hits == 7 and special_hit:
        return default_prizes['tier_2']  # 二等奖
    elif red_hits == 7:
        return default_prizes['tier_1']  # 一等奖
    elif red_hits == 6 and special_hit:
        return default_prizes['tier_3']  # 三等奖
    elif red_hits == 6 or (red_hits == 5 and special_hit):
        return default_prizes['tier_4']  # 四等奖
    elif red_hits == 5 or (red_hits == 4 and special_hit):
        return default_prizes['tier_5']  # 五等奖
    elif red_hits == 4 or (red_hits == 3 and special_hit):
        return default_prizes['tier_6']  # 六等奖
    elif red_hits == 3 or (red_hits == 2 and special_hit):
        return default_prizes['tier_7']  # 七等奖
    else:
        return 0


def compare_single_ticket(ticket, actual_reds, actual_special, config):
    """对比单式票"""
    red_hits = sorted(set(ticket['reds']) & set(actual_reds))
    special_hit = ticket.get('special') == actual_special
    
    prize = calculate_prize(len(red_hits), special_hit, config)
    
    return {
        'type': ticket.get('type', 'single'),
        'red_hits': len(red_hits),
        'hit_red_numbers': red_hits,
        'special_hit': special_hit,
        'prize': prize
    }


def compare_combo_ticket(ticket, actual_reds, actual_special, config):
    """对比复式票（简化计算）"""
    red_hits = sorted(set(ticket['reds']) & set(actual_reds))
    special_hit = actual_special in ticket.get('special', [])
    
    # 复式票中奖计算较复杂，这里简化处理
    # 实际应根据组合数计算各奖级注数
    base_prize = calculate_prize(len(red_hits), special_hit, config)
    
    # 如果中了特别号，奖金会翻倍（简化估算）
    estimated_prize = base_prize * len(ticket['special']) if special_hit else base_prize
    
    return {
        'type': ticket.get('type', 'combo'),
        'red_hits': len(red_hits),
        'hit_red_numbers': red_hits,
        'special_hit': special_hit,
        'estimated_prize': estimated_prize,
        'cost': ticket.get('cost', 0)
    }


def analyze_draw_pattern(draw):
    """分析开奖号码形态"""
    reds = draw['reds']
    
    # 奇偶比
    odd_count = sum(1 for n in reds if n % 2 == 1)
    even_count = len(reds) - odd_count
    
    # 分区比
    zones = [[1, 10], [11, 20], [21, 30]]
    zone_counts = [0, 0, 0]
    for num in reds:
        for i, (start, end) in enumerate(zones):
            if start <= num <= end:
                zone_counts[i] += 1
    
    # 连号
    consecutive = []
    for i in range(len(reds) - 1):
        if reds[i + 1] - reds[i] == 1:
            consecutive.append((reds[i], reds[i + 1]))
    
    # 和值
    sum_value = sum(reds)
    
    return {
        'odd_even': f"{odd_count}:{even_count}",
        'zones': zone_counts,
        'zone_ratio': ':'.join(map(str, zone_counts)),
        'consecutive': consecutive,
        'sum': sum_value
    }


def main():
    print("📣 七乐彩开奖复盘")
    print("=" * 40)
    
    # 加载配置
    config_path = ROOT / 'config.json'
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 加载开奖结果
    draw = load_latest_draw()
    if not draw:
        print("❌ 无开奖数据，请先更新历史数据")
        return
    
    print(f"\n📌 开奖期号：{draw['draw_id']} 期")
    print(f"📅 开奖日期：{draw['draw_date']} ({draw['draw_day']})")
    
    reds_str = ' '.join(f"{n:02d}" for n in draw['reds'])
    print(f"🎯 开奖号码：{reds_str} + 特 {draw['special']:02d}")
    
    # 形态分析
    pattern = analyze_draw_pattern(draw)
    print(f"形态：奇偶 {pattern['odd_even']}｜分区 {pattern['zone_ratio']}｜和值 {pattern['sum']}")
    if pattern['consecutive']:
        consec_str = ', '.join(f"{a}-{b}" for a, b in pattern['consecutive'])
        print(f"连号：{consec_str}")
    else:
        print("连号：无")
    
    # 加载选号结果
    picks_data, picks_file = load_latest_picks()
    if not picks_data:
        print("\n⚠️  无选号记录")
        return
    
    print(f"\n选号文件：{picks_file.name}")
    print("\n🎯 本期命中情况：")
    
    total_prize = 0
    best_performance = None
    best_hits = 0
    
    # 对比单式
    for i, ticket in enumerate(picks_data.get('picks', []), 1):
        result = compare_single_ticket(ticket, draw['reds'], draw['special'], config)
        total_prize += result['prize']
        
        hit_desc = f"{result['red_hits']}红"
        if result['special_hit']:
            hit_desc += " + 特"
        
        prize_str = f"{result['prize']}元" if result['prize'] > 0 else "未中奖"
        print(f"  推荐{i}: {hit_desc} → {prize_str}")
        
        if result['red_hits'] > best_hits:
            best_hits = result['red_hits']
            best_performance = f"推荐{i}"
    
    # 对比复式
    combo = picks_data.get('combo_pick')
    if combo:
        result = compare_combo_ticket(combo, draw['reds'], draw['special'], config)
        hit_desc = f"{result['red_hits']}红"
        if result['special_hit']:
            hit_desc += " + 特"
        
        prize_str = f"≈{result['estimated_prize']}元" if result['estimated_prize'] > 0 else "未中奖"
        print(f"  复式 ({combo['type']}): {hit_desc} → {prize_str} (成本{result['cost']}元)")
        
        if result['red_hits'] > best_hits:
            best_performance = f"复式 ({combo['type']})"
    
    print(f"\n本期合计奖金：{total_prize}元")
    
    if best_performance:
        print(f"本期最好表现：{best_performance}，{best_hits}红")
    
    # 规则复盘建议
    print("\n🧪 规则净化建议：")
    if 70 <= pattern['sum'] <= 160:
        print("  ✓ 和值处于常见区间，现有和值约束可继续保留。")
    if not pattern['consecutive']:
        print("  ✓ 本期无连号，连号规则维持中性即可。")
    if all(1 <= z <= 4 for z in pattern['zones']):
        print("  ✓ 分区形态正常，主流分区规则有效。")
    
    print("\n结论：继续做纪律化复盘，优化规则，但不做'必中'幻想。")


if __name__ == '__main__':
    main()
