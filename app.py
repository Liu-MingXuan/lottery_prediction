from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from database.db import init_db, get_all_ssq, get_all_dlt, get_conn
from crawler.ssq import crawl_ssq
from crawler.dlt import crawl_dlt
from analysis.predictor import predict_ssq, predict_dlt

app = FastAPI(title="彩票预测系统")

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
def index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.get("/api/history/ssq")
def history_ssq(page: int = 1, size: int = 20):
    records = get_all_ssq()
    total = len(records)
    start = total - page * size
    end = total - (page - 1) * size
    page_records = records[max(0, start):end]
    return {
        "total": total,
        "page": page,
        "records": page_records[::-1],
    }


@app.get("/api/history/dlt")
def history_dlt(page: int = 1, size: int = 20):
    records = get_all_dlt()
    total = len(records)
    start = total - page * size
    end = total - (page - 1) * size
    page_records = records[max(0, start):end]
    return {
        "total": total,
        "page": page,
        "records": page_records[::-1],
    }


@app.get("/api/predict")
def predict(period: int = Query(0, description="参考最近N期，0=全部"),
            count: int = Query(5, description="输出预测组数")):
    crawl_ssq()
    crawl_dlt()

    ssq_results = predict_ssq(combo_count=count, prediction_span=period)
    dlt_results = predict_dlt(combo_count=count, prediction_span=period)

    return {"双色球": ssq_results, "大乐透": dlt_results}


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


@app.on_event("startup")
def startup():
    init_db()
