import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "data" / "wms.db"

def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # 예시 테이블 (이미 있다면 IF NOT EXISTS)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_code TEXT,
        item_name TEXT,
        qty INTEGER,
        location TEXT
    )
    """)

    conn.commit()
    conn.close()

