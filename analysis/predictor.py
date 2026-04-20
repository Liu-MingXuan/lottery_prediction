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


def greedy_select(prob, freq, total_draws, count):
    """
    贪心选号：从候选池中逐个选取，综合考虑个体概率和子组合惩罚。
    每步选使 score = 个体概率 - 新增惩罚 最大的号码。
    """
    # 取概率最高的 CANDIDATE_POOL_SIZE 个号码作为候选池
    pool = sorted(prob.items(), key=lambda x: x[1], reverse=True)[:CANDIDATE_POOL_SIZE]
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


def predict_ssq():
    """双色球预测：6红+1蓝，带子组合惩罚"""
    records = get_all_ssq()
    if not records:
        print("[双色球] 无历史数据，跳过预测")
        return None

    main_keys = ["red1", "red2", "red3", "red4", "red5", "red6"]
    bonus_keys = ["blue"]
    main_range = (1, 33)
    bonus_range = (1, 16)

    # 用 PREDICTION_SPAN 期数据计算个体概率
    subset = records[-PREDICTION_SPAN:] if len(records) >= PREDICTION_SPAN else records
    main_prob, bonus_prob = analyze(subset, main_keys, bonus_keys, main_range, bonus_range)

    # 用全量历史构建子组合频率（惩罚基于全部历史）
    main_freq = build_combination_freq(records, main_keys, max_k=6)
    total_draws = len(records)

    # 贪心选红球（带惩罚）
    top_reds = greedy_select(main_prob, main_freq, total_draws, 6)
    top_reds_sorted = sorted(top_reds, key=lambda x: x[0])

    # 蓝球只选1个，无需子组合惩罚
    top_blue = sorted(bonus_prob.items(), key=lambda x: x[1], reverse=True)[:1]

    combined_prob = reduce(operator.mul, [p for _, p in top_reds_sorted]) * top_blue[0][1]

    return {
        "红区": [f"{num:02d}" for num, _ in top_reds_sorted],
        "蓝区": [f"{num:02d}" for num, _ in top_blue],
        "红区各号概率": {f"{num:02d}": round(p, 6) for num, p in top_reds_sorted},
        "蓝区各号概率": {f"{num:02d}": round(p, 6) for num, p in top_blue},
        "综合概率": combined_prob,
    }


def predict_dlt():
    """大乐透预测：5前区+2后区，带子组合惩罚"""
    records = get_all_dlt()
    if not records:
        print("[大乐透] 无历史数据，跳过预测")
        return None

    main_keys = ["front1", "front2", "front3", "front4", "front5"]
    bonus_keys = ["back1", "back2"]
    main_range = (1, 35)
    bonus_range = (1, 12)

    subset = records[-PREDICTION_SPAN:] if len(records) >= PREDICTION_SPAN else records
    main_prob, bonus_prob = analyze(subset, main_keys, bonus_keys, main_range, bonus_range)

    main_freq = build_combination_freq(records, main_keys, max_k=5)
    bonus_freq = build_combination_freq(records, bonus_keys, max_k=2)
    total_draws = len(records)

    # 贪心选前区（带惩罚）
    top_fronts = greedy_select(main_prob, main_freq, total_draws, 5)
    top_fronts_sorted = sorted(top_fronts, key=lambda x: x[0])

    # 贪心选后区（带惩罚）
    top_backs = greedy_select(bonus_prob, bonus_freq, total_draws, 2)
    top_backs_sorted = sorted(top_backs, key=lambda x: x[0])

    combined_prob = reduce(operator.mul, [p for _, p in top_fronts_sorted]) * reduce(
        operator.mul, [p for _, p in top_backs_sorted]
    )

    return {
        "前区": [f"{num:02d}" for num, _ in top_fronts_sorted],
        "后区": [f"{num:02d}" for num, _ in top_backs_sorted],
        "前区各号概率": {f"{num:02d}": round(p, 6) for num, p in top_fronts_sorted},
        "后区各号概率": {f"{num:02d}": round(p, 6) for num, p in top_backs_sorted},
        "综合概率": combined_prob,
    }
