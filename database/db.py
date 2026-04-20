import sqlite3
from config import DB_PATH


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS ssq_history (
            issue TEXT PRIMARY KEY,
            draw_date TEXT,
            red1 INTEGER, red2 INTEGER, red3 INTEGER,
            red4 INTEGER, red5 INTEGER, red6 INTEGER,
            blue INTEGER
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS dlt_history (
            issue TEXT PRIMARY KEY,
            draw_date TEXT,
            front1 INTEGER, front2 INTEGER, front3 INTEGER,
            front4 INTEGER, front5 INTEGER,
            back1 INTEGER, back2 INTEGER
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS ssq_probability (
            number INTEGER PRIMARY KEY,
            red_prob REAL,
            blue_prob REAL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS dlt_probability (
            number INTEGER PRIMARY KEY,
            front_prob REAL,
            back_prob REAL
        )
    """)
    conn.commit()
    conn.close()


def get_latest_issue(lottery_type):
    table = "ssq_history" if lottery_type == "ssq" else "dlt_history"
    conn = get_conn()
    c = conn.cursor()
    c.execute(f"SELECT MAX(issue) FROM {table}")
    row = c.fetchone()
    conn.close()
    return row[0] if row and row[0] else None


def insert_ssq(records):
    if not records:
        return
    conn = get_conn()
    c = conn.cursor()
    c.executemany(
        "INSERT OR IGNORE INTO ssq_history "
        "(issue, draw_date, red1, red2, red3, red4, red5, red6, blue) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        records,
    )
    conn.commit()
    conn.close()


def insert_dlt(records):
    if not records:
        return
    conn = get_conn()
    c = conn.cursor()
    c.executemany(
        "INSERT OR IGNORE INTO dlt_history "
        "(issue, draw_date, front1, front2, front3, front4, front5, back1, back2) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        records,
    )
    conn.commit()
    conn.close()


def get_all_ssq():
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM ssq_history ORDER BY issue ASC")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_dlt():
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM dlt_history ORDER BY issue ASC")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_ssq_probability(records):
    """保存双色球每个号码的红区/蓝区概率"""
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM ssq_probability")
    c.executemany(
        "INSERT INTO ssq_probability (number, red_prob, blue_prob) VALUES (?, ?, ?)",
        records,
    )
    conn.commit()
    conn.close()


def save_dlt_probability(records):
    """保存大乐透每个号码的前区/后区概率"""
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM dlt_probability")
    c.executemany(
        "INSERT INTO dlt_probability (number, front_prob, back_prob) VALUES (?, ?, ?)",
        records,
    )
    conn.commit()
    conn.close()
