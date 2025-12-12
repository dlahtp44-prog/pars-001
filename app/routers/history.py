from fastapi import APIRouter, HTTPException
from app.core.database import get_conn

router = APIRouter(prefix="/history", tags=["History"])


@router.get("/")
def get_history():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM inventory_tx
        ORDER BY id DESC
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    return rows


@router.post("/rollback")
def rollback(tx_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM inventory_tx WHERE id=?", (tx_id,))
    row = cur.fetchone()

    if not row:
        raise HTTPException(404, "기록 없음")

    qty = float(row["qty"])

    cur.execute("""
        INSERT INTO inventory_tx
        (tx_type, warehouse, location, item_code, lot_no, qty, remark)
        VALUES ('ROLLBACK', ?, ?, ?, ?, ?, ?)
    """, (
        row["warehouse"], row["location"], row["item_code"],
        row["lot_no"], -qty, f"ROLLBACK #{tx_id}"
    ))

    conn.commit()
    conn.close()

    return {"result": "OK"}

