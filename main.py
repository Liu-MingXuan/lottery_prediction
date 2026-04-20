import argparse
import json
from database.db import init_db, get_all_ssq, get_all_dlt, get_conn
from crawler.ssq import crawl_ssq
from crawler.dlt import crawl_dlt
from analysis.analyzer import multi_period_analysis
from analysis.predictor import predict_ssq, predict_dlt


def print_period_table(title, period_data, num_range):
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
    row = "合计 "
    for p in periods:
        main_prob, _ = period_data[p]
        total = sum(main_prob.values())
        row += f" | {total:>10.4f}"
    print(row)


def print_bonus_table(title, period_data, num_range):
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


def print_prob_table(title, prob_records, main_col, bonus_col):
    """打印数据库中的概率表格"""
    header = f"{'号码':>4} | {main_col:>10} | {bonus_col:>10}"
    separator = "-" * len(header)

    print(f"\n{'=' * 20} {title} {'=' * 20}")
    print(header)
    print(separator)

    for r in prob_records:
        num = r[0]
        main_val = r[1]
        bonus_val = r[2]
        row = f"{num:02d}  | {main_val:>10.6f} | {bonus_val:>10.6f}"
        print(row)

    print(separator)


def main():
    parser = argparse.ArgumentParser(description="彩票预测系统")
    parser.add_argument(
        "-p", "--period", type=int, default=0,
        help="参考最近 N 期历史记录，0 表示参考全部历史（默认: 0）",
    )
    parser.add_argument(
        "-c", "--count", type=int, default=5,
        help="输出预测号码的组数（默认: 5）",
    )
    args = parser.parse_args()

    period_label = "全部历史" if args.period == 0 else f"最近{args.period}期"

    init_db()
    print("=" * 50)
    print("彩票预测系统")
    print(f"参考历史: {period_label} | 预测组数: {args.count}")
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
    print(f"\n{'=' * 50}")
    print(f"预测结果（{args.count}组推荐）")
    print("=" * 50)

    ssq_results = predict_ssq(combo_count=args.count, prediction_span=args.period)
    dlt_results = predict_dlt(combo_count=args.count, prediction_span=args.period)

    if ssq_results:
        print("\n【双色球】")
        for i, r in enumerate(ssq_results, 1):
            reds = " ".join(r["红区"])
            blue = r["蓝区"][0]
            prob = r["综合概率"]
            print(f"  第{i}组: {reds} + {blue}  (综合概率: {prob:.2e})")

    if dlt_results:
        print("\n【大乐透】")
        for i, r in enumerate(dlt_results, 1):
            fronts = " ".join(r["前区"])
            backs = " ".join(r["后区"])
            prob = r["综合概率"]
            print(f"  第{i}组: {fronts} + {backs}  (综合概率: {prob:.2e})")

    # 打印数据库中的概率表
    print(f"\n{'=' * 50}")
    print("号码概率总表")
    print("=" * 50)

    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM ssq_probability ORDER BY number ASC")
    print_prob_table("双色球 号码概率", c.fetchall(), "红区", "蓝区")

    c.execute("SELECT * FROM dlt_probability ORDER BY number ASC")
    print_prob_table("大乐透 号码概率", c.fetchall(), "前区", "后区")
    conn.close()

    # 详细概率数据
    print("\n--- 详细概率数据 ---")
    result = {}
    if ssq_results:
        result["双色球"] = ssq_results
    if dlt_results:
        result["大乐透"] = dlt_results
    print(json.dumps(result, ensure_ascii=False, indent=4))


if __name__ == "__main__":
    main()
