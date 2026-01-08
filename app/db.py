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
    """DB 연결 생성 및 설정"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _q3(val) -> float:
    """소수점 3자리 반올림 고정 (부동소수점 오차 방지)"""
    if val is None:
        return 0.0
    return float(Decimal(str(val)).quantize(Decimal("0.000"), rounding=ROUND_HALF_UP))


def _norm(v: Optional[str]) -> str:
    """문자열 공백 제거 및 None 처리"""
    return (v or "").strip()


# =====================================================
# INIT / MIGRATION
# =====================================================

def init_db() -> None:
    """데이터베이스 테이블 및 인덱스 초기화"""
    conn = get_db()
    try:
        cur = conn.cursor()

        # 재고 테이블
        cur.execute(
            """
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
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_inventory_key ON inventory (warehouse, location, brand, item_code, lot, spec)"
        )

        # 일반 이력 테이블
        cur.execute(
            """
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
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_history_created ON history (created_at)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_history_key ON history (warehouse, item_code, lot, spec)")

        # 파손 코드 마스터
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS damage_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                type TEXT NOT NULL,
                situation TEXT NOT NULL,
                description TEXT DEFAULT '',
                is_active INTEGER NOT NULL DEFAULT 1
            )
            """
        )
        cur.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS ux_damage_codes_key ON damage_codes (category, type, situation)"
        )

        # 파손 발생 이력
        cur.execute(
            """
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
            """
        )

        # 초기 데이터 삽입 (1회)
        cur.execute("SELECT COUNT(*) FROM damage_codes")
        if cur.fetchone()[0] == 0:
            cur.executemany(
                """
                INSERT INTO damage_codes (category, type, situation, description)
                VALUES (?, ?, ?, ?)
                """,
                [
                    ("물류", "수작업", "이동", "수작업 이동 중 발생"),
                    ("물류", "수작업", "낙하", "수작업 중 낙하"),
                    ("물류", "지게차", "충격", "지게차 충돌"),
                    ("운송", "하차", "부주의", "하차 중 파손"),
                    ("가공", "업체", "불량", "가공 불량"),
                ],
            )

        conn.commit()
    finally:
        conn.close()


# =====================================================
# INVENTORY HELPERS
# =====================================================

def _find_inventory_candidates(
    warehouse: str,
    location: str,
    item_code: str,
    lot: str,
    spec: str,
) -> List[sqlite3.Row]:
    """brand 미입력 시 후보 검색 (qty>0만)"""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT * FROM inventory
            WHERE warehouse=? AND location=? AND item_code=? AND lot=? AND spec=? AND qty > 0
            """,
            (_norm(warehouse), _norm(location), _norm(item_code), _norm(lot), _norm(spec)),
        )
        return cur.fetchall()
    finally:
        conn.close()


def resolve_inventory_brand_and_name(
    warehouse: str,
    location: str,
    item_code: str,
    lot: str,
    spec: str,
    brand: str = "",
) -> Tuple[str, str]:
    """
    ✅ 브랜드/품명 자동 보정
    - brand가 비어있으면 inventory에서 (warehouse,location,item_code,lot,spec) 기준으로 탐색
    - 후보가 1개면 그 값을 사용
    - 후보가 0개면 없음
    - 후보가 2개 이상이면 모호 → 브랜드를 입력하라고 안내
    반환: (brand, item_name)
    """
    brand_n = _norm(brand)
    if brand_n:
        # brand가 있으면 item_name만 보정(빈 경우 대비)
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT brand, item_name FROM inventory
                WHERE warehouse=? AND location=? AND brand=? AND item_code=? AND lot=? AND spec=?
                ORDER BY updated_at DESC LIMIT 1
                """,
                (
                    _norm(warehouse),
                    _norm(location),
                    brand_n,
                    _norm(item_code),
                    _norm(lot),
                    _norm(spec),
                ),
            )
            r = cur.fetchone()
            if r:
                return (r["brand"], r["item_name"])
            return (brand_n, "")
        finally:
            conn.close()

    candidates = _find_inventory_candidates(warehouse, location, item_code, lot, spec)
    if len(candidates) == 1:
        r = candidates[0]
        return (r["brand"], r["item_name"])
    if len(candidates) == 0:
        return ("", "")
    # 2개 이상
    brands = sorted({(c["brand"] or "") for c in candidates})
    raise ValueError(f"브랜드가 여러 개입니다. 브랜드를 지정해 주세요: {', '.join(brands)}")


# =====================================================
# INVENTORY (현재고 & 안전 로직)
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
    """
    ✅ 현재고 조회
    - qty > 0만 반환 (현재고 현황에서 0 수량 제거)
    """
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


def upsert_inventory(
    warehouse: str,
    location: str,
    brand: str,
    item_code: str,
    item_name: str,
    lot: str,
    spec: str,
    qty_delta: float,
    note: str = "",
) -> bool:
    """
    ✅ 재고 증감 및 자동 정리
    - qty_delta < 0 (출고/이동출발) 시 현재고보다 많이 나갈 수 없도록 방어
    - 재고 0 이하 도달 시 해당 row 자동 삭제
    - 반환값: 성공 True / 재고 부족 등 실패 False
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        now = datetime.now().isoformat(timespec="seconds")
        delta = _q3(qty_delta)

        w, l, b, ic, iname, lt, sp = map(
            _norm, [warehouse, location, brand, item_code, item_name, lot, spec]
        )

        cur.execute(
            """
            SELECT id, qty FROM inventory
            WHERE warehouse=? AND location=? AND brand=? AND item_code=? AND lot=? AND spec=?
            """,
            (w, l, b, ic, lt, sp),
        )
        row = cur.fetchone()

        if row:
            current = float(row["qty"])
            if delta < 0 and current < abs(delta):
                return False  # 재고 부족
            new_qty = _q3(current + delta)
            if new_qty <= 0:
                cur.execute("DELETE FROM inventory WHERE id=?", (row["id"],))
            else:
                cur.execute(
                    "UPDATE inventory SET qty=?, note=?, updated_at=? WHERE id=?",
                    (new_qty, _norm(note), now, row["id"]),
                )
        else:
            # 신규 입고(+)만 생성 가능
            if delta <= 0:
                return False
            cur.execute(
                """
                INSERT INTO inventory
                (warehouse, location, brand, item_code, item_name, lot, spec, qty, note, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (w, l, b, ic, iname, lt, sp, delta, _norm(note), now),
            )

        conn.commit()
        return True
    finally:
        conn.close()


# =====================================================
# HISTORY (입고/출고/이동)
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
    dedup_seconds: int = 5,
) -> None:
    """✅ 입/출고/이동 이력 기록 (중복 방지 포함)"""
    conn = get_db()
    try:
        cur = conn.cursor()
        now = datetime.now()
        threshold = (now - timedelta(seconds=dedup_seconds)).isoformat(timespec="seconds")
        q = _q3(qty)

        cur.execute(
            """
            SELECT COUNT(*) FROM history
            WHERE type=? AND warehouse=? AND item_code=? AND lot=? AND spec=?
              AND from_location=? AND to_location=?
              AND ABS(qty - ?) < 0.0005
              AND created_at >= ?
            """,
            (
                _norm(type),
                _norm(warehouse),
                _norm(item_code),
                _norm(lot),
                _norm(spec),
                _norm(from_location),
                _norm(to_location),
                q,
                threshold,
            ),
        )
        if cur.fetchone()[0] > 0:
            return

        cur.execute(
            """
            INSERT INTO history
            (type, warehouse, operator, brand, item_code, item_name, lot, spec,
             from_location, to_location, qty, note, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                _norm(type),
                _norm(warehouse),
                _norm(operator),
                _norm(brand),
                _norm(item_code),
                _norm(item_name),
                _norm(lot),
                _norm(spec),
                _norm(from_location),
                _norm(to_location),
                q,
                _norm(note),
                now.isoformat(timespec="seconds"),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def query_history(
    year: Optional[int] = None,
    month: Optional[int] = None,
    day: Optional[int] = None,
    limit: int = 500,
) -> List[Dict[str, Any]]:
    """
    ✅ 통합 이력 조회
    - 템플릿에서 사용하는 r.location 제공:
      입고: to_location / 출고: from_location / 이동: from_location
    """
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
            where.append("created_at LIKE ?"); params.append(f"{pat}%")

        sql = """
            SELECT
                h.*,
                CASE
                    WHEN h.type='입고' THEN h.to_location
                    WHEN h.type='출고' THEN h.from_location
                    ELSE h.from_location
                END AS location
            FROM history h
        """
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY created_at DESC, id DESC LIMIT ?"
        params.append(int(limit))

        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


# =====================================================
# DAMAGE / CS
# =====================================================

def list_damage_codes(category: str = "", type: str = "", situation: str = "", active_only: bool = True) -> List[Dict[str, Any]]:
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


def add_damage_history(data: Dict[str, Any]) -> None:
    """파손 내역 기록"""
    conn = get_db()
    try:
        cur = conn.cursor()
        now = datetime.now().isoformat(timespec="seconds")
        cur.execute(
            """
            INSERT INTO damage_history (
                occurred_at, warehouse, location, brand, item_code,
                item_name, lot, spec, qty, damage_code_id, detail, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                _norm(data.get("occurred_at", "")),
                _norm(data.get("warehouse", "")),
                _norm(data.get("location", "")),
                _norm(data.get("brand", "")),
                _norm(data.get("item_code", "")),
                _norm(data.get("item_name", "")),
                _norm(data.get("lot", "")),
                _norm(data.get("spec", "")),
                _q3(data.get("qty", 0)),
                int(data.get("damage_code_id", 0)),
                _norm(data.get("detail", "")),
                now,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def query_damage_history(year: Optional[int] = None, month: Optional[int] = None, limit: int = 500) -> List[Dict[str, Any]]:
    conn = get_db()
    try:
        cur = conn.cursor()
        where, params = [], []
        if year:
            pat = f"{int(year):04d}"
            if month:
                pat += f"-{int(month):02d}"
            where.append("dh.occurred_at LIKE ?"); params.append(f"{pat}%")

        sql = """
            SELECT dh.*, dc.category, dc.type, dc.situation
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


def query_damage_summary_by_category(year: Optional[int] = None, month: Optional[int] = None) -> List[Dict[str, Any]]:
    """파손 통계 요약 (카테고리별)"""
    conn = get_db()
    try:
        cur = conn.cursor()
        where, params = [], []
        if year:
            pat = f"{int(year):04d}"
            if month:
                pat += f"-{int(month):02d}"
            where.append("dh.occurred_at LIKE ?"); params.append(f"{pat}%")

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
