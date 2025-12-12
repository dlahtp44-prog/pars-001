from .database import get_conn


def upsert_item(item_code: str, item_name: str = "", spec: str = ""):
    """
    품번/품명/규격 등록 또는 업데이트.
    """
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO items (item_code, item_name, spec)
        VALUES (?, ?, ?)
        ON CONFLICT(item_code)
        DO UPDATE SET
            item_name = COALESCE(?, item_name),
            spec = COALESCE(?, spec)
    """, (item_code, item_name, spec, item_name, spec))

    conn.commit()
    conn.close()


def get_current_qty(warehouse, location, item_code, lot_no):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT COALESCE(SUM(qty), 0) AS total
        FROM inventory_tx
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (warehouse, location, item_code, lot_no))

    row = cur.fetchone()
    conn.close()
    return float(row["total"]) if row else 0


def location_exists(warehouse: str, location: str) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT 1 FROM locations
        WHERE warehouse=? AND location=?
    """, (warehouse, location))

    exists = cur.fetchone()
    conn.close()
    return bool(exists)

