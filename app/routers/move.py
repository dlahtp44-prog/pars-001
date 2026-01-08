from fastapi import APIRouter, HTTPException
from app.core.models import get_current_qty
from app.core.database import get_conn

router = APIRouter(prefix="/move", tags=["Move"])


@router.post("/")
def move(
    wh_from: str,
    loc_from: str,
    wh_to: str,
    loc_to: str,
    item_code: str,
    lot_no: str,
    qty: float,
    remark: str = "MOVE",
):
    if qty <= 0:
        raise HTTPException(400, "qty must be > 0")

    current = get_current_qty(wh_from, loc_from, item_code, lot_no)
    if qty > current:
        raise HTTPException(400, f"재고 부족 (현재고 {current})")

    conn = get_conn()
    cur = conn.cursor()

    # 출고
    cur.execute("""
        INSERT INTO inventory_tx
        (tx_type, warehouse, location, item_code, lot_no, qty, remark)
        VALUES ('MOVE', ?, ?, ?, ?, ?, ?)
    """, (wh_from, loc_from, item_code, lot_no, -abs(qty), remark + " OUT"))

    # 입고
    cur.execute("""
        INSERT INTO inventory_tx
        (tx_type, warehouse, location, item_code, lot_no, qty, remark)
        VALUES ('MOVE', ?, ?, ?, ?, ?, ?)
    """, (wh_to, loc_to, item_code, lot_no, qty, remark + " IN"))

    conn.commit()
    conn.close()

    return {"result": "OK"}

