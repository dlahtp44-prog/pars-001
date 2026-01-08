from fastapi import APIRouter, Form

from app.db import upsert_inventory, add_history

router = APIRouter(prefix="/api/outbound", tags=["출고"])


@router.post("")
def outbound(
    warehouse: str = Form(...),
    location: str = Form(...),
    brand: str = Form(""),
    item_code: str = Form(...),
    item_name: str = Form(""),
    lot: str = Form(...),
    spec: str = Form(...),
    qty: float = Form(...),
    operator: str = Form(""),
    note: str = Form(""),
):
    if qty <= 0:
        return {"ok": False, "msg": "출고 수량은 1 이상이어야 합니다."}

    ok = upsert_inventory(
        warehouse=warehouse,
        location=location,
        brand=brand,
        item_code=item_code,
        item_name=item_name,
        lot=lot,
        spec=spec,
        qty_delta=-qty,
        note=note or "출고",
    )

    if not ok:
        return {"ok": False, "msg": "재고가 부족하여 출고할 수 없습니다."}

    add_history(
        type="출고",
        warehouse=warehouse,
        operator=operator,
        brand=brand,
        item_code=item_code,
        item_name=item_name,
        lot=lot,
        spec=spec,
        from_location=location,
        to_location="",
        qty=qty,
        note=note or "출고",
    )

    return {"ok": True}
