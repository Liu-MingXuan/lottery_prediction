import requests
from bs4 import BeautifulSoup
from config import USER_AGENT, REQUEST_TIMEOUT
import db

DLT_500_URL = "https://datachart.500.com/dlt/history/newinc/history.php"


def crawl_dlt():
    latest_issue = db.get_latest_issue("dlt")
    print(f"[大乐透] 最新期号: {latest_issue or '无（全量爬取）'}")

    start = "07001"
    if latest_issue:
        year = int(latest_issue[:2])
        seq = int(latest_issue[2:])
        next_seq = seq + 1
        start = f"{year:02d}{next_seq:03d}"

    end = "99999"

    params = {"start": start, "end": end}
    headers = {"User-Agent": USER_AGENT}
    resp = requests.get(DLT_500_URL, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
    resp.encoding = "gb2312"

    soup = BeautifulSoup(resp.text, "html.parser")
    rows = soup.select("tbody tr")

    all_records = []
    for row in rows:
        tds = row.find_all("td")
        if len(tds) < 8:
            continue

        issue = tds[0].get_text(strip=True)
        if latest_issue and issue <= latest_issue:
            continue

        fronts = [int(tds[i].get_text(strip=True)) for i in range(1, 6)]
        backs = [int(tds[i].get_text(strip=True)) for i in range(6, 8)]

        year_prefix = "20" + issue[:2]
        draw_date = f"{year_prefix}"

        all_records.append((
            issue, draw_date,
            fronts[0], fronts[1], fronts[2],
            fronts[3], fronts[4],
            backs[0], backs[1],
        ))

    db.insert_dlt(all_records)
    print(f"[大乐透] 新增 {len(all_records)} 条记录")
    return len(all_records)
