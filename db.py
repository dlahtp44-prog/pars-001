# app/db.py
import sqlite3
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Tuple

from app.core.paths import DB_PATH


# =====================================================
# DB CONNECTION
# =====================================================

def get_db() -> sqlite3.Connection:
    """
    SQLite 안전 연결
    - FastAPI 멀티스레드 대응
    - database is locked 방지
    """
    conn = sqlite3.connect(
        str(DB_PATH),
        timeout=10,
        check_same_thread=False,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 10000")
    return conn


# =====================================================
# UTILS
# =====================================================

def _norm(v: Optional[str]) -> str:
    return (v or "").strip()


def _q3(v) -> float:
    if v is None:
        return 0.0
    return float(Decimal(str(v)).quantize(Decimal("0.000"), rounding=ROUND_HALF_UP))


# =====================================================
# INIT / MIGRATION
# =====================================================

def init_db() -> None:
    conn = get_db()
    try:
        cur = conn.cursor()

        # INVENTORY
        # (기존 코드/페이지 호환 위해 note 컬럼 유지)
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

        # HISTORY (입고/출고/이동)
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

        # DAMAGE HISTORY (CS)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS damage_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            occurred_at TEXT NOT NULL,          -- 발생일(사용자 입력)
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
            created_at TEXT NOT NULL,           -- 등록시간(서버)
            FOREIGN KEY(damage_code_id) REFERENCES damage_codes(id)
        )
        """)

        # SEED DAMAGE CODES (1회)
        cur.execute("SELECT COUNT(*) FROM damage_codes")
        if cur.fetchone()[0] == 0:
            cur.executemany("""
            INSERT INTO damage_codes (category, type, situation, description)
            VALUES (?, ?, ?, ?)
            """, [
                ("물류", "수작업", "이동", "수작업 이동 중"),
                ("물류", "수작업", "낙하", "수작업 낙하"),
                ("물류", "지게차", "충격", "지게차 충돌"),
                ("운송", "하차", "부주의", "하차 중 파손"),
                ("가공", "업체", "불량", "가공 불량"),
            ])

        conn.commit()
    finally:
        conn.close()


# =====================================================
# INVENTORY CORE (단일 로직)
# =====================================================

def _upsert_inventory_with_conn(
    conn: sqlite3.Connection,
    warehouse: str,
    location: str,
    brand: str,
    item_code: str,
    item_name: str,
    lot: str,
    spec: str,
    qty_delta: float,
) -> bool:
    cur = conn.cursor()
    now = datetime.now().isoformat(timespec="seconds")
    delta = _q3(qty_delta)

    w, l, b, ic, iname, lt, sp = map(
        _norm, [warehouse, location, brand, item_code, item_name, lot, spec]
    )

    cur.execute("""
        SELECT id, qty FROM inventory
        WHERE warehouse=? AND location=? AND brand=? AND item_code=? AND lot=? AND spec=?
    """, (w, l, b, ic, lt, sp))
    row = cur.fetchone()

    if row:
        current = float(row["qty"])
        if delta < 0 and current < abs(delta):
            return False

        new_qty = _q3(current + delta)
        if new_qty <= 0:
            cur.execute("DELETE FROM inventory WHERE id=?", (row["id"],))
        else:
            cur.execute("""
                UPDATE inventory
                SET qty=?, updated_at=?
                WHERE id=?
            """, (new_qty, now, row["id"]))
    else:
        if delta <= 0:
            return False

        cur.execute("""
            INSERT INTO inventory
            (warehouse, location, brand, item_code, item_name, lot, spec, qty, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (w, l, b, ic, iname, lt, sp, delta, now))

    return True


# =====================================================
# INVENTORY PUBLIC ENTRY (엑셀 업로드 호환 최우선)
# - 기존 코드가 positional / keyword / **kwargs 어떤 방식이든 호출 가능하게 방어
# =====================================================

def upsert_inventory(*args, **kwargs) -> bool:
    """
    ✅ 재고 증감 단일 진입점
    - upsert_inventory(warehouse, location, brand, item_code, item_name, lot, spec, qty_delta)
    - upsert_inventory(warehouse=..., location=..., ..., qty_delta=...)
    - upsert_inventory(**row_dict)
    전부 지원 (엑셀 업로드에서 가장 많이 깨지는 부분 방어)
    """
    if args and kwargs:
        raise TypeError("upsert_inventory는 positional 또는 keyword 중 한 방식만 사용하세요.")

    if args:
        if len(args) != 8:
            raise TypeError(f"upsert_inventory positional 인자는 8개여야 합니다. (현재 {len(args)}개)")
        warehouse, location, brand, item_code, item_name, lot, spec, qty_delta = args
    else:
        warehouse = kwargs.get("warehouse", "")
        location = kwargs.get("location", "")
        brand = kwargs.get("brand", "")
        item_code = kwargs.get("item_code", "")
        item_name = kwargs.get("item_name", "")
        lot = kwargs.get("lot", "")
        spec = kwargs.get("spec", "")
        qty_delta = kwargs.get("qty_delta", 0)

    conn = get_db()
    try:
        ok = _upsert_inventory_with_conn(
            conn,
            warehouse=str(warehouse),
            location=str(location),
            brand=str(brand),
            item_code=str(item_code),
            item_name=str(item_name),
            lot=str(lot),
            spec=str(spec),
            qty_delta=float(qty_delta),
        )
        if ok:
            conn.commit()
        return ok
    finally:
        conn.close()


# =====================================================
# INVENTORY QUERY
# =====================================================

def query_inventory(
    warehouse: Optional[str] = None,
    location: Optional[str] = None,
    brand: Optional[str] = None,
    item_code: Optional[str] = None,
    lot: Optional[str] = None,
    spec: Optional[str] = None,
    limit: int = 500,
) -> List[Dict[str, Any]]:
    conn = get_db()
    try:
        cur = conn.cursor()
        where, params = ["qty > 0"], []

        if warehouse:
            where.append("warehouse=?"); params.append(_norm(warehouse))
        if location:
            where.append("location LIKE ?"); params.append(f"%{_norm(location)}%")
        if brand:
            where.append("brand=?"); params.append(_norm(brand))
        if item_code:
            where.append("item_code LIKE ?"); params.append(f"%{_norm(item_code)}%")
        if lot:
            where.append("lot LIKE ?"); params.append(f"%{_norm(lot)}%")
        if spec:
            where.append("spec LIKE ?"); params.append(f"%{_norm(spec)}%")

        sql = "SELECT * FROM inventory WHERE " + " AND ".join(where)
        sql += " ORDER BY updated_at DESC LIMIT ?"
        params.append(int(limit))

        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


# =====================================================
# BRAND / ITEM RESOLVE (이동 / 출고용)
# =====================================================

def resolve_inventory_brand_and_name(
    warehouse: str,
    location: str,
    item_code: str,
    lot: str,
    spec: str,
    brand: str = "",
) -> Tuple[str, str]:
    """
    이동 / 출고 시:
    - brand가 있으면 그 brand 기준으로 name 보정
    - brand가 없으면 inventory에서 단일 brand만 허용 (여러 개면 에러)
    """
    conn = get_db()
    try:
        cur = conn.cursor()

        if brand:
            cur.execute("""
            SELECT brand, item_name
            FROM inventory
            WHERE warehouse=? AND location=? AND brand=?
              AND item_code=? AND lot=? AND spec=?
            ORDER BY updated_at DESC LIMIT 1
            """, (
                _norm(warehouse), _norm(location), _norm(brand),
                _norm(item_code), _norm(lot), _norm(spec)
            ))
            r = cur.fetchone()
            return (r["brand"], r["item_name"]) if r else (_norm(brand), "")

        cur.execute("""
        SELECT DISTINCT brand, item_name
        FROM inventory
        WHERE warehouse=? AND location=?
          AND item_code=? AND lot=? AND spec=? AND qty > 0
        """, (
            _norm(warehouse), _norm(location),
            _norm(item_code), _norm(lot), _norm(spec)
        ))
        rows = cur.fetchall()

        if len(rows) == 1:
            return rows[0]["brand"], rows[0]["item_name"]
        if len(rows) == 0:
            return "", ""

        brands = ", ".join(sorted({r["brand"] for r in rows}))
        raise ValueError(f"브랜드가 여러 개입니다: {brands}")
    finally:
        conn.close()


# =====================================================
# HISTORY WRITE (입고/출고/이동)
# =====================================================

def add_history(
    type: str,
    warehouse: str,
    operator: str,
    brand: str,
    item_code: str,
    item_name: str,
    lot: str,
    spec: str,
    from_location: str,
    to_location: str,
    qty: float,
    note: str = "",
):
    conn = get_db()
    try:
        conn.execute("""
        INSERT INTO history
        (type, warehouse, operator, brand, item_code, item_name,
         lot, spec, from_location, to_location, qty, note, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            _norm(type), _norm(warehouse), _norm(operator), _norm(brand),
            _norm(item_code), _norm(item_name), _norm(lot), _norm(spec),
            _norm(from_location), _norm(to_location),
            _q3(qty), _norm(note),
            datetime.now().isoformat(timespec="seconds"),
        ))
        conn.commit()
    finally:
        conn.close()


# =====================================================
# HISTORY QUERY (기존 /page/history 호환용)
# - 기존 템플릿(history.html)에서 사용하는 컬럼 그대로 유지
# =====================================================

def query_history(
    year: Optional[int] = None,
    month: Optional[int] = None,
    day: Optional[int] = None,
    limit: int = 500,
) -> List[Dict[str, Any]]:
    conn = get_db()
    try:
        cur = conn.cursor()
        where, params = [], []

        if year:
            pat = f"{int(year):04d}"
            if month:
                pat += f"-{int(month):02d}"
                if day:
                    pat += f"-{int(day):02d}"
            where.append("created_at LIKE ?")
            params.append(f"{pat}%")

        sql = """
        SELECT
            h.*,
            CASE
                WHEN h.type='입고' THEN h.to_location
                ELSE h.from_location
            END AS location
        FROM history h
        """
        if where:
            sql += " WHERE " + " AND ".join(where)

        sql += " ORDER BY h.created_at DESC, h.id DESC LIMIT ?"
        params.append(int(limit))

        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


# =====================================================
# 통합 이력 (이동/출고/입고 + CS)
# - 기존 history.html 같은 테이블로도 출력 가능하도록 컬럼 맞춤
# =====================================================

def query_all_history(
    year: Optional[int] = None,
    month: Optional[int] = None,
    day: Optional[int] = None,
    limit: int = 500,
) -> List[Dict[str, Any]]:
    conn = get_db()
    try:
        cur = conn.cursor()
        where, params = [], []

        if year:
            pat = f"{int(year):04d}"
            if month:
                pat += f"-{int(month):02d}"
                if day:
                    pat += f"-{int(day):02d}"
            where.append("created_at LIKE ?")
            params.append(f"{pat}%")

        # ✅ history와 동일 컬럼셋으로 맞춤 (템플릿 재사용 가능)
        sql = """
        SELECT * FROM (
            SELECT
                created_at,
                type,
                warehouse,
                operator,
                brand,
                item_code,
                item_name,
                lot,
                spec,
                from_location,
                to_location,
                CASE WHEN type='입고' THEN to_location ELSE from_location END AS location,
                qty,
                note
            FROM history

            UNION ALL

            SELECT
                created_at,
                'CS' AS type,
                warehouse,
                '' AS operator,
                brand,
                item_code,
                item_name,
                lot,
                spec,
                '' AS from_location,
                '' AS to_location,
                location AS location,
                (qty * -1) AS qty,
                detail AS note
            FROM damage_history
        )
        """
        if where:
            sql += " WHERE " + " AND ".join(where)

        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(int(limit))

        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


# =====================================================
# DAMAGE CODE LIST
# =====================================================

def list_damage_codes(active_only: bool = True) -> List[Dict[str, Any]]:
    conn = get_db()
    try:
        sql = "SELECT * FROM damage_codes"
        if active_only:
            sql += " WHERE is_active=1"
        sql += " ORDER BY category, type, situation"
        cur = conn.execute(sql)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


# =====================================================
# DAMAGE HISTORY WRITE (CS / 파손 등록)
# =====================================================

def add_damage_history(
    occurred_at: str,
    warehouse: str,
    location: str,
    brand: str,
    item_code: str,
    item_name: str,
    lot: str,
    spec: str,
    qty: float,
    damage_code_id: int,
    detail: str = "",
    deduct_inventory: bool = False,
):
    """
    CS / 파손 이력 등록
    - 발생일(occurred_at): 사용자 입력값 (기본=오늘, 수정 가능 UX)
    - created_at: 서버 등록시간
    - deduct_inventory=True 인 경우 재고 차감까지 처리
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        now = datetime.now().isoformat(timespec="seconds")
        q = _q3(qty)

        cur.execute("""
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
        """, (
            _norm(occurred_at),
            _norm(warehouse),
            _norm(location),
            _norm(brand),
            _norm(item_code),
            _norm(item_name),
            _norm(lot),
            _norm(spec),
            q,
            int(damage_code_id),
            _norm(detail),
            now,
        ))

        if deduct_inventory:
            ok = _upsert_inventory_with_conn(
                conn,
                warehouse=warehouse,
                location=location,
                brand=brand,
                item_code=item_code,
                item_name=item_name,
                lot=lot,
                spec=spec,
                qty_delta=-q,
            )
            if not ok:
                raise ValueError("재고 부족으로 차감할 수 없습니다.")

        conn.commit()
    finally:
        conn.close()


# =====================================================
# DAMAGE HISTORY QUERY (페이지/리포트용 - 필요 시 사용)
# =====================================================

def query_damage_history(
    year: Optional[int] = None,
    month: Optional[int] = None,
    limit: int = 500,
) -> List[Dict[str, Any]]:
    conn = get_db()
    try:
        cur = conn.cursor()
        where, params = [], []

        if year:
            pat = f"{int(year):04d}"
            if month:
                pat += f"-{int(month):02d}"
            where.append("dh.occurred_at LIKE ?")
            params.append(f"{pat}%")

        sql = """
        SELECT
            dh.*,
            dc.category,
            dc.type AS damage_type,
            dc.situation
        FROM damage_history dh
        JOIN damage_codes dc ON dh.damage_code_id = dc.id
        """
        if where:
            sql += " WHERE " + " AND ".join(where)

        sql += " ORDER BY dh.occurred_at DESC, dh.id DESC LIMIT ?"
        params.append(int(limit))

        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def query_damage_summary_by_category(
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> List[Dict[str, Any]]:
    conn = get_db()
    try:
        cur = conn.cursor()
        where, params = [], []

        if year:
            pat = f"{int(year):04d}"
            if month:
                pat += f"-{int(month):02d}"
            where.append("dh.occurred_at LIKE ?")
            params.append(f"{pat}%")

        sql = """
        SELECT
            dc.category,
            COUNT(*) AS cnt
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
