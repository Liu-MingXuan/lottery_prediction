from collections import defaultdict
from config import (
    WEIGHT_BASE_FREQ, WEIGHT_RECENT_FREQ, WEIGHT_MISS,
    WEIGHT_ODD_EVEN, WEIGHT_SUM_REGRESSION, WEIGHT_COLD_HOT,
    WEIGHT_ZONE_DISTRIBUTION,
    RECENT_PERIODS, ANALYSIS_PERIODS, PREDICTION_SPAN,
    HOT_COLD_RECENT,
)


def simple_frequency(records, keys, num_range):
    total = len(records) if records else 1
    count = defaultdict(int)
    for r in records:
        for key in keys:
            count[r[key]] += 1
    return {n: count.get(n, 0) / total for n in range(num_range[0], num_range[1] + 1)}


def _base_frequency(records, main_keys, bonus_keys, main_range, bonus_range):
    total = len(records) if records else 1
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


def _recent_weighted_frequency(records, main_keys, bonus_keys, main_range, bonus_range):
    n = len(records)
    if n == 0:
        return {}, {}
    main_weighted = defaultdict(float)
    bonus_weighted = defaultdict(float)
    total_weight = 0
    for i, r in enumerate(records):
        weight = i + 1
        total_weight += weight
        for key in main_keys:
            main_weighted[r[key]] += weight
        for key in bonus_keys:
            bonus_weighted[r[key]] += weight
    main_freq = {num: main_weighted[num] / total_weight for num in range(main_range[0], main_range[1] + 1)}
    bonus_freq = {num: bonus_weighted[num] / total_weight for num in range(bonus_range[0], bonus_range[1] + 1)}
    return main_freq, bonus_freq


def _miss_probability(records, main_keys, bonus_keys, main_range, bonus_range):
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


# ========== 新增：遗漏值（当前连续未出现期数） ==========

def miss_values(records, main_keys, bonus_keys, main_range, bonus_range):
    main_miss = {}
    bonus_miss = {}
    n = len(records)

    for num in range(main_range[0], main_range[1] + 1):
        miss = n
        for i in range(n - 1, -1, -1):
            if any(records[i][key] == num for key in main_keys):
                miss = n - 1 - i
                break
        main_miss[num] = miss

    for num in range(bonus_range[0], bonus_range[1] + 1):
        miss = n
        for i in range(n - 1, -1, -1):
            if any(records[i][key] == num for key in bonus_keys):
                miss = n - 1 - i
                break
        bonus_miss[num] = miss

    return main_miss, bonus_miss


# ========== 新增：奇偶比分析 ==========

def _odd_even_count(numbers):
    odd = sum(1 for n in numbers if n % 2 == 1)
    even = len(numbers) - odd
    return odd, even


def odd_even_stats(records, main_keys, bonus_keys):
    main_ratios = []
    bonus_ratios = []
    for r in records:
        main_nums = [r[key] for key in main_keys]
        bonus_nums = [r[key] for key in bonus_keys]
        main_ratios.append(_odd_even_count(main_nums))
        bonus_ratios.append(_odd_even_count(bonus_nums))
    return main_ratios, bonus_ratios


# ========== 新增：求和值分析 ==========

def sum_stats(records, main_keys, bonus_keys):
    main_sums = [sum(r[key] for key in main_keys) for r in records]
    bonus_sums = [sum(r[key] for key in bonus_keys) for r in records]
    return main_sums, bonus_sums


# ========== 新增：冷热号分析 ==========

def hot_cold_classify(records, main_keys, bonus_keys, main_range, bonus_range, recent=HOT_COLD_RECENT):
    recent_records = records[-recent:] if len(records) >= recent else records

    def classify(keys, num_range):
        count = defaultdict(int)
        for r in recent_records:
            for key in keys:
                count[r[key]] += 1
        total_nums = sum(count.values()) if count else 1
        num_count = len(num_range)
        expected_per_num = total_nums / num_count if num_count else 1
        result = {}
        for num in range(num_range[0], num_range[1] + 1):
            freq = count.get(num, 0)
            if freq > expected_per_num * 1.2:
                result[num] = "hot"
            elif freq < expected_per_num * 0.8:
                result[num] = "cold"
            else:
                result[num] = "warm"
        return result

    main_cls = classify(main_keys, main_range)
    bonus_cls = classify(bonus_keys, bonus_range)
    return main_cls, bonus_cls


# ========== 新增：分区分布 ==========

def _get_zone(num, main_range):
    span = main_range[1] - main_range[0] + 1
    third = span / 3
    offset = num - main_range[0]
    if offset < third:
        return "low"
    elif offset < third * 2:
        return "mid"
    else:
        return "high"


def zone_distribution(records, main_keys, bonus_keys, main_range, bonus_range):
    def calc(keys, num_range):
        zones = {"low": 0, "mid": 0, "high": 0}
        total = 0
        for r in records:
            for key in keys:
                z = _get_zone(r[key], num_range)
                zones[z] += 1
                total += 1
        if total == 0:
            return {"low": 0.333, "mid": 0.333, "high": 0.334}
        return {k: v / total for k, v in zones.items()}

    return calc(main_keys, main_range), calc(bonus_keys, bonus_range)


# ========== 新增：概率调整函数 ==========

def _odd_even_adjustment(records, keys, prob, num_range):
    all_ratios = [_odd_even_count([r[key] for key in keys]) for r in records]
    if not all_ratios:
        return {n: 0 for n in range(num_range[0], num_range[1] + 1)}
    avg_odd = sum(o for o, e in all_ratios) / len(all_ratios)
    avg_even = sum(e for o, e in all_ratios) / len(all_ratios)
    total_avg = avg_odd + avg_even
    odd_ratio = avg_odd / total_avg
    even_ratio = avg_even / total_avg

    recent_n = min(50, len(records))
    recent_ratios = [_odd_even_count([r[key] for key in keys]) for r in records[-recent_n:]]
    r_avg_odd = sum(o for o, e in recent_ratios) / len(recent_ratios)
    r_avg_even = sum(e for o, e in recent_ratios) / len(recent_ratios)
    r_total = r_avg_odd + r_avg_even
    r_odd_ratio = r_avg_odd / r_total
    r_even_ratio = r_avg_even / r_total

    odd_diff = odd_ratio - r_odd_ratio
    even_diff = even_ratio - r_even_ratio
    adjustment = {}
    for num in range(num_range[0], num_range[1] + 1):
        if num % 2 == 1:
            adjustment[num] = odd_diff
        else:
            adjustment[num] = even_diff
    return adjustment


def _sum_regression(records, keys, prob, num_range):
    sums = [sum(r[key] for key in keys) for r in records]
    if not sums:
        return {n: 0 for n in range(num_range[0], num_range[1] + 1)}
    avg_sum = sum(sums) / len(sums)

    recent_n = min(50, len(records))
    recent_sums = [sum(r[key] for key in keys) for r in records[-recent_n:]]
    r_avg_sum = sum(recent_sums) / len(recent_sums)

    diff = avg_sum - r_avg_sum
    if abs(diff) < 1:
        return {n: 0 for n in range(num_range[0], num_range[1] + 1)}

    adjustment = {}
    for num in range(num_range[0], num_range[1] + 1):
        if diff > 0:
            adjustment[num] = (num / avg_sum) * (diff / avg_sum)
        else:
            adjustment[num] = ((num_range[1] + num_range[0] - num) / avg_sum) * (abs(diff) / avg_sum)
    return adjustment


def _cold_hot_adjustment(records, keys, prob, num_range, recent=HOT_COLD_RECENT):
    recent_records = records[-recent:] if len(records) >= recent else records
    count = defaultdict(int)
    for r in recent_records:
        for key in keys:
            count[r[key]] += 1
    num_count = num_range[1] - num_range[0] + 1
    total = sum(count.values()) if count else 1
    expected = total / num_count

    adjustment = {}
    for num in range(num_range[0], num_range[1] + 1):
        freq = count.get(num, 0)
        ratio = freq / expected if expected > 0 else 1
        if ratio < 0.8:
            adjustment[num] = (1 - ratio) * 0.5
        elif ratio > 1.2:
            adjustment[num] = -(ratio - 1) * 0.3
        else:
            adjustment[num] = 0
    return adjustment


def _zone_distribution_adjustment(records, keys, prob, num_range):
    hist_dist, _ = zone_distribution(records, keys, [], num_range, num_range)

    recent_n = min(50, len(records))
    recent_dist, _ = zone_distribution(records[-recent_n:], keys, [], num_range, num_range)

    diff = {z: hist_dist[z] - recent_dist[z] for z in ["low", "mid", "high"]}

    adjustment = {}
    for num in range(num_range[0], num_range[1] + 1):
        z = _get_zone(num, num_range)
        adjustment[num] = diff.get(z, 0)
    return adjustment


# ========== 归一化 ==========

def _normalize(freq):
    total = sum(freq.values())
    if total == 0:
        return freq
    return {k: v / total for k, v in freq.items()}


# ========== 增强的综合分析（7 维度加权） ==========

def analyze(records, main_keys, bonus_keys, main_range, bonus_range,
            recent_periods=RECENT_PERIODS):
    base_main, base_bonus = _base_frequency(
        records, main_keys, bonus_keys, main_range, bonus_range
    )
    recent_main, recent_bonus = _recent_weighted_frequency(
        records, main_keys, bonus_keys, main_range, bonus_range
    )
    miss_main, miss_bonus = _miss_probability(
        records, main_keys, bonus_keys, main_range, bonus_range
    )
    oe_adj_main = _odd_even_adjustment(records, main_keys, base_main, main_range)
    oe_adj_bonus = _odd_even_adjustment(records, bonus_keys, base_bonus, bonus_range)
    sum_adj_main = _sum_regression(records, main_keys, base_main, main_range)
    sum_adj_bonus = _sum_regression(records, bonus_keys, base_bonus, bonus_range)
    ch_adj_main = _cold_hot_adjustment(records, main_keys, base_main, main_range)
    ch_adj_bonus = _cold_hot_adjustment(records, bonus_keys, base_bonus, bonus_range)
    zd_adj_main = _zone_distribution_adjustment(records, main_keys, base_main, main_range)
    zd_adj_bonus = _zone_distribution_adjustment(records, bonus_keys, base_bonus, bonus_range)

    combined_main = {}
    for num in range(main_range[0], main_range[1] + 1):
        combined_main[num] = (
            WEIGHT_BASE_FREQ * base_main.get(num, 0)
            + WEIGHT_RECENT_FREQ * recent_main.get(num, 0)
            + WEIGHT_MISS * miss_main.get(num, 0)
            + WEIGHT_ODD_EVEN * oe_adj_main.get(num, 0)
            + WEIGHT_SUM_REGRESSION * sum_adj_main.get(num, 0)
            + WEIGHT_COLD_HOT * ch_adj_main.get(num, 0)
            + WEIGHT_ZONE_DISTRIBUTION * zd_adj_main.get(num, 0)
        )

    combined_bonus = {}
    for num in range(bonus_range[0], bonus_range[1] + 1):
        combined_bonus[num] = (
            WEIGHT_BASE_FREQ * base_bonus.get(num, 0)
            + WEIGHT_RECENT_FREQ * recent_bonus.get(num, 0)
            + WEIGHT_MISS * miss_bonus.get(num, 0)
            + WEIGHT_ODD_EVEN * oe_adj_bonus.get(num, 0)
            + WEIGHT_SUM_REGRESSION * sum_adj_bonus.get(num, 0)
            + WEIGHT_COLD_HOT * ch_adj_bonus.get(num, 0)
            + WEIGHT_ZONE_DISTRIBUTION * zd_adj_bonus.get(num, 0)
        )

    return _normalize(combined_main), _normalize(combined_bonus)


# ========== 多阶段分析（保持兼容） ==========

def multi_period_analysis(records, main_keys, bonus_keys, main_range, bonus_range):
    result = {}

    for period in ANALYSIS_PERIODS:
        subset = records[-period:] if len(records) >= period else records
        main_prob = simple_frequency(subset, main_keys, main_range)
        bonus_prob = simple_frequency(subset, bonus_keys, bonus_range)
        result[f"最近{period}期"] = (main_prob, bonus_prob)

    main_all = simple_frequency(records, main_keys, main_range)
    bonus_all = simple_frequency(records, bonus_keys, bonus_range)
    result["所有历史"] = (main_all, bonus_all)

    prediction_records = records[-PREDICTION_SPAN:] if len(records) >= PREDICTION_SPAN else records
    main_pred, bonus_pred = analyze(
        prediction_records, main_keys, bonus_keys, main_range, bonus_range
    )
    result["预测"] = (main_pred, bonus_pred)

    return result


# ========== 综合分析接口（供 API 使用） ==========

def full_analysis(records, main_keys, bonus_keys, main_range, bonus_range, period=0):
    if period and period > 0:
        subset = records[-period:] if len(records) >= period else records
    else:
        subset = records

    main_prob, bonus_prob = analyze(subset, main_keys, bonus_keys, main_range, bonus_range)
    main_miss, bonus_miss = miss_values(subset, main_keys, bonus_keys, main_range, bonus_range)
    main_oe_ratios, bonus_oe_ratios = odd_even_stats(subset, main_keys, bonus_keys)
    main_sums, bonus_sums = sum_stats(subset, main_keys, bonus_keys)
    main_cls, bonus_cls = hot_cold_classify(subset, main_keys, bonus_keys, main_range, bonus_range)
    main_dist, bonus_dist = zone_distribution(subset, main_keys, bonus_keys, main_range, bonus_range)

    # 概率排行
    main_prob_rank = sorted(
        [{"number": num, "prob": round(p, 6)} for num, p in main_prob.items()],
        key=lambda x: x["prob"], reverse=True
    )
    bonus_prob_rank = sorted(
        [{"number": num, "prob": round(p, 6)} for num, p in bonus_prob.items()],
        key=lambda x: x["prob"], reverse=True
    )

    # 遗漏排行
    main_miss_rank = sorted(
        [{"number": num, "miss": m} for num, m in main_miss.items()],
        key=lambda x: x["miss"], reverse=True
    )
    bonus_miss_rank = sorted(
        [{"number": num, "miss": m} for num, m in bonus_miss.items()],
        key=lambda x: x["miss"], reverse=True
    )

    def _avg_ratio(ratios):
        if not ratios:
            return "0:0"
        avg_o = sum(o for o, e in ratios) / len(ratios)
        avg_e = sum(e for o, e in ratios) / len(ratios)
        return f"{avg_o:.1f}:{avg_e:.1f}"

    recent_n = min(30, len(subset))
    recent_oe_main, recent_oe_bonus = odd_even_stats(subset[-recent_n:], main_keys, bonus_keys)

    recent_sums_main, recent_sums_bonus = sum_stats(subset[-recent_n:], main_keys, bonus_keys)

    # 冷热号分组
    def _group_by_cls(cls):
        hot, warm, cold = [], [], []
        for num, c in sorted(cls.items()):
            if c == "hot":
                hot.append(num)
            elif c == "cold":
                cold.append(num)
            else:
                warm.append(num)
        return {"hot": hot, "warm": warm, "cold": cold}

    return {
        "probabilities": {"main": main_prob_rank, "bonus": bonus_prob_rank},
        "miss_values": {"main": main_miss_rank, "bonus": bonus_miss_rank},
        "stats": {
            "odd_even": {
                "main": {
                    "history_avg": _avg_ratio(main_oe_ratios),
                    "recent_avg": _avg_ratio(recent_oe_main),
                },
                "bonus": {
                    "history_avg": _avg_ratio(bonus_oe_ratios),
                    "recent_avg": _avg_ratio(recent_oe_bonus),
                },
            },
            "sum_range": {
                "main": {
                    "min": min(main_sums) if main_sums else 0,
                    "max": max(main_sums) if main_sums else 0,
                    "avg": round(sum(main_sums) / len(main_sums), 1) if main_sums else 0,
                    "recent_avg": round(sum(recent_sums_main) / len(recent_sums_main), 1) if recent_sums_main else 0,
                },
                "bonus": {
                    "min": min(bonus_sums) if bonus_sums else 0,
                    "max": max(bonus_sums) if bonus_sums else 0,
                    "avg": round(sum(bonus_sums) / len(bonus_sums), 1) if bonus_sums else 0,
                    "recent_avg": round(sum(recent_sums_bonus) / len(recent_sums_bonus), 1) if recent_sums_bonus else 0,
                },
            },
            "hot_cold": {
                "main": _group_by_cls(main_cls),
                "bonus": _group_by_cls(bonus_cls),
            },
            "distribution": {
                "main": {k: round(v, 3) for k, v in main_dist.items()},
                "bonus": {k: round(v, 3) for k, v in bonus_dist.items()},
            },
        },
        "heatmap": {
            "main": {num: main_cls[num] for num in range(main_range[0], main_range[1] + 1)},
            "bonus": {num: bonus_cls[num] for num in range(bonus_range[0], bonus_range[1] + 1)},
        },
        "total_periods": len(subset),
    }
