from collections import defaultdict
from config import (
    WEIGHT_BASE_FREQ, WEIGHT_RECENT_FREQ, WEIGHT_MISS, RECENT_PERIODS,
)


def _base_frequency(records, main_keys, bonus_keys, main_range, bonus_range):
    """基础频率：每个号码在历史中的出现概率"""
    total = len(records)
    if total == 0:
        return {}, {}

    main_count = defaultdict(int)
    bonus_count = defaultdict(int)

    for r in records:
        for key in main_keys:
            main_count[r[key]] += 1
        for key in bonus_keys:
            bonus_count[r[key]] += 1

    main_freq = {n: main_count[n] / total for n in range(main_range[0], main_range[1] + 1)}
    bonus_freq = {n: bonus_count[n] / total for n in range(bonus_range[0], bonus_range[1] + 1)}
    return main_freq, bonus_freq


def _recent_weighted_frequency(records, main_keys, bonus_keys, main_range, bonus_range, periods):
    """近期加权频率：近期数据权重更高，线性衰减"""
    recent = records[-periods:] if len(records) >= periods else records
    n = len(recent)
    if n == 0:
        return {}, {}

    main_weighted = defaultdict(float)
    bonus_weighted = defaultdict(float)
    total_weight = 0

    for i, r in enumerate(recent):
        weight = i + 1  # 越近权重越大
        total_weight += weight
        for key in main_keys:
            main_weighted[r[key]] += weight
        for key in bonus_keys:
            bonus_weighted[r[key]] += weight

    main_freq = {num: main_weighted[num] / total_weight for num in range(main_range[0], main_range[1] + 1)}
    bonus_freq = {num: bonus_weighted[num] / total_weight for num in range(bonus_range[0], bonus_range[1] + 1)}
    return main_freq, bonus_freq


def _miss_probability(records, main_keys, bonus_keys, main_range, bonus_range):
    """遗漏回补概率：当前遗漏值 / 平均遗漏值"""
    main_miss = {}
    bonus_miss = {}

    for num in range(main_range[0], main_range[1] + 1):
        current_miss = 0
        intervals = []
        last_seen = -1
        for i, r in enumerate(records):
            found = any(r[key] == num for key in main_keys)
            if found:
                if last_seen >= 0:
                    intervals.append(i - last_seen)
                last_seen = i
                current_miss = 0
            else:
                current_miss += 1

        avg_interval = sum(intervals) / len(intervals) if intervals else len(records)
        main_miss[num] = current_miss / avg_interval if avg_interval > 0 else 0

    for num in range(bonus_range[0], bonus_range[1] + 1):
        current_miss = 0
        intervals = []
        last_seen = -1
        for i, r in enumerate(records):
            found = any(r[key] == num for key in bonus_keys)
            if found:
                if last_seen >= 0:
                    intervals.append(i - last_seen)
                last_seen = i
                current_miss = 0
            else:
                current_miss += 1

        avg_interval = sum(intervals) / len(intervals) if intervals else len(records)
        bonus_miss[num] = current_miss / avg_interval if avg_interval > 0 else 0

    return main_miss, bonus_miss


def _normalize(freq):
    """归一化使概率之和为 1"""
    total = sum(freq.values())
    if total == 0:
        return freq
    return {k: v / total for k, v in freq.items()}


def analyze(records, main_keys, bonus_keys, main_range, bonus_range):
    """
    综合概率分析，返回每个号码的主区/副区概率
    """
    base_main, base_bonus = _base_frequency(
        records, main_keys, bonus_keys, main_range, bonus_range
    )
    recent_main, recent_bonus = _recent_weighted_frequency(
        records, main_keys, bonus_keys, main_range, bonus_range, RECENT_PERIODS
    )
    miss_main, miss_bonus = _miss_probability(
        records, main_keys, bonus_keys, main_range, bonus_range
    )

    # 综合概率
    combined_main = {}
    for num in range(main_range[0], main_range[1] + 1):
        combined_main[num] = (
            WEIGHT_BASE_FREQ * base_main.get(num, 0)
            + WEIGHT_RECENT_FREQ * recent_main.get(num, 0)
            + WEIGHT_MISS * miss_main.get(num, 0)
        )

    combined_bonus = {}
    for num in range(bonus_range[0], bonus_range[1] + 1):
        combined_bonus[num] = (
            WEIGHT_BASE_FREQ * base_bonus.get(num, 0)
            + WEIGHT_RECENT_FREQ * recent_bonus.get(num, 0)
            + WEIGHT_MISS * miss_bonus.get(num, 0)
        )

    return _normalize(combined_main), _normalize(combined_bonus)
