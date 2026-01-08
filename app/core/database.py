import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(os.path.dirname(BASE_DIR), "..", "WMS.db")
DB_PATH = os.path.abspath(DB_PATH)


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # 품목 테이블
    cur.execute("""
        CREATE TABLE IF NOT EXISTS items (
            item_code TEXT PRIMARY KEY,
            item_name TEXT,
            spec TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Location
    cur.execute("""
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            warehouse TEXT NOT NULL,
            location TEXT NOT NULL,
            UNIQUE(warehouse, location)
        )
    """)

    # 재고 트랜잭션 테이블
    cur.execute("""
        CREATE TABLE IF NOT EXISTS inventory_tx (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tx_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            tx_type TEXT NOT NULL,
            warehouse TEXT NOT NULL,
            location TEXT NOT NULL,
            item_code TEXT NOT NULL,
            lot_no TEXT NOT NULL,
            qty REAL NOT NULL,
            remark TEXT,
            FOREIGN KEY(item_code) REFERENCES items(item_code)
        )
    """)

    conn.commit()
    conn.close()


# 실행 시 DB 자동 초기화
init_db()

