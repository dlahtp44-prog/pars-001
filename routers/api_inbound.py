from __future__ import annotations

from fastapi import APIRouter, Form, HTTPException
from decimal import Decimal, ROUND_HALF_UP

from app.db import add_history, upsert_inventory, rollback_history

router = APIRouter(prefix="/api/inbound", tags=["inbound"])


def normalize_qty(value) -> float:
    """수량을 소수점 3자리까지 반올림하여 float로 반환"""
    try:
        d = Decimal(str(value)).quantize(Decimal("0.000"), rounding=ROUND_HALF_UP)
        return float(d)
    except Exception:
        raise HTTPException(status_code=400, detail="수량 형식이 올바르지 않습니다.")


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
    qty_norm = normalize_qty(qty)

    if qty_norm <= 0:
        raise HTTPException(status_code=400, detail="수량은 0보다 커야 합니다.")

    ok = upsert_inventory(
        warehouse=warehouse,
        location=location,
        brand=brand,
        item_code=item_code,
        item_name=item_name,
        lot=lot,
        spec=spec,
        qty_delta=qty_norm,
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
        qty=qty_norm,
        note=note,
    )

    return {"ok": True, "type": "입고", "qty": qty_norm}


@router.post("/rollback")
def inbound_rollback(
    history_id: int = Form(...),
    operator: str = Form(""),
    note: str = Form(""),
):
    try:
        rollback_history(history_id=history_id, operator=operator, note=note)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="입고 롤백 처리 중 오류가 발생했습니다.")

    return {"ok": True, "type": "입고 롤백", "history_id": history_id}
