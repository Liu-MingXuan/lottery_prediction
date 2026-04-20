import requests
from bs4 import BeautifulSoup
from config import USER_AGENT, REQUEST_TIMEOUT
import db

SSQ_500_URL = "https://datachart.500.com/ssq/history/newinc/history.php"


def crawl_ssq():
    latest_issue = db.get_latest_issue("ssq")
    print(f"[双色球] 最新期号: {latest_issue or '无（全量爬取）'}")

    # 计算期号范围：如果有已有数据，从最新期号+1开始
    start = "03001"
    if latest_issue:
        year = int(latest_issue[:4])
        seq = int(latest_issue[4:])
        next_seq = seq + 1
        # 跨年处理
        start = f"{year}{next_seq:03d}"

    end = "99999"  # 让服务端返回到最新

    params = {"start": start, "end": end}
    headers = {"User-Agent": USER_AGENT}
    resp = requests.get(SSQ_500_URL, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
    resp.encoding = "gb2312"

    soup = BeautifulSoup(resp.text, "html.parser")
    rows = soup.select("tbody tr")

    all_records = []
    for row in rows:
        tds = row.find_all("td")
        if len(tds) < 8:
            continue

        issue = tds[0].get_text(strip=True)
        # 跳过已有记录
        if latest_issue and issue <= latest_issue:
            continue

        reds = [int(tds[i].get_text(strip=True)) for i in range(1, 7)]
        blue = int(tds[7].get_text(strip=True))

        # 500.com 没有直接提供日期，从期号推算年份
        year_prefix = "20" + issue[:2]
        draw_date = f"{year_prefix}"

        all_records.append((
            issue, draw_date,
            reds[0], reds[1], reds[2],
            reds[3], reds[4], reds[5],
            blue,
        ))

    db.insert_ssq(all_records)
    print(f"[双色球] 新增 {len(all_records)} 条记录")
    return len(all_records)
