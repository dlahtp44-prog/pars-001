
from fastapi import APIRouter, HTTPException
from app.core.models import upsert_item, get_current_qty
from app.core.database import get_conn

router = APIRouter(prefix="/inbound", tags=["Inbound"])


@router.post("/")
def inbound(
    warehouse: str,
    location: str,
    item_code: str,
    lot_no: str,
    qty: float,
    item_name: str = "",
    spec: str = "",
    remark: str = "IN",
):
    if qty <= 0:
        raise HTTPException(400, "qty must be greater than 0")

    conn = get_conn()
    cur = conn.cursor()

    # 품목 자동 등록
    upsert_item(item_code, item_name, spec)

    cur.execute("""
        INSERT INTO inventory_tx
        (tx_type, warehouse, location, item_code, lot_no, qty, remark)
        VALUES ('IN', ?, ?, ?, ?, ?, ?)
    """, (warehouse, location, item_code, lot_no, qty, remark))

    conn.commit()
    conn.close()

    new_qty = get_current_qty(warehouse, location, item_code, lot_no)

    return {"result": "OK", "after_qty": new_qty}
