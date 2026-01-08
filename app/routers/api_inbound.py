from fastapi import APIRouter, Form, HTTPException

from app.db import add_history, upsert_inventory

router = APIRouter(prefix="/api/inbound", tags=["inbound"])


@router.post("")
def inbound(
    warehouse: str = Form(...),
    location: str = Form(...),
    brand: str = Form(""),
    item_code: str = Form(...),
    item_name: str = Form(...),
    lot: str = Form(...),
    spec: str = Form(...),
    qty: float = Form(...),
    note: str = Form(""),
    operator: str = Form(""),
):
    """✅ 입고 처리 + 이력 기록"""
    if qty is None or float(qty) <= 0:
        raise HTTPException(status_code=400, detail="수량은 1 이상이어야 합니다.")

    ok = upsert_inventory(
        warehouse=warehouse,
        location=location,
        brand=brand,
        item_code=item_code,
        item_name=item_name,
        lot=lot,
        spec=spec,
        qty_delta=float(qty),
        note=note,
    )
    if not ok:
        raise HTTPException(status_code=400, detail="입고 처리에 실패했습니다.")

    add_history(
        type="입고",
        warehouse=warehouse,
        operator=operator,
        brand=brand,
        item_code=item_code,
        item_name=item_name,
        lot=lot,
        spec=spec,
        from_location="입고",
        to_location=location,
        qty=float(qty),
        note=note,
    )

    return {"ok": True}
