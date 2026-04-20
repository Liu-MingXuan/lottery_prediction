from itertools import combinations
from collections import defaultdict
from functools import reduce
import operator

from config import COMBO_PENALTY_WEIGHTS, CANDIDATE_POOL_SIZE
from analysis.analyzer import analyze
from database.db import (
    get_all_ssq, get_all_dlt,
    save_ssq_probability, save_dlt_probability,
)


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


def greedy_select(prob, freq, total_draws, count, prev_combos=None):
    """
    贪心选号：综合考虑个体概率、历史子组合惩罚和已选组合去重惩罚。
    prev_combos: 前几组已选的号码组合列表，用于增加重复惩罚
    """
    pool = sorted(prob.items(), key=lambda x: x[1], reverse=True)[:CANDIDATE_POOL_SIZE]
    selected = []
    remaining = list(pool)

    for _ in range(count):
        best_score = -float("inf")
        best_idx = 0

        for i, (num, p) in enumerate(remaining):
            test_set = [n for n, _ in selected] + [num]
            penalty = calc_penalty(test_set, freq, total_draws)
            if prev_combos:
                for combo in prev_combos:
                    overlap = len(set(test_set) & set(combo))
                    penalty += overlap * 0.05
            score = p - penalty
            if score > best_score:
                best_score = score
                best_idx = i

        selected.append(remaining[best_idx])
        remaining.pop(best_idx)

    return selected


def predict_ssq(combo_count=5, prediction_span=None):
    """双色球预测：生成 combo_count 组推荐号码"""
    records = get_all_ssq()
    if not records:
        print("[双色球] 无历史数据，跳过预测")
        return []

    main_keys = ["red1", "red2", "red3", "red4", "red5", "red6"]
    bonus_keys = ["blue"]
    main_range = (1, 33)
    bonus_range = (1, 16)

    # prediction_span: 0 表示使用全部历史，否则使用最近 N 期
    if prediction_span and prediction_span > 0:
        subset = records[-prediction_span:] if len(records) >= prediction_span else records
    else:
        subset = records

    main_prob, bonus_prob = analyze(subset, main_keys, bonus_keys, main_range, bonus_range)

    # 保存概率到数据库
    prob_rows = []
    for num in range(1, 34):
        prob_rows.append((num, round(main_prob.get(num, 0), 6), round(bonus_prob.get(num, 0), 6)))
    save_ssq_probability(prob_rows)

    main_freq = build_combination_freq(records, main_keys, max_k=6)
    total_draws = len(records)

    blues_sorted = sorted(bonus_prob.items(), key=lambda x: x[1], reverse=True)

    results = []
    prev_red_combos = []

    for i in range(combo_count):
        reds = greedy_select(main_prob, main_freq, total_draws, 6, prev_combos=prev_red_combos)
        reds_sorted = sorted(reds, key=lambda x: x[0])

        blue = blues_sorted[i % len(blues_sorted)]

        combined_prob = reduce(operator.mul, [p for _, p in reds_sorted]) * blue[1]

        results.append({
            "红区": [f"{num:02d}" for num, _ in reds_sorted],
            "蓝区": [f"{blue[0]:02d}"],
            "红区各号概率": {f"{num:02d}": round(p, 6) for num, p in reds_sorted},
            "蓝区各号概率": {f"{blue[0]:02d}": round(blue[1], 6)},
            "综合概率": combined_prob,
        })

        prev_red_combos.append([n for n, _ in reds_sorted])

    return results


def predict_dlt(combo_count=5, prediction_span=None):
    """大乐透预测：生成 combo_count 组推荐号码"""
    records = get_all_dlt()
    if not records:
        print("[大乐透] 无历史数据，跳过预测")
        return []

    main_keys = ["front1", "front2", "front3", "front4", "front5"]
    bonus_keys = ["back1", "back2"]
    main_range = (1, 35)
    bonus_range = (1, 12)

    if prediction_span and prediction_span > 0:
        subset = records[-prediction_span:] if len(records) >= prediction_span else records
    else:
        subset = records

    main_prob, bonus_prob = analyze(subset, main_keys, bonus_keys, main_range, bonus_range)

    # 保存概率到数据库
    prob_rows = []
    for num in range(1, 36):
        prob_rows.append((num, round(main_prob.get(num, 0), 6), round(bonus_prob.get(num, 0), 6)))
    save_dlt_probability(prob_rows)

    main_freq = build_combination_freq(records, main_keys, max_k=5)
    bonus_freq = build_combination_freq(records, bonus_keys, max_k=2)
    total_draws = len(records)

    back_combos = []
    prev_back_combos = []
    for _ in range(combo_count):
        backs = greedy_select(bonus_prob, bonus_freq, total_draws, 2, prev_combos=prev_back_combos)
        backs_sorted = sorted(backs, key=lambda x: x[0])
        back_combos.append(backs_sorted)
        prev_back_combos.append([n for n, _ in backs_sorted])

    results = []
    prev_front_combos = []

    for i in range(combo_count):
        fronts = greedy_select(main_prob, main_freq, total_draws, 5, prev_combos=prev_front_combos)
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

        prev_front_combos.append([n for n, _ in fronts_sorted])

    return results
