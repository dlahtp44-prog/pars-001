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

        # =====================
        # INVENTORY
        # =====================
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

        # =====================
        # HISTORY
        # =====================
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
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_history_created ON history (created_at)"
        )

        # =====================
        # DAMAGE CODES
        # =====================
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

        # =====================
        # DAMAGE HISTORY
        # =====================
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

        # =====================
        # DAMAGE CODE SEED (🔥 안정판)
        # =====================
        cur.execute("DELETE FROM damage_codes")

        damage_seed = [
            # 물류
            ("물류", "수작업", "이동", "수작업 이동 중 파손"),
            ("물류", "수작업", "낙하", "수작업 중 낙하"),
            ("물류", "수작업", "충격", "수작업 중 외부 충격"),
            ("물류", "지게차", "이동", "지게차 이동 중 충돌"),
            ("물류", "지게차", "낙하", "지게차 작업 중 낙하"),
            ("물류", "지게차", "충격", "지게차 충돌"),
            ("물류", "보관", "적재 기준 미준수", "적재 기준 위반"),
            ("물류", "보관", "허용 하중 초과", "허용 하중 초과"),
            ("물류", "보관", "장기 적재", "장기 보관 중 파손"),
            ("물류", "기타", "원인 불명", "원인 미확인"),

            # 사옥
            ("사옥", "수작업", "이동", "사옥 내 이동 중 파손"),
            ("사옥", "수작업", "낙하", "사옥 내 낙하"),
            ("사옥", "수작업", "충격", "사옥 내 충격"),
            ("사옥", "보관", "적재 기준 미준수", "사옥 보관 중 적재 불량"),

            # 운송
            ("운송", "하차", "부주의", "하차 작업 중 부주의"),
            ("운송", "하차", "충격", "하차 중 충격"),
            ("운송", "운송", "사고", "운송 중 사고"),
            ("운송", "운송", "적재 불량", "차량 적재 불량"),

            # 하차지
            ("하차지", "수작업", "이동", "하차지 이동 중 파손"),
            ("하차지", "수작업", "낙하", "하차지 낙하"),
            ("하차지", "지게차", "충격", "하차지 지게차 충돌"),
            ("하차지", "보관", "적재 기준 미준수", "하차지 보관 중 적재 불량"),
            ("하차지", "기타", "원인 불명", "하차지 원인 미확인"),

            # 가공공장
            ("가공공장", "제품", "재단 불량", "재단 작업 중 불량"),
            ("가공공장", "제품", "제품 파손", "가공 중 제품 파손"),
            ("가공공장", "제품", "색상 불량", "색상 불량"),
            ("가공공장", "기타", "재단 불량", "기타 재단 불량"),

            # 원자재
            ("원자재", "생산", "출격 불량", "생산 공정 불량"),
            ("원자재", "생산", "적재 불량", "원자재 적재 불량"),

            # 부상
            ("부상", "지게차", "충격", "지게차 작업 중 부상"),
        ]

        cur.executemany("""
            INSERT INTO damage_codes (category, type, situation, description)
            VALUES (?, ?, ?, ?)
        """, damage_seed)

        conn.commit()

    finally:
        conn.close()


# =====================================================
# INVENTORY HELPERS
# =====================================================

def resolve_inventory_brand_and_name(
    warehouse, location, item_code, lot, spec, brand=""
) -> Tuple[str, str]:
    conn = get_db()
    try:
        cur = conn.cursor()
        brand_n = _norm(brand)

        if brand_n:
            cur.execute("""
                SELECT brand, item_name FROM inventory
                WHERE warehouse=? AND location=? AND brand=?
                  AND item_code=? AND lot=? AND spec=?
                ORDER BY updated_at DESC LIMIT 1
            """, (_norm(warehouse), _norm(location), brand_n,
                  _norm(item_code), _norm(lot), _norm(spec)))
            r = cur.fetchone()
            return (r["brand"], r["item_name"]) if r else (brand_n, "")

        cur.execute("""
            SELECT brand, item_name FROM inventory
            WHERE warehouse=? AND location=? AND item_code=? AND lot=? AND spec=? AND qty > 0
        """, (_norm(warehouse), _norm(location),
              _norm(item_code), _norm(lot), _norm(spec)))
        rows = cur.fetchall()

        if len(rows) == 1:
            return (rows[0]["brand"], rows[0]["item_name"])
        if not rows:
            return ("", "")
        raise ValueError("브랜드가 여러 개입니다. 브랜드를 지정해 주세요.")
    finally:
        conn.close()


# =====================================================
# INVENTORY
# =====================================================

def query_inventory(
    warehouse=None, location=None, brand=None,
    item_code=None, lot=None, spec=None,
    limit: int = 500
) -> List[Dict[str, Any]]:
    conn = get_db()
    try:
        cur = conn.cursor()
        where, params = ["qty > 0"], []

        if warehouse:
            where.append("warehouse LIKE ?"); params.append(f"%{_norm(warehouse)}%")
        if location:
            where.append("location LIKE ?"); params.append(f"%{_norm(location)}%")
        if brand:
            where.append("brand = ?"); params.append(_norm(brand))
        if item_code:
            where.append("item_code LIKE ?"); params.append(f"%{_norm(item_code)}%")
        if lot:
            where.append("lot LIKE ?"); params.append(f"%{_norm(lot)}%")
        if spec:
            where.append("spec LIKE ?"); params.append(f"%{_norm(spec)}%")

        sql = "SELECT * FROM inventory WHERE " + " AND ".join(where)
        sql += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)

        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def upsert_inventory(
    warehouse, location, brand, item_code, item_name,
    lot, spec, qty_delta, note=""
) -> bool:
    conn = get_db()
    try:
        cur = conn.cursor()
        now = datetime.now().isoformat(timespec="seconds")
        delta = _q3(qty_delta)

        cur.execute("""
            SELECT id, qty FROM inventory
            WHERE warehouse=? AND location=? AND brand=?
              AND item_code=? AND lot=? AND spec=?
        """, (_norm(warehouse), _norm(location), _norm(brand),
              _norm(item_code), _norm(lot), _norm(spec)))
        row = cur.fetchone()

        if row:
            new_qty = _q3(float(row["qty"]) + delta)
            if new_qty <= 0:
                cur.execute("DELETE FROM inventory WHERE id=?", (row["id"],))
            else:
                cur.execute("""
                    UPDATE inventory
                    SET qty=?, note=?, updated_at=?
                    WHERE id=?
                """, (new_qty, _norm(note), now, row["id"]))
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

def add_history(
    type, warehouse, operator, brand, item_code, item_name,
    lot, spec, from_location, to_location, qty,
    note="", dedup_seconds=5
):
    conn = get_db()
    try:
        cur = conn.cursor()
        now = datetime.now()
        threshold = (now - timedelta(seconds=dedup_seconds)).isoformat(timespec="seconds")

        cur.execute("""
            SELECT COUNT(*) FROM history
            WHERE type=? AND warehouse=? AND item_code=? AND lot=? AND spec=?
              AND from_location=? AND to_location=?
              AND created_at >= ?
        """, (_norm(type), _norm(warehouse), _norm(item_code),
              _norm(lot), _norm(spec),
              _norm(from_location), _norm(to_location), threshold))

        if cur.fetchone()[0] > 0:
            return

        cur.execute("""
            INSERT INTO history
            (type, warehouse, operator, brand, item_code, item_name, lot, spec,
             from_location, to_location, qty, note, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (_norm(type), _norm(warehouse), _norm(operator), _norm(brand),
              _norm(item_code), _norm(item_name), _norm(lot), _norm(spec),
              _norm(from_location), _norm(to_location),
              _q3(qty), _norm(note), now.isoformat(timespec="seconds")))

        conn.commit()
    finally:
        conn.close()


def query_history(year=None, month=None, day=None, limit=500):
    conn = get_db()
    try:
        cur = conn.cursor()
        where, params = [], []

        if year and month:
            pat = f"{int(year):04d}-{int(month):02d}"
            if day:
                pat += f"-{int(day):02d}"
            where.append("created_at LIKE ?")
            params.append(f"{pat}%")
        elif year:
            where.append("created_at LIKE ?")
            params.append(f"{int(year):04d}%")

        sql = """
            SELECT h.*,
            CASE
                WHEN h.type='입고' THEN h.to_location
                ELSE h.from_location
            END AS location
            FROM history h
        """
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY h.created_at DESC LIMIT ?"
        params.append(limit)

        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


# =====================================================
# DAMAGE / CS
# =====================================================

def list_damage_codes(
    *,
    category: str = "",
    type: str = "",
    situation: str = "",
    active_only: bool = True,
):
    conn = get_db()
    try:
        cur = conn.cursor()
        where, params = [], []

        if active_only:
            where.append("is_active=1")
        if category:
            where.append("category=?"); params.append(_norm(category))
        if type:
            where.append("type=?"); params.append(_norm(type))
        if situation:
            where.append("situation=?"); params.append(_norm(situation))

        sql = "SELECT * FROM damage_codes"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY category, type, situation"

        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def add_damage_history(
    *, occurred_at, warehouse, location, brand="",
    item_code, item_name, lot, spec,
    qty, damage_code_id, detail="", deduct_inventory=False
):
    conn = get_db()
    try:
        cur = conn.cursor()
        now = datetime.now().isoformat(timespec="seconds")

        brand_n, item_name_n = resolve_inventory_brand_and_name(
            warehouse, location, item_code, lot, spec, brand
        )

        cur.execute("""
            INSERT INTO damage_history (
                occurred_at, warehouse, location, brand,
                item_code, item_name, lot, spec,
                qty, damage_code_id, detail, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            _norm(occurred_at) or now[:10],
            _norm(warehouse), _norm(location), brand_n,
            _norm(item_code), item_name_n,
            _norm(lot), _norm(spec),
            _q3(qty), damage_code_id, _norm(detail), now
        ))

        if deduct_inventory:
            cur.execute("""
                SELECT id, qty FROM inventory
                WHERE warehouse=? AND location=? AND brand=?
                  AND item_code=? AND lot=? AND spec=?
            """, (_norm(warehouse), _norm(location), brand_n,
                  _norm(item_code), _norm(lot), _norm(spec)))
            r = cur.fetchone()
            if not r or float(r["qty"]) < qty:
                raise ValueError("차감할 재고가 부족합니다.")

            remain = _q3(float(r["qty"]) - qty)
            if remain <= 0:
                cur.execute("DELETE FROM inventory WHERE id=?", (r["id"],))
            else:
                cur.execute(
                    "UPDATE inventory SET qty=?, updated_at=? WHERE id=?",
                    (remain, now, r["id"])
                )

        conn.commit()
    finally:
        conn.close()


def query_damage_history(year=None, month=None, limit=500):
    conn = get_db()
    try:
        cur = conn.cursor()
        where, params = [], []

        if year and month:
            where.append("dh.occurred_at LIKE ?")
            params.append(f"{int(year):04d}-{int(month):02d}%")
        elif year:
            where.append("dh.occurred_at LIKE ?")
            params.append(f"{int(year):04d}%")

        sql = """
            SELECT dh.*, dc.category, dc.type, dc.situation
            FROM damage_history dh
            JOIN damage_codes dc ON dh.damage_code_id = dc.id
        """
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY dh.occurred_at DESC LIMIT ?"
        params.append(limit)

        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def query_damage_summary_by_category(year=None, month=None):
    conn = get_db()
    try:
        cur = conn.cursor()
        where, params = [], []

        if year and month:
            where.append("dh.occurred_at LIKE ?")
            params.append(f"{int(year):04d}-{int(month):02d}%")
        elif year:
            where.append("dh.occurred_at LIKE ?")
            params.append(f"{int(year):04d}%")

        sql = """
            SELECT dc.category, COUNT(*) AS cnt
            FROM damage_history dh
            JOIN damage_codes dc ON dh.damage_code_id = dc.id
        """
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " GROUP BY dc.category ORDER BY cnt DESC"

        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
