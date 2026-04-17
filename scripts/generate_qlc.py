#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
七乐彩选号生成器
- 基于历史数据和规则生成推荐号码
- 支持单式、复式选号
- 输出 JSON 和 Markdown 格式
"""

import json
import random
import math
from pathlib import Path
from datetime import datetime
import csv

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / 'config.json'
DATA_PATH = ROOT / 'data' / 'qlc_history.csv'
OUTPUTS_DIR = ROOT / 'outputs'


def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_history():
    """加载历史开奖数据"""
    if not DATA_PATH.exists():
        return []
    
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def analyze_frequency(history, limit=30):
    """分析近期号码频率"""
    if not history:
        return {}, {}
    
    red_freq = {i: 0 for i in range(1, 31)}
    special_freq = {i: 0 for i in range(1, 31)}  # 七乐彩特别号范围 01-30
    
    recent = history[-limit:] if len(history) >= limit else history
    
    for row in recent:
        for i in range(1, 8):
            red_num = int(row[f'red_{i}'])
            red_freq[red_num] += 1
        
        special = int(row['special_1'])
        special_freq[special] += 1
    
    return red_freq, special_freq


def analyze_hot_cold(freq, top_n=7):
    """分析热号和冷号"""
    sorted_nums = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    hot = [num for num, count in sorted_nums[:top_n]]
    cold = [num for num, count in sorted_nums[-top_n:]]
    return hot, cold


def check_sum(red_nums, min_sum, max_sum):
    """检查和值是否在范围内"""
    total = sum(red_nums)
    return min_sum <= total <= max_sum


def check_odd_even(red_nums, allowed_ratios):
    """检查奇偶比"""
    odd_count = sum(1 for n in red_nums if n % 2 == 1)
    even_count = len(red_nums) - odd_count
    ratio = f"{odd_count}:{even_count}"
    return ratio in allowed_ratios


def check_zones(red_nums, zones, allowed_ratios):
    """检查分区比"""
    zone_counts = [0, 0, 0]
    for num in red_nums:
        for i, (start, end) in enumerate(zones):
            if start <= num <= end:
                zone_counts[i] += 1
                break
    
    ratio = ':'.join(map(str, zone_counts))
    return ratio in allowed_ratios


def check_consecutive(red_nums, max_consecutive):
    """检查连号数量"""
    sorted_nums = sorted(red_nums)
    consecutive_count = 0
    for i in range(len(sorted_nums) - 1):
        if sorted_nums[i + 1] - sorted_nums[i] == 1:
            consecutive_count += 1
    return consecutive_count <= max_consecutive


def generate_single_pick(config, history, hot_reds, cold_reds, hot_special, cold_special):
    """生成一注单式号码"""
    rules = config['selection_rules']
    max_attempts = 1000
    
    # 无历史数据时使用纯随机策略
    use_random = not hot_reds or not cold_reds or not hot_special or not cold_special
    
    for _ in range(max_attempts):
        # 混合策略：热号 + 冷号 + 随机
        pick_reds = set()
        
        if use_random:
            # 纯随机生成
            pick_reds = set(random.sample(range(1, 31), 7))
        else:
            # 从热号中选 3-4 个
            hot_pick = random.sample(hot_reds, random.randint(3, 4))
            pick_reds.update(hot_pick)
            
            # 从冷号中选 1-2 个
            cold_pick = random.sample(cold_reds, random.randint(1, 2))
            pick_reds.update(cold_pick)
            
            # 剩余随机
            while len(pick_reds) < 7:
                num = random.randint(1, 30)
                if num not in pick_reds:
                    pick_reds.add(num)
        
        red_nums = sorted(list(pick_reds))[:7]
        
        # 验证规则
        if not check_sum(red_nums, rules['min_sum'], rules['max_sum']):
            continue
        if not check_odd_even(red_nums, rules['odd_even_ratios']):
            continue
        if not check_zones(red_nums, rules['zones'], rules['zone_ratios']):
            continue
        if not check_consecutive(red_nums, rules['consecutive_max']):
            continue
        
        # 特别号：热号优先
        if use_random:
            special = random.randint(1, 16)
        else:
            special = random.choice(hot_special) if random.random() < 0.7 else random.choice(cold_special)
        
        return {
            'reds': red_nums,
            'special': special
        }
    
    # 如果所有尝试都失败，返回一个基本合规的
    red_nums = sorted(random.sample(range(1, 31), 7))
    special = random.randint(1, 16)
    return {'reds': red_nums, 'special': special}


def generate_picks(config, history, count=5):
    """生成多注号码"""
    red_freq, special_freq = analyze_frequency(history)
    hot_reds, cold_reds = analyze_hot_cold(red_freq)
    hot_special, cold_special = analyze_hot_cold(special_freq, top_n=5)
    
    picks = []
    for i in range(count):
        pick = generate_single_pick(config, history, hot_reds, cold_reds, hot_special, cold_special)
        picks.append({
            'type': 'single',
            'reds': pick['reds'],
            'special': pick['special'],
            'cost': 2
        })
    
    return picks


def generate_combo_pick(config, history, red_count=8, special_count=1):
    """生成复式票"""
    red_freq, special_freq = analyze_frequency(history)
    hot_reds, cold_reds = analyze_hot_cold(red_freq, top_n=red_count + 2)
    hot_special, cold_special = analyze_hot_cold(special_freq, top_n=special_count + 1)
    
    # 无历史数据时使用纯随机策略
    use_random = not hot_reds or not cold_reds or not hot_special or not cold_special
    
    # 选红球
    red_pick = set()
    if use_random:
        red_pick = set(random.sample(range(1, 31), red_count))
    else:
        red_pick.update(random.sample(hot_reds, min(red_count - 2, len(hot_reds))))
        red_pick.update(random.sample(cold_reds, min(2, len(cold_reds))))
        while len(red_pick) < red_count:
            num = random.randint(1, 30)
            if num not in red_pick:
                red_pick.add(num)
    
    # 选特别号
    if use_random:
        special_pick = random.sample(range(1, 17), special_count)
    else:
        special_pick = random.sample(hot_special + cold_special, special_count)
    
    # 计算注数和成本
    from math import comb
    combinations = comb(red_count, 7) * special_count
    cost = combinations * 2
    
    return {
        'type': f'{red_count}+{special_count}',
        'reds': sorted(list(red_pick)),
        'special': special_pick,
        'combinations': combinations,
        'cost': cost
    }


def save_picks(picks, combo_pick, config):
    """保存选号结果"""
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    
    result = {
        'generated_at': datetime.now().isoformat(),
        'lottery': '七乐彩',
        'next_draw_days': config['draw_days'],
        'picks': picks,
        'combo_pick': combo_pick
    }
    
    # JSON 输出
    json_path = OUTPUTS_DIR / f'qlc-picks-{timestamp}.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    # Markdown 输出
    md_path = OUTPUTS_DIR / f'qlc-picks-{timestamp}.md'
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# 七乐彩选号推荐\n\n")
        f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write(f"**开奖日期**: 周一、三、五 21:15\n\n")
        f.write("---\n\n")
        
        f.write("## 📋 单式推荐（5 注）\n\n")
        for i, pick in enumerate(picks, 1):
            reds_str = ' '.join(f"{n:02d}" for n in pick['reds'])
            f.write(f"**推荐{i}**: {reds_str} + 特 {pick['special']:02d}  (2 元)\n\n")
        
        f.write("---\n\n")
        f.write("## 🎯 复式推荐\n\n")
        reds_str = ' '.join(f"{n:02d}" for n in combo_pick['reds'])
        special_str = ' '.join(f"{n:02d}" for n in combo_pick['special'])
        f.write(f"**{combo_pick['type']}**: {reds_str} + 特 {special_str}\n\n")
        f.write(f"- 注数：{combo_pick['combinations']} 注\n")
        f.write(f"- 成本：{combo_pick['cost']} 元\n\n")
    
    return json_path, md_path


def main():
    print("🎰 七乐彩选号生成器")
    print("=" * 40)
    
    config = load_config()
    history = load_history()
    
    print(f"📊 加载历史数据：{len(history)} 期")
    
    # 生成单式
    picks = generate_picks(config, history, count=5)
    print(f"✅ 生成 {len(picks)} 注单式推荐")
    
    # 生成复式（8+1）
    combo_pick = generate_combo_pick(config, history, red_count=8, special_count=1)
    print(f"✅ 生成 1 注 {combo_pick['type']} 复式推荐 ({combo_pick['cost']} 元)")
    
    # 保存
    json_path, md_path = save_picks(picks, combo_pick, config)
    print(f"📁 JSON: {json_path}")
    print(f"📁 Markdown: {md_path}")
    
    # 输出摘要
    print("\n" + "=" * 40)
    print("📋 选号摘要:")
    for i, pick in enumerate(picks, 1):
        reds_str = ' '.join(f"{n:02d}" for n in pick['reds'])
        print(f"  推荐{i}: {reds_str} + 特 {pick['special']:02d}")
    
    reds_str = ' '.join(f"{n:02d}" for n in combo_pick['reds'])
    special_str = ' '.join(f"{n:02d}" for n in combo_pick['special'])
    print(f"\n  复式 ({combo_pick['type']}): {reds_str} + 特 {special_str}")
    print(f"  成本：{combo_pick['cost']} 元")


if __name__ == '__main__':
    main()
