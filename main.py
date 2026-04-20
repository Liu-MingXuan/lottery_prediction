import json
import db
import crawler_ssq
import crawler_dlt
import predictor


def main():
    # 1. 初始化数据库
    db.init_db()
    print("=" * 50)
    print("彩票预测系统")
    print("=" * 50)

    # 2. 爬取最新数据（增量）
    print("\n--- 爬取数据 ---")
    crawler_ssq.crawl_ssq()
    crawler_dlt.crawl_dlt()

    # 3. 概率分析 & 预测
    print("\n--- 预测结果 ---")
    ssq_result = predictor.predict_ssq()
    dlt_result = predictor.predict_dlt()

    result = {}
    if ssq_result:
        result["双色球"] = ssq_result
    if dlt_result:
        result["大乐透"] = dlt_result

    print(json.dumps(result, ensure_ascii=False, indent=4))


if __name__ == "__main__":
    main()
