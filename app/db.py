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
    return float(
        Decimal(str(val)).quantize(Decimal("0.000"), rounding=ROUND_HALF_UP)
    )


def _norm(v: Optional[str]) -> str:
    return (v or "").strip()


def _add_column_if_not_exists(cur, table: str, column: str, ddl: str):
    cur.execute(f"PRAGMA table_info({table})")
    cols = [r["name"] for r in cur.fetchall()]
    if column not in cols:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")


# =====================================================
# ADMIN
# =====================================================

def reset_inventory_and_history():
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM inventory")
        cur.execute("DELETE FROM history")
        conn.commit()
    finally:
        conn.close()


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
        # USERS
        # =====================
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        default_users = ["양동규","박상칠","김광현","이모세","인어진","user1"]
        now = datetime.now().isoformat(timespec="seconds")
        for u in default_users:
            cur.execute("""
                INSERT OR IGNORE INTO users (username, password, updated_at)
                VALUES (?, ?, ?)
            """, (_norm(u), "1234", now))

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

        # --- migration ---
        _add_column_if_not_exists(cur, "history", "batch_id", "batch_id TEXT")
        _add_column_if_not_exists(cur, "history", "rolled_back", "rolled_back INTEGER NOT NULL DEFAULT 0")
        _add_column_if_not_exists(cur, "history", "rollback_at", "rollback_at TEXT")
        _add_column_if_not_exists(cur, "history", "rollback_by", "rollback_by TEXT")
        _add_column_if_not_exists(cur, "history", "rollback_note", "rollback_note TEXT")

        conn.commit()  # 🔥 컬럼 먼저 확정

        cur.execute("CREATE INDEX IF NOT EXISTS idx_history_created ON history (created_at)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_history_batch ON history (batch_id)")

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
        # DAMAGE CODE SEED (안정판)
        # =====================
        cur.execute("DELETE FROM damage_codes")

        damage_seed = [
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
            ("사옥", "수작업", "이동", "사옥 내 이동 중 파손"),
            ("사옥", "수작업", "낙하", "사옥 내 낙하"),
            ("사옥", "수작업", "충격", "사옥 내 충격"),
            ("사옥", "보관", "적재 기준 미준수", "사옥 보관 중 적재 불량"),
            ("운송", "하차", "부주의", "하차 작업 중 부주의"),
            ("운송", "하차", "충격", "하차 중 충격"),
            ("운송", "운송", "사고", "운송 중 사고"),
            ("운송", "운송", "적재 불량", "차량 적재 불량"),
            ("하차지", "수작업", "이동", "하차지 이동 중 파손"),
            ("하차지", "수작업", "낙하", "하차지 낙하"),
            ("하차지", "수작업", "충격", "하차지 충격"),
            ("하차지", "지게차", "이동", "하차지 지게차 이동"),
            ("하차지", "지게차", "낙하", "하차지 지게차 낙하"),
            ("하차지", "지게차", "충격", "하차지 지게차 충돌"),
            ("하차지", "보관", "허용하중초과", "허용수치이상과적"),
            ("하차지", "보관", "적재 기준 미준수", "언패킹 불완전적재 벽에세워둠"),
            ("하차지", "보관", "장기적재", "장기간적재로인한 변형 누적"),
            ("하차지", "기타", "원인 불명", "하차지 원인 미확인"),
            ("가공공장", "제품", "재단 불량", "주문된규격과다르게재단"),
            ("가공공장", "제품", "제품 파손", "가공 중 제품 파손"),
            ("가공공장", "제품", "색상 불량", "색상 불량"),
            ("가공공장", "기타", "재단 불량", "기타 재단 불량"),
            ("원산지", "생산", "제품하자", "생산 공정 불량"),
            ("원자재", "생산", "충격보완미흡", "제품보호완충제 불량"),
            ("부산항", "지게차", "충격", "지게차 작업 중 손상"),
            ("입항", "운송보험", "충격", "운송중 손상"),
        ]

        cur.executemany("""
            INSERT INTO damage_codes (category, type, situation, description)
            VALUES (?, ?, ?, ?)
        """, damage_seed)

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
def get_inventory_one(
    warehouse, location, brand,
    item_code, lot, spec
) -> Optional[Dict[str, Any]]:
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM inventory
            WHERE warehouse=? AND location=? AND brand=?
              AND item_code=? AND lot=? AND spec=?
        """, (
            _norm(warehouse), _norm(location), _norm(brand),
            _norm(item_code), _norm(lot), _norm(spec)
        ))
        r = cur.fetchone()
        return dict(r) if r else None
    finally:
        conn.close()

def get_inventory_by_item_code(
    *, item_code: str, warehouse: str | None = None
) -> List[Dict[str, Any]]:
    """
    출고용 재고 조회
    - 품번 기준
    - qty > 0 인 현재고만
    - 로케이션/LOT/규격 선택용
    """
    conn = get_db()
    try:
        cur = conn.cursor()

        where = ["item_code = ?", "qty > 0"]
        params: list[Any] = [_norm(item_code)]

        if warehouse:
            where.append("warehouse = ?")
            params.append(_norm(warehouse))

        sql = f"""
            SELECT
                warehouse,
                location,
                brand,
                item_code,
                item_name,
                lot,
                spec,
                qty
            FROM inventory
            WHERE {" AND ".join(where)}
            ORDER BY
                warehouse,
                location,
                lot,
                spec
        """

        cur.execute(sql, params)
        rows = cur.fetchall()

        return [
            {
                "warehouse": r["warehouse"],
                "location": r["location"],
                "brand": r["brand"],
                "item_code": r["item_code"],
                "item_name": r["item_name"],
                "lot": r["lot"],
                "spec": r["spec"],
                "qty": _q3(r["qty"]),
            }
            for r in rows
        ]

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


def query_inventory(
    warehouse=None, location=None, brand=None,
    item_code=None, lot=None, spec=None,
    limit: int = 500
) -> list[dict]:
    conn = get_db()
    try:
        cur = conn.cursor()
        where, params = ["qty > 0"], []

        if warehouse:
            where.append("warehouse LIKE ?")
            params.append(f"%{_norm(warehouse)}%")

        if location:
            where.append("location LIKE ?")
            params.append(f"%{_norm(location)}%")

        if brand:
            where.append("brand = ?")
            params.append(_norm(brand))

        if item_code:
            where.append("item_code LIKE ?")
            params.append(f"%{_norm(item_code)}%")

        if lot:
            where.append("lot LIKE ?")
            params.append(f"%{_norm(lot)}%")

        if spec:
            where.append("spec LIKE ?")
            params.append(f"%{_norm(spec)}%")

        sql = """
            SELECT *
            FROM inventory
            WHERE {where}
            ORDER BY
                brand ASC,
                item_code ASC,
                location ASC,
                lot ASC,
                spec ASC
            LIMIT ?
        """.format(where=" AND ".join(where))

        params.append(limit)

        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]

    finally:
        conn.close()
def query_inventory_smart(q: str | None = None, limit: int = 1000):
    conn = get_db()
    try:
        cur = conn.cursor()

        where = ["qty > 0"]
        params = []

        if q:
            qn = _norm(q)

            if "-" in qn:  # 로케이션
                where.append("location LIKE ?")
                params.append(f"%{qn}%")

            elif qn.isdigit():  # 품번
                where.append("item_code LIKE ?")
                params.append(f"%{qn}%")

            elif any(c.isdigit() for c in qn):  # LOT
                where.append("lot LIKE ?")
                params.append(f"%{qn}%")

            else:  # 브랜드
                where.append("brand LIKE ?")
                params.append(f"%{qn}%")

        sql = f"""
            SELECT *
            FROM inventory
            WHERE {" AND ".join(where)}
            ORDER BY
              brand ASC,
              item_code ASC,
              location ASC,
              lot ASC,
              spec ASC
            LIMIT ?
        """
        params.append(limit)

        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()



# =====================================================
# HISTORY
# =====================================================

def add_history(
    type, warehouse, operator, brand, item_code, item_name,
    lot, spec, from_location, to_location, qty,
    note="", batch_id=None, dedup_seconds=5
):
    conn = get_db()
    try:
        cur = conn.cursor()
        now_dt = datetime.now()
        now = now_dt.isoformat(timespec="seconds")
        threshold = (now_dt - timedelta(seconds=dedup_seconds)).isoformat(timespec="seconds")

        cur.execute("""
            SELECT COUNT(*) FROM history
            WHERE type=? AND warehouse=? AND item_code=? AND lot=? AND spec=?
              AND from_location=? AND to_location=? AND qty=?
              AND created_at >= ?
        """, (
            _norm(type), _norm(warehouse), _norm(item_code),
            _norm(lot), _norm(spec),
            _norm(from_location), _norm(to_location),
            _q3(qty), threshold
        ))
        if cur.fetchone()[0] > 0:
            return

        cur.execute("PRAGMA table_info(history)")
        cols = {r["name"] for r in cur.fetchall()}

        if "batch_id" in cols:
            cur.execute("""
                INSERT INTO history
                (type, warehouse, operator, brand, item_code, item_name,
                 lot, spec, from_location, to_location, qty, note, batch_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                _norm(type), _norm(warehouse), _norm(operator), _norm(brand),
                _norm(item_code), _norm(item_name),
                _norm(lot), _norm(spec),
                _norm(from_location), _norm(to_location),
                _q3(qty), _norm(note), batch_id, now
            ))
        else:
            cur.execute("""
                INSERT INTO history
                (type, warehouse, operator, brand, item_code, item_name,
                 lot, spec, from_location, to_location, qty, note, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                _norm(type), _norm(warehouse), _norm(operator), _norm(brand),
                _norm(item_code), _norm(item_name),
                _norm(lot), _norm(spec),
                _norm(from_location), _norm(to_location),
                _q3(qty), _norm(note), now
            ))

        conn.commit()
    finally:
        conn.close()
def history_exists_by_token(token: str) -> bool:
    if not token:
        return False

    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute(
            "SELECT 1 FROM history WHERE token = ? LIMIT 1",
            (token,)
        )
        row = cur.fetchone()
        return row is not None
    except Exception:
        # token 컬럼이 없을 때 대비
        return False
    finally:
        conn.close()


# =====================================================
# ROLLBACK
# =====================================================

def rollback_history(history_id: int, operator: str, note: str = ""):
    """
    입고 / 출고 / 이동 롤백
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        now = datetime.now().isoformat(timespec="seconds")

        cur.execute(
            "SELECT * FROM history WHERE id=? AND rolled_back=0",
            (history_id,)
        )
        h = cur.fetchone()
        if not h:
            raise ValueError("이미 롤백되었거나 존재하지 않는 이력입니다.")

        if h["type"] not in ("입고", "출고", "이동"):
            raise ValueError("롤백 대상이 아닌 이력입니다.")

        qty = _q3(h["qty"])

        if h["type"] == "입고":
            ok = upsert_inventory(
                h["warehouse"], h["to_location"], h["brand"],
                h["item_code"], h["item_name"],
                h["lot"], h["spec"],
                -qty, note="입고 롤백"
            )
        elif h["type"] == "출고":
            ok = upsert_inventory(
                h["warehouse"], h["from_location"], h["brand"],
                h["item_code"], h["item_name"],
                h["lot"], h["spec"],
                qty, note="출고 롤백"
            )
        else:
            ok1 = upsert_inventory(
                h["warehouse"], h["to_location"], h["brand"],
                h["item_code"], h["item_name"],
                h["lot"], h["spec"],
                -qty, note="이동 롤백"
            )
            ok2 = upsert_inventory(
                h["warehouse"], h["from_location"], h["brand"],
                h["item_code"], h["item_name"],
                h["lot"], h["spec"],
                qty, note="이동 롤백"
            )
            ok = ok1 and ok2

        if not ok:
            raise ValueError("재고 롤백 실패")

        cur.execute("""
            UPDATE history
            SET rolled_back=1,
                rollback_at=?,
                rollback_by=?,
                rollback_note=?
            WHERE id=?
        """, (now, _norm(operator), _norm(note), history_id))

        cur.execute("""
            INSERT INTO history
            (type, warehouse, operator, brand,
             item_code, item_name, lot, spec,
             from_location, to_location,
             qty, note, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "롤백",
            h["warehouse"],
            _norm(operator),
            h["brand"],
            h["item_code"],
            h["item_name"],
            h["lot"],
            h["spec"],
            h["to_location"],
            h["from_location"],
            qty,
            f"원본ID:{h['id']} {note}",
            now
        ))

        conn.commit()
    finally:
        conn.close()

def rollback_batch(batch_id: str, operator: str, note: str = "") -> int:
    """
    엑셀(batch) 전체 롤백
    inventory는 품목별 합산 후 1회 처리
    """
    conn = get_db()
    try:
        cur = conn.cursor()

        cur.execute("""
            SELECT * FROM history
            WHERE batch_id = ?
              AND rolled_back = 0
              AND type = '입고'
        """, (batch_id,))
        rows = cur.fetchall()

        if not rows:
            return 0

        summary = {}
        for r in rows:
            key = (
                r["warehouse"],
                r["to_location"],
                r["brand"],
                r["item_code"],
                r["item_name"],
                r["lot"],
                r["spec"],
            )
            summary[key] = summary.get(key, 0) + r["qty"]

        for (
            warehouse, location, brand,
            item_code, item_name, lot, spec
        ), total_qty in summary.items():

            ok = upsert_inventory(
                warehouse, location, brand,
                item_code, item_name,
                lot, spec,
                -total_qty,
                note=f"배치롤백:{batch_id}"
            )
            if not ok:
                raise ValueError("배치 재고 롤백 실패")

        now = datetime.now().isoformat(timespec="seconds")
        cur.execute("""
            UPDATE history
            SET rolled_back = 1,
                rollback_at = ?,
                rollback_by = ?,
                rollback_note = ?
            WHERE batch_id = ?
        """, (now, operator, note, batch_id))

        conn.commit()
        return len(rows)

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


# =====================================================
# HISTORY QUERY (PAGE / EXCEL 공용)
# =====================================================

def query_history(
    *,
    limit: int = 300,
    year: int | None = None,
    month: int | None = None,
    day: int | None = None,
):
    conn = get_db()
    try:
        cur = conn.cursor()
        where, params = [], []

        if year and month and day:
            where.append("created_at LIKE ?")
            params.append(f"{year:04d}-{month:02d}-{day:02d}%")
        elif year and month:
            where.append("created_at LIKE ?")
            params.append(f"{year:04d}-{month:02d}%")
        elif year:
            where.append("created_at LIKE ?")
            params.append(f"{year:04d}%")

        sql = "SELECT * FROM history"
        if where:
            sql += " WHERE " + " AND ".join(where)

        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        conn.close()
        
def query_inventory_as_of(
    *,
    as_of_date: str,
    keyword: str | None = None,
):
    """
    기준일(as_of_date) 기준 재고 현황
    - history 테이블 기준
    - 기준일 23:59:59 까지의 입고 / 출고 누계
    """

    conn = get_db()
    try:
        cur = conn.cursor()

        where = []
        params = []

        # ✅ 기준일 끝 (해당 날짜까지 누계)
        where.append("h.created_at <= ?")
        params.append(f"{as_of_date} 23:59:59")

        # ✅ 통합 검색
        if keyword:
            kw = f"%{keyword}%"
            where.append(
                """
                (
                    h.warehouse LIKE ?
                    OR COALESCE(h.to_location, h.from_location) LIKE ?
                    OR h.brand LIKE ?
                    OR h.item_code LIKE ?
                    OR h.item_name LIKE ?
                    OR h.lot LIKE ?
                    OR h.spec LIKE ?
                )
                """
            )
            params.extend([kw] * 7)

        where_sql = " AND ".join(where)

        sql = f"""
        SELECT
            h.warehouse,
            COALESCE(h.to_location, h.from_location) AS location,
            h.brand,
            h.item_code,
            h.item_name,
            h.lot,
            h.spec,

            -- ✅ 입고 누계
            SUM(
                CASE
                    WHEN h.type = '입고' THEN h.qty
                    ELSE 0
                END
            ) AS inbound_qty,

            -- ✅ 출고 누계
            SUM(
                CASE
                    WHEN h.type = '출고' THEN h.qty
                    ELSE 0
                END
            ) AS outbound_qty,

            -- ✅ 현재고 = 입고 - 출고
            SUM(
                CASE
                    WHEN h.type = '입고' THEN h.qty
                    ELSE 0
                END
            )
            -
            SUM(
                CASE
                    WHEN h.type = '출고' THEN h.qty
                    ELSE 0
                END
            ) AS current_qty

        FROM history h
        WHERE {where_sql}

        GROUP BY
            h.warehouse,
            COALESCE(h.to_location, h.from_location),
            h.brand,
            h.item_code,
            h.item_name,
            h.lot,
            h.spec

        HAVING current_qty != 0

        ORDER BY
            h.warehouse,
            location,
            h.item_code
        """

        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]

    finally:
        conn.close()






# app/db.py 맨 아래에 추가

from app.utils.erp_verify import make_compare_key

def get_inventory_compare_rows(erp_rows: list[dict]) -> dict:
    """
    Returns:
      {
        "summary": {total, match, diff, wms_missing, erp_missing, rollup},
        "rows": [ {status, mode, item_code, lot, spec, erp_qty, wms_qty, diff, note} ... ]
      }
    """
    # 1) WMS inventory (합산)
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT item_code, lot, spec, SUM(qty) AS qty
            FROM inventory
            WHERE qty > 0
            GROUP BY item_code, lot, spec
            """
        )
        wms_raw = [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

    key_types = ["L3", "L2_LOT", "L2_SPEC", "L1"]
    erp_maps = {k: {} for k in key_types}
    wms_maps = {k: {} for k in key_types}
    erp_present: dict[str, set[str]] = {}
    wms_present: dict[str, set[str]] = {}

    def _add(maps, present, item_code: str, lot: str, spec: str, qty: float):
        item_code = _norm(item_code)
        lot = _norm(lot)
        spec = _norm(spec)
        if not item_code:
            return

        kt, key = make_compare_key(item_code, lot, spec)
        maps[kt][key] = float(maps[kt].get(key, 0.0)) + float(qty)
        present.setdefault(item_code, set()).add(kt)

        # rollup들 추가
        maps["L1"][(item_code,)] = float(maps["L1"].get((item_code,), 0.0)) + float(qty)
        present.setdefault(item_code, set()).add("L1")

        if lot:
            maps["L2_LOT"][(item_code, lot)] = float(maps["L2_LOT"].get((item_code, lot), 0.0)) + float(qty)
            present.setdefault(item_code, set()).add("L2_LOT")
        if spec:
            maps["L2_SPEC"][(item_code, spec)] = float(maps["L2_SPEC"].get((item_code, spec), 0.0)) + float(qty)
            present.setdefault(item_code, set()).add("L2_SPEC")
        if lot and spec:
            maps["L3"][(item_code, lot, spec)] = float(maps["L3"].get((item_code, lot, spec), 0.0)) + float(qty)
            present.setdefault(item_code, set()).add("L3")

    for r in erp_rows or []:
        _add(erp_maps, erp_present, r.get("item_code",""), r.get("lot",""), r.get("spec",""), float(r.get("qty") or 0))

    for r in wms_raw or []:
        _add(wms_maps, wms_present, r.get("item_code",""), r.get("lot",""), r.get("spec",""), float(r.get("qty") or 0))

    all_codes = sorted(set(erp_present.keys()) | set(wms_present.keys()))

    def choose_mode(code: str) -> str:
        e = erp_present.get(code, set())
        w = wms_present.get(code, set())
        if "L3" in e and "L3" in w:
            return "L3"
        if "L2_LOT" in e and "L2_LOT" in w:
            return "L2_LOT"
        if "L2_SPEC" in e and "L2_SPEC" in w:
            return "L2_SPEC"
        return "L1"

    summary = {"total": 0, "match": 0, "diff": 0, "wms_missing": 0, "erp_missing": 0, "rollup": 0}
    out_rows = []

    for code in all_codes:
        mode = choose_mode(code)
        e_types = erp_present.get(code, set())
        w_types = wms_present.get(code, set())

        did_rollup = (mode == "L1" and (e_types - {"L1"} or w_types - {"L1"}) and (e_types and w_types))

        # 해당 code에 대한 key set 추출
        def keys_for_code(m, mode_t):
            return {k for k in m[mode_t].keys() if k and k[0] == code}

        keys = keys_for_code(erp_maps, mode) | keys_for_code(wms_maps, mode)
        if not keys:
            continue

        for key in sorted(keys):
            erp_qty = float(erp_maps[mode].get(key, 0.0))
            wms_qty = float(wms_maps[mode].get(key, 0.0))
            diff = erp_qty - wms_qty

            lot = ""
            spec = ""
            if mode == "L3":
                _, lot, spec = key
            elif mode == "L2_LOT":
                _, lot = key
            elif mode == "L2_SPEC":
                _, spec = key

            if erp_qty > 0 and wms_qty > 0:
                if abs(diff) < 1e-9:
                    status = "✅ 일치"; summary["match"] += 1
                else:
                    status = "⚠️ 차이"; summary["diff"] += 1
            elif erp_qty > 0 and wms_qty == 0:
                status = "❌ WMS 없음"; summary["wms_missing"] += 1
            elif erp_qty == 0 and wms_qty > 0:
                status = "❌ ERP 없음"; summary["erp_missing"] += 1
            else:
                status = "—"

            note = "관리단위(LOT/규격) 불일치로 품번 단위 합산 비교" if did_rollup else ""
            if did_rollup:
                summary["rollup"] += 1

            out_rows.append({
                "status": status, "mode": mode, "item_code": code,
                "lot": lot, "spec": spec,
                "erp_qty": round(erp_qty, 3), "wms_qty": round(wms_qty, 3),
                "diff": round(diff, 3), "note": note
            })
            summary["total"] += 1

    return {"summary": summary, "rows": out_rows}
# =====================================================
# 출고 통계 (연 / 월 / 일)
# =====================================================
from datetime import datetime


def query_outbound_summary(year: int | None = None, month: int | None = None):
    """
    출고 통계 (일별 합계)
    year / month가 None이면 현재 연/월 자동 적용
    반환 예:
    [
        {"day": "2026-01-03", "total_qty": 12},
        {"day": "2026-01-10", "total_qty": 5},
    ]
    """

    # ✅ None 방어 처리 (페이지 직접 접근 대비)
    now = datetime.now()

    if year is None:
        year = now.year
    if month is None:
        month = now.month

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            substr(created_at, 1, 10) AS day,
            SUM(qty) AS total_qty
        FROM history
        WHERE
            type = 'OUT'
            AND strftime('%Y', created_at) = ?
            AND strftime('%m', created_at) = ?
        GROUP BY day
        ORDER BY day
        """,
        (str(year), f"{int(month):02d}")
    )

    rows = cur.fetchall()
    conn.close()

    return [
        {"day": row[0], "total_qty": row[1]}
        for row in rows
    ]


