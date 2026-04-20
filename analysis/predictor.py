from itertools import combinations
from collections import defaultdict
from functools import reduce
import operator

from config import (
    PREDICTION_SPAN, COMBO_PENALTY_WEIGHTS, CANDIDATE_POOL_SIZE,
)
from analysis.analyzer import analyze
from database.db import get_all_ssq, get_all_dlt


def build_combination_freq(records, keys, max_k):
    """预计算历史中所有 2..max_k 元子组合的出现频率"""
    freq = {k: defaultdict(int) for k in range(2, max_k + 1)}
    for record in records:
        numbers = tuple(sorted(record[key] for key in keys))
        for k in range(2, min(max_k, len(numbers)) + 1):
            for combo in combinations(numbers, k):
                freq[k][combo] += 1
    return freq


def calc_penalty(candidate_numbers, freq, total_draws):
    """计算候选号码集合的子组合频率惩罚分"""
    sorted_nums = tuple(sorted(candidate_numbers))
    penalty = 0.0
    for k in range(2, len(sorted_nums) + 1):
        weight = COMBO_PENALTY_WEIGHTS.get(k, k)
        for combo in combinations(sorted_nums, k):
            f = freq[k].get(combo, 0)
            if total_draws > 0:
                penalty += weight * (f / total_draws)
    return penalty


def greedy_select(prob, freq, total_draws, count, exclude=None):
    """
    贪心选号：综合考虑个体概率和子组合惩罚。
    exclude: 需要排除的号码集合（已在前几组中选用）
    """
    exclude = exclude or set()
    pool = [
        (n, p) for n, p in sorted(prob.items(), key=lambda x: x[1], reverse=True)
        if n not in exclude
    ][:CANDIDATE_POOL_SIZE]
    selected = []
    remaining = list(pool)

    for _ in range(count):
        best_score = -float("inf")
        best_idx = 0

        for i, (num, p) in enumerate(remaining):
            test_set = [n for n, _ in selected] + [num]
            penalty = calc_penalty(test_set, freq, total_draws)
            score = p - penalty
            if score > best_score:
                best_score = score
                best_idx = i

        selected.append(remaining[best_idx])
        remaining.pop(best_idx)

    return selected


def predict_ssq(combo_count=5):
    """双色球预测：生成 combo_count 组推荐号码"""
    records = get_all_ssq()
    if not records:
        print("[双色球] 无历史数据，跳过预测")
        return []

    main_keys = ["red1", "red2", "red3", "red4", "red5", "red6"]
    bonus_keys = ["blue"]
    main_range = (1, 33)
    bonus_range = (1, 16)

    subset = records[-PREDICTION_SPAN:] if len(records) >= PREDICTION_SPAN else records
    main_prob, bonus_prob = analyze(subset, main_keys, bonus_keys, main_range, bonus_range)

    main_freq = build_combination_freq(records, main_keys, max_k=6)
    total_draws = len(records)

    # 蓝球按概率排序，每组取不同的蓝球
    blues_sorted = sorted(bonus_prob.items(), key=lambda x: x[1], reverse=True)

    results = []
    used_reds = set()

    for i in range(combo_count):
        # 贪心选红球，排除已选号码
        reds = greedy_select(main_prob, main_freq, total_draws, 6, exclude=used_reds)
        reds_sorted = sorted(reds, key=lambda x: x[0])

        # 选蓝球：每组取排名不同的蓝球
        blue = blues_sorted[i % len(blues_sorted)]

        combined_prob = reduce(operator.mul, [p for _, p in reds_sorted]) * blue[1]

        results.append({
            "红区": [f"{num:02d}" for num, _ in reds_sorted],
            "蓝区": [f"{blue[0]:02d}"],
            "红区各号概率": {f"{num:02d}": round(p, 6) for num, p in reds_sorted},
            "蓝区各号概率": {f"{blue[0]:02d}": round(blue[1], 6)},
            "综合概率": combined_prob,
        })

        # 将本组红球加入排除集，保证下一组不重复
        used_reds.update(n for n, _ in reds_sorted)

    return results


def predict_dlt(combo_count=5):
    """大乐透预测：生成 combo_count 组推荐号码"""
    records = get_all_dlt()
    if not records:
        print("[大乐透] 无历史数据，跳过预测")
        return []

    main_keys = ["front1", "front2", "front3", "front4", "front5"]
    bonus_keys = ["back1", "back2"]
    main_range = (1, 35)
    bonus_range = (1, 12)

    subset = records[-PREDICTION_SPAN:] if len(records) >= PREDICTION_SPAN else records
    main_prob, bonus_prob = analyze(subset, main_keys, bonus_keys, main_range, bonus_range)

    main_freq = build_combination_freq(records, main_keys, max_k=5)
    bonus_freq = build_combination_freq(records, bonus_keys, max_k=2)
    total_draws = len(records)

    # 预生成多组后区候选
    used_backs = set()
    back_combos = []
    for _ in range(combo_count):
        backs = greedy_select(bonus_prob, bonus_freq, total_draws, 2, exclude=used_backs)
        back_combos.append(sorted(backs, key=lambda x: x[0]))
        used_backs.update(n for n, _ in backs)

    results = []
    used_fronts = set()

    for i in range(combo_count):
        fronts = greedy_select(main_prob, main_freq, total_draws, 5, exclude=used_fronts)
        fronts_sorted = sorted(fronts, key=lambda x: x[0])
        backs_sorted = back_combos[i]

        combined_prob = reduce(operator.mul, [p for _, p in fronts_sorted]) * reduce(
            operator.mul, [p for _, p in backs_sorted]
        )

        results.append({
            "前区": [f"{num:02d}" for num, _ in fronts_sorted],
            "后区": [f"{num:02d}" for num, _ in backs_sorted],
            "前区各号概率": {f"{num:02d}": round(p, 6) for num, p in fronts_sorted},
            "后区各号概率": {f"{num:02d}": round(p, 6) for num, p in backs_sorted},
            "综合概率": combined_prob,
        })

        used_fronts.update(n for n, _ in fronts_sorted)

    return results
