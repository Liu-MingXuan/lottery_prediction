from functools import reduce
import operator
import analyzer
import db


def predict_ssq():
    """双色球预测：6红+1蓝"""
    records = db.get_all_ssq()
    if not records:
        print("[双色球] 无历史数据，跳过预测")
        return None

    main_keys = ["red1", "red2", "red3", "red4", "red5", "red6"]
    bonus_keys = ["blue"]
    main_range = (1, 33)
    bonus_range = (1, 16)

    main_prob, bonus_prob = analyzer.analyze(
        records, main_keys, bonus_keys, main_range, bonus_range
    )

    # 取概率最高的 6 个红球
    top_reds = sorted(main_prob.items(), key=lambda x: x[1], reverse=True)[:6]
    top_reds_sorted = sorted(top_reds, key=lambda x: x[0])

    # 取概率最高的 1 个蓝球
    top_blue = sorted(bonus_prob.items(), key=lambda x: x[1], reverse=True)[:1]

    # 综合概率
    combined_prob = reduce(operator.mul, [p for _, p in top_reds_sorted]) * top_blue[0][1]

    return {
        "红区": [f"{num:02d}" for num, _ in top_reds_sorted],
        "蓝区": [f"{num:02d}" for num, _ in top_blue],
        "红区各号概率": {f"{num:02d}": round(p, 6) for num, p in top_reds_sorted},
        "蓝区各号概率": {f"{num:02d}": round(p, 6) for num, p in top_blue},
        "综合概率": combined_prob,
    }


def predict_dlt():
    """大乐透预测：5前区+2后区"""
    records = db.get_all_dlt()
    if not records:
        print("[大乐透] 无历史数据，跳过预测")
        return None

    main_keys = ["front1", "front2", "front3", "front4", "front5"]
    bonus_keys = ["back1", "back2"]
    main_range = (1, 35)
    bonus_range = (1, 12)

    main_prob, bonus_prob = analyzer.analyze(
        records, main_keys, bonus_keys, main_range, bonus_range
    )

    # 取概率最高的 5 个前区
    top_fronts = sorted(main_prob.items(), key=lambda x: x[1], reverse=True)[:5]
    top_fronts_sorted = sorted(top_fronts, key=lambda x: x[0])

    # 取概率最高的 2 个后区
    top_backs = sorted(bonus_prob.items(), key=lambda x: x[1], reverse=True)[:2]
    top_backs_sorted = sorted(top_backs, key=lambda x: x[0])

    # 综合概率
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
