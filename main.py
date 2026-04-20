import json
from database.db import init_db, get_all_ssq, get_all_dlt
from crawler.ssq import crawl_ssq
from crawler.dlt import crawl_dlt
from analysis.analyzer import multi_period_analysis
from analysis.predictor import predict_ssq, predict_dlt


def print_period_table(title, period_data, num_range):
    """打印多历史阶段概率表格"""
    periods = list(period_data.keys())
    header = f"{'号码':>4}"
    for p in periods:
        header += f" | {p:>10}"
    separator = "-" * len(header)

    print(f"\n{'=' * 20} {title} {'=' * 20}")
    print(header)
    print(separator)

    for num in range(num_range[0], num_range[1] + 1):
        row = f"{num:02d}  "
        for p in periods:
            main_prob, _ = period_data[p]
            val = main_prob.get(num, 0)
            row += f" | {val:>10.4f}"
        print(row)

    print(separator)
    # 合计行
    row = "合计 "
    for p in periods:
        main_prob, _ = period_data[p]
        total = sum(main_prob.values())
        row += f" | {total:>10.4f}"
    print(row)


def print_bonus_table(title, period_data, num_range):
    """打印副区（蓝区/后区）概率表格"""
    periods = list(period_data.keys())
    header = f"{'号码':>4}"
    for p in periods:
        header += f" | {p:>10}"
    separator = "-" * len(header)

    print(f"\n{'=' * 20} {title} {'=' * 20}")
    print(header)
    print(separator)

    for num in range(num_range[0], num_range[1] + 1):
        row = f"{num:02d}  "
        for p in periods:
            _, bonus_prob = period_data[p]
            val = bonus_prob.get(num, 0)
            row += f" | {val:>10.4f}"
        print(row)

    print(separator)
    row = "合计 "
    for p in periods:
        _, bonus_prob = period_data[p]
        total = sum(bonus_prob.values())
        row += f" | {total:>10.4f}"
    print(row)


def main():
    init_db()
    print("=" * 50)
    print("彩票预测系统")
    print("=" * 50)

    # 爬取数据
    print("\n--- 爬取数据 ---")
    crawl_ssq()
    crawl_dlt()

    # 多阶段概率分析
    ssq_records = get_all_ssq()
    dlt_records = get_all_dlt()

    if ssq_records:
        ssq_main_keys = ["red1", "red2", "red3", "red4", "red5", "red6"]
        ssq_bonus_keys = ["blue"]
        ssq_periods = multi_period_analysis(
            ssq_records, ssq_main_keys, ssq_bonus_keys, (1, 33), (1, 16)
        )
        print_period_table("双色球 红区概率", ssq_periods, (1, 33))
        print_bonus_table("双色球 蓝区概率", ssq_periods, (1, 16))

    if dlt_records:
        dlt_main_keys = ["front1", "front2", "front3", "front4", "front5"]
        dlt_bonus_keys = ["back1", "back2"]
        dlt_periods = multi_period_analysis(
            dlt_records, dlt_main_keys, dlt_bonus_keys, (1, 35), (1, 12)
        )
        print_period_table("大乐透 前区概率", dlt_periods, (1, 35))
        print_bonus_table("大乐透 后区概率", dlt_periods, (1, 12))

    # 预测结果
    print("\n" + "=" * 50)
    print("预测结果")
    print("=" * 50)

    ssq_result = predict_ssq()
    dlt_result = predict_dlt()

    result = {}
    if ssq_result:
        result["双色球"] = ssq_result
    if dlt_result:
        result["大乐透"] = dlt_result

    print(json.dumps(result, ensure_ascii=False, indent=4))


if __name__ == "__main__":
    main()
