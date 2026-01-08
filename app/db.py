# app/db.py
import sqlite3
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Tuple

from app.core.paths import DB_PATH

# =====================================================
# DB CONNECTION & UTILS
# =====================================================

def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _q3(val) -> float:
    if val is None:
        return 0.0
    return float(Decimal(str(val)).quantize(Decimal("0.000"), rounding=ROUND_HALF_UP))


def _norm(v: Optional[str]) -> str:
    return (v or "").strip()


# =====================================================
# INIT / MIGRATION
# =====================================================

def init_db() -> None:
    conn = get_db()
    try:
        cur = conn.cursor()

        # INVENTORY
        cur.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                warehouse TEXT NOT NULL,
                location TEXT NOT NULL,
                brand TEXT NOT NULL DEFAULT '',
                item_code TEXT NOT NULL,
                item_name TEXT NOT NULL,
                lot TEXT NOT NULL,
                spec TEXT NOT NULL,
                qty REAL NOT NULL,
                note TEXT DEFAULT '',
                updated_at TEXT NOT NULL
            )
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_inventory_key
            ON inventory (warehouse, location, brand, item_code, lot, spec)
        """)

        # HISTORY
        cur.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                warehouse TEXT NOT NULL,
                operator TEXT NOT NULL DEFAULT '',
                brand TEXT NOT NULL DEFAULT '',
                item_code TEXT NOT NULL,
                item_name TEXT NOT NULL,
                lot TEXT NOT NULL,
                spec TEXT NOT NULL,
                from_location TEXT DEFAULT '',
                to_location TEXT DEFAULT '',
                qty REAL NOT NULL,
                note TEXT DEFAULT '',
                created_at TEXT NOT NULL
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_history_created ON history (created_at)")
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_history_key
            ON history (warehouse, item_code, lot, spec)
        """)

        # DAMAGE CODES
        cur.execute("""
            CREATE TABLE IF NOT EXISTS damage_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                type TEXT NOT NULL,
                situation TEXT NOT NULL,
                description TEXT DEFAULT '',
                is_active INTEGER NOT NULL DEFAULT 1
            )
        """)
        cur.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS ux_damage_codes_key
            ON damage_codes (category, type, situation)
        """)

        # DAMAGE HISTORY
        cur.execute("""
            CREATE TABLE IF NOT EXISTS damage_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                occurred_at TEXT NOT NULL,
                warehouse TEXT NOT NULL,
                location TEXT NOT NULL,
                brand TEXT NOT NULL DEFAULT '',
                item_code TEXT NOT NULL,
                item_name TEXT NOT NULL,
                lot TEXT NOT NULL,
                spec TEXT NOT NULL,
                qty REAL NOT NULL,
                damage_code_id INTEGER NOT NULL,
                detail TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                FOREIGN KEY(damage_code_id) REFERENCES damage_codes(id)
            )
        """)

        # DAMAGE CODE SEED
        cur.execute("SELECT COUNT(*) FROM damage_codes")
        if cur.fetchone()[0] == 0:
            cur.executemany("""
                INSERT INTO damage_codes (category, type, situation, description)
                VALUES (?, ?, ?, ?)
            """, [
                ("물류", "수작업", "이동", "수작업 이동 중 발생"),
                ("물류", "수작업", "낙하", "수작업 중 낙하"),
                ("물류", "지게차", "충격", "지게차 충돌"),
                ("운송", "하차", "부주의", "하차 중 파손"),
                ("가공", "업체", "불량", "가공 불량"),
            ])

        conn.commit()
    finally:
        conn.close()


# =====================================================
# INVENTORY HELPERS
# =====================================================

def _find_inventory_candidates(warehouse, location, item_code, lot, spec):
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM inventory
            WHERE warehouse=? AND location=? AND item_code=? AND lot=? AND spec=? AND qty > 0
        """, (_norm(warehouse), _norm(location), _norm(item_code), _norm(lot), _norm(spec)))
        return cur.fetchall()
    finally:
        conn.close()


def resolve_inventory_brand_and_name(warehouse, location, item_code, lot, spec, brand=""):
    brand_n = _norm(brand)
    if brand_n:
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT brand, item_name FROM inventory
                WHERE warehouse=? AND location=? AND brand=? AND item_code=? AND lot=? AND spec=?
                ORDER BY updated_at DESC LIMIT 1
            """, (_norm(warehouse), _norm(location), brand_n,
                  _norm(item_code), _norm(lot), _norm(spec)))
            r = cur.fetchone()
            return (r["brand"], r["item_name"]) if r else (brand_n, "")
        finally:
            conn.close()

    candidates = _find_inventory_candidates(warehouse, location, item_code, lot, spec)
    if len(candidates) == 1:
        return (candidates[0]["brand"], candidates[0]["item_name"])
    if not candidates:
        return ("", "")
    raise ValueError("브랜드가 여러 개입니다. 브랜드를 지정해 주세요.")


# =====================================================
# INVENTORY
# =====================================================

def query_inventory(**kwargs) -> List[Dict[str, Any]]:
    conn = get_db()
    try:
        cur = conn.cursor()
        where, params = ["qty > 0"], []
        for k, v in kwargs.items():
            if v:
                where.append(f"{k} LIKE ?")
                params.append(f"%{_norm(v)}%")
        sql = "SELECT * FROM inventory WHERE " + " AND ".join(where)
        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def upsert_inventory(warehouse, location, brand, item_code, item_name, lot, spec, qty_delta, note="") -> bool:
    conn = get_db()
    try:
        cur = conn.cursor()
        now = datetime.now().isoformat(timespec="seconds")
        delta = _q3(qty_delta)

        cur.execute("""
            SELECT id, qty FROM inventory
            WHERE warehouse=? AND location=? AND brand=? AND item_code=? AND lot=? AND spec=?
        """, (_norm(warehouse), _norm(location), _norm(brand),
              _norm(item_code), _norm(lot), _norm(spec)))
        row = cur.fetchone()

        if row:
            new_qty = _q3(float(row["qty"]) + delta)
            if new_qty <= 0:
                cur.execute("DELETE FROM inventory WHERE id=?", (row["id"],))
            else:
                cur.execute("UPDATE inventory SET qty=?, updated_at=? WHERE id=?",
                            (new_qty, now, row["id"]))
        else:
            if delta <= 0:
                return False
            cur.execute("""
                INSERT INTO inventory
                (warehouse, location, brand, item_code, item_name, lot, spec, qty, note, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (_norm(warehouse), _norm(location), _norm(brand),
                  _norm(item_code), _norm(item_name),
                  _norm(lot), _norm(spec), delta, _norm(note), now))

        conn.commit()
        return True
    finally:
        conn.close()


# =====================================================
# HISTORY
# =====================================================

def add_history(type, warehouse, operator, brand, item_code, item_name,
                lot, spec, from_location, to_location, qty, note="", dedup_seconds=5):
    conn = get_db()
    try:
        cur = conn.cursor()
        now = datetime.now().isoformat(timespec="seconds")
        cur.execute("""
            INSERT INTO history
            (type, warehouse, operator, brand, item_code, item_name, lot, spec,
             from_location, to_location, qty, note, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (_norm(type), _norm(warehouse), _norm(operator), _norm(brand),
              _norm(item_code), _norm(item_name), _norm(lot), _norm(spec),
              _norm(from_location), _norm(to_location), _q3(qty), _norm(note), now))
        conn.commit()
    finally:
        conn.close()


def query_history(year=None, month=None, day=None, limit=500):
    conn = get_db()
    try:
        cur = conn.cursor()
        sql = """
            SELECT h.*,
            CASE
                WHEN h.type='입고' THEN h.to_location
                WHEN h.type='출고' THEN h.from_location
                ELSE h.from_location
            END AS location
            FROM history h
            ORDER BY h.created_at DESC
            LIMIT ?
        """
        cur.execute(sql, (limit,))
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


# =====================================================
# DAMAGE / CS
# =====================================================

def list_damage_codes(**kwargs):
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM damage_codes WHERE is_active=1")
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def add_damage_history(
    *,
    occurred_at: str,
    warehouse: str,
    location: str,
    brand: str = "",
    item_code: str,
    item_name: str,
    lot: str,
    spec: str,
    qty: float,
    damage_code_id: int,
    detail: str = "",
    deduct_inventory: bool = False,
) -> None:
    """
    ✅ CS / 파손 등록 (API 호환 최종판)
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        now = datetime.now().isoformat(timespec="seconds")

        occurred_at_n = _norm(occurred_at) or now[:10]
        warehouse_n = _norm(warehouse)
        location_n = _norm(location)
        brand_n = _norm(brand)
        item_code_n = _norm(item_code)
        item_name_n = _norm(item_name)
        lot_n = _norm(lot)
        spec_n = _norm(spec)
        qty_n = _q3(qty)
        detail_n = _norm(detail)

        # 필수값 방어
        if not (warehouse_n and location_n and item_code_n and item_name_n and lot_n and spec_n):
            raise ValueError("CS/파손 필수 항목 누락")
        if qty_n <= 0:
            raise ValueError("수량은 1 이상이어야 합니다.")
        if damage_code_id <= 0:
            raise ValueError("파손 유형이 지정되지 않았습니다.")

        # 파손 이력 저장
        cur.execute(
            """
            INSERT INTO damage_history (
                occurred_at,
                warehouse,
                location,
                brand,
                item_code,
                item_name,
                lot,
                spec,
                qty,
                damage_code_id,
                detail,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                occurred_at_n,
                warehouse_n,
                location_n,
                brand_n,
                item_code_n,
                item_name_n,
                lot_n,
                spec_n,
                qty_n,
                damage_code_id,
                detail_n,
                now,
            ),
        )

        # 재고 차감 옵션
        if deduct_inventory:
            cur.execute(
                """
                SELECT id, qty FROM inventory
                WHERE warehouse=? AND location=? AND brand=?
                  AND item_code=? AND lot=? AND spec=?
                """,
                (
                    warehouse_n,
                    location_n,
                    brand_n,
                    item_code_n,
                    lot_n,
                    spec_n,
                ),
            )
            row = cur.fetchone()
            if not row or float(row["qty"]) < qty_n:
                raise ValueError("차감할 재고가 부족합니다.")

            remain = _q3(float(row["qty"]) - qty_n)
            if remain <= 0:
                cur.execute("DELETE FROM inventory WHERE id=?", (row["id"],))
            else:
                cur.execute(
                    "UPDATE inventory SET qty=?, updated_at=? WHERE id=?",
                    (remain, now, row["id"]),
                )

        conn.commit()
    finally:
        conn.close()



def query_damage_history(year=None, month=None, limit=500):
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT dh.*, dc.category, dc.type, dc.situation
            FROM damage_history dh
            JOIN damage_codes dc ON dh.damage_code_id = dc.id
            ORDER BY dh.occurred_at DESC
            LIMIT ?
        """, (limit,))
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def query_damage_summary_by_category(year=None, month=None):
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT dc.category, COUNT(*) AS cnt
            FROM damage_history dh
            JOIN damage_codes dc ON dh.damage_code_id = dc.id
            GROUP BY dc.category
            ORDER BY cnt DESC
        """)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
