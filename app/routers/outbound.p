from fastapi import APIRouter, HTTPException
from app.core.models import get_current_qty
from app.core.database import get_conn

router = APIRouter(prefix="/outbound", tags=["Outbound"])


@router.post("/")
def outbound(
    warehouse: str,
    location: str,
    item_code: str,
    lot_no: str,
    qty: float,
    remark: str = "OUT",
):
    if qty <= 0:
        raise HTTPException(400, "qty must be > 0")

    current = get_current_qty(warehouse, location, item_code, lot_no)
    if qty > current:
        raise HTTPException(400, f"재고 부족 (현재고: {current})")

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO inventory_tx
        (tx_type, warehouse, location, item_code, lot_no, qty, remark)
        VALUES ('OUT', ?, ?, ?, ?, ?, ?)
    """, (warehouse, location, item_code, lot_no, -abs(qty), remark))

    conn.commit()
    conn.close()

    return {"result": "OK", "after_qty": current - qty}

