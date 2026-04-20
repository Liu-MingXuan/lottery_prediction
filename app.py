from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional

from database.db import init_db, get_all_ssq, get_all_dlt, get_conn
from crawler.ssq import crawl_ssq
from crawler.dlt import crawl_dlt
from analysis.predictor import predict_ssq, predict_dlt

app = FastAPI(title="彩票预测系统")

app.mount("/static", StaticFiles(directory="static"), name="static")


# ========== 奖级表 ==========

SSQ_PRIZE_TABLE = [
    ((6, 1), "一等奖", "浮动（最高500万）"),
    ((6, 0), "二等奖", "浮动"),
    ((5, 1), "三等奖", "3,000元"),
    ((5, 0), "四等奖", "200元"),
    ((4, 1), "四等奖", "200元"),
    ((4, 0), "五等奖", "10元"),
    ((3, 1), "五等奖", "10元"),
    ((2, 1), "六等奖", "5元"),
    ((1, 1), "六等奖", "5元"),
    ((0, 1), "六等奖", "5元"),
]

DLT_PRIZE_TABLE = [
    ((5, 2), "一等奖", "浮动（最高1000万）"),
    ((5, 1), "二等奖", "浮动"),
    ((5, 0), "三等奖", "10,000元"),
    ((4, 2), "四等奖", "3,000元"),
    ((4, 1), "五等奖", "500元"),
    ((3, 2), "六等奖", "200元"),
    ((4, 0), "七等奖", "100元"),
    ((3, 1), "八等奖", "15元"),
    ((2, 2), "九等奖", "5元"),
    ((1, 2), "九等奖", "5元"),
    ((0, 2), "九等奖", "5元"),
]


def calc_prize(main_match: int, bonus_match: int, table: list) -> Optional[dict]:
    for (m, b), level, prize in table:
        if main_match == m and bonus_match == b:
            return {"level": level, "prize": prize}
    return None


# ========== 请求模型 ==========

class CheckRequest(BaseModel):
    type: str  # "ssq" or "dlt"
    main: List[int]
    bonus: List[int]


# ========== 页面 ==========

@app.get("/", response_class=HTMLResponse)
def index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()


# ========== 历史开奖 API ==========

@app.get("/api/history/ssq")
def history_ssq(page: int = 1, size: int = 20):
    records = get_all_ssq()
    total = len(records)
    start = total - page * size
    end = total - (page - 1) * size
    page_records = records[max(0, start):end]
    return {"total": total, "page": page, "records": page_records[::-1]}


@app.get("/api/history/dlt")
def history_dlt(page: int = 1, size: int = 20):
    records = get_all_dlt()
    total = len(records)
    start = total - page * size
    end = total - (page - 1) * size
    page_records = records[max(0, start):end]
    return {"total": total, "page": page, "records": page_records[::-1]}


# ========== 预测 API ==========

@app.get("/api/predict")
def predict(period: int = Query(0, description="参考最近N期，0=全部"),
            count: int = Query(5, description="输出预测组数")):
    crawl_ssq()
    crawl_dlt()

    ssq_results = predict_ssq(combo_count=count, prediction_span=period)
    dlt_results = predict_dlt(combo_count=count, prediction_span=period)

    return {"双色球": ssq_results, "大乐透": dlt_results}


# ========== 概率 API ==========

@app.get("/api/probability/ssq")
def probability_ssq():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT number, red_prob, blue_prob FROM ssq_probability ORDER BY number")
    rows = [{"number": r[0], "red_prob": r[1], "blue_prob": r[2]} for r in c.fetchall()]
    conn.close()
    return rows


@app.get("/api/probability/dlt")
def probability_dlt():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT number, front_prob, back_prob FROM dlt_probability ORDER BY number")
    rows = [{"number": r[0], "front_prob": r[1], "back_prob": r[2]} for r in c.fetchall()]
    conn.close()
    return rows


# ========== 号码查询 API ==========

@app.post("/api/check/history")
def check_history(req: CheckRequest):
    """查询一组号码是否为历史开奖记录（精确匹配）"""
    conn = get_conn()
    c = conn.cursor()

    if req.type == "ssq":
        main_sorted = sorted(req.main)
        bonus = req.bonus[0] if req.bonus else 0
        c.execute(
            "SELECT issue, draw_date, red1, red2, red3, red4, red5, red6, blue "
            "FROM ssq_history WHERE red1=? AND red2=? AND red3=? AND red4=? AND red5=? AND red6=? AND blue=?",
            (*main_sorted, bonus),
        )
        rows = c.fetchall()
        matches = [{"issue": r[0], "draw_date": r[1], "red": [r[2], r[3], r[4], r[5], r[6], r[7]], "blue": r[8]} for r in rows]
    else:
        main_sorted = sorted(req.main)
        bonus_sorted = sorted(req.bonus)
        c.execute(
            "SELECT issue, draw_date, front1, front2, front3, front4, front5, back1, back2 "
            "FROM dlt_history WHERE front1=? AND front2=? AND front3=? AND front4=? AND front5=? AND back1=? AND back2=?",
            (*main_sorted, *bonus_sorted),
        )
        rows = c.fetchall()
        matches = [{"issue": r[0], "draw_date": r[1], "front": [r[2], r[3], r[4], r[5], r[6]], "back": [r[7], r[8]]} for r in rows]

    conn.close()
    return {"found": len(matches) > 0, "count": len(matches), "matches": matches}


@app.post("/api/check/prize")
def check_prize(req: CheckRequest):
    """计算购买号码的中奖等级（对比最近一期开奖）"""
    conn = get_conn()
    c = conn.cursor()

    if req.type == "ssq":
        c.execute("SELECT issue, draw_date, red1, red2, red3, red4, red5, red6, blue FROM ssq_history ORDER BY issue DESC LIMIT 1")
        row = c.fetchone()
        if not row:
            conn.close()
            return {"error": "暂无双色球历史数据"}

        latest = {
            "issue": row[0], "draw_date": row[1],
            "red": sorted([row[2], row[3], row[4], row[5], row[6], row[7]]),
            "blue": row[8],
        }
        main_match = len(set(req.main) & set(latest["red"]))
        bonus_match = 1 if req.bonus and req.bonus[0] == latest["blue"] else 0
        prize = calc_prize(main_match, bonus_match, SSQ_PRIZE_TABLE)

        result = {
            "latest": latest,
            "user_main": sorted(req.main),
            "user_blue": req.bonus[0] if req.bonus else None,
            "main_match": main_match,
            "bonus_match": bonus_match,
            "prize": prize,
        }
    else:
        c.execute("SELECT issue, draw_date, front1, front2, front3, front4, front5, back1, back2 FROM dlt_history ORDER BY issue DESC LIMIT 1")
        row = c.fetchone()
        if not row:
            conn.close()
            return {"error": "暂无大乐透历史数据"}

        latest = {
            "issue": row[0], "draw_date": row[1],
            "front": sorted([row[2], row[3], row[4], row[5], row[6]]),
            "back": sorted([row[7], row[8]]),
        }
        main_match = len(set(req.main) & set(latest["front"]))
        bonus_match = len(set(req.bonus) & set(latest["back"]))
        prize = calc_prize(main_match, bonus_match, DLT_PRIZE_TABLE)

        result = {
            "latest": latest,
            "user_front": sorted(req.main),
            "user_back": sorted(req.bonus),
            "main_match": main_match,
            "bonus_match": bonus_match,
            "prize": prize,
        }

    conn.close()
    return result


@app.get("/api/prize-table/{type}")
def prize_table(type: str):
    """获取奖级表"""
    table = SSQ_PRIZE_TABLE if type == "ssq" else DLT_PRIZE_TABLE
    is_ssq = type == "ssq"
    main_label = "红球" if is_ssq else "前区"
    bonus_label = "蓝球" if is_ssq else "后区"
    return [{
        "main": m, "bonus": b, "level": level, "prize": prize,
        "main_label": main_label, "bonus_label": bonus_label,
    } for (m, b), level, prize in table]


@app.on_event("startup")
def startup():
    init_db()
