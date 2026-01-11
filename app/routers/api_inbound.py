from fastapi import APIRouter, Form, HTTPException
from decimal import Decimal, ROUND_HALF_UP

from app.db import add_history, upsert_inventory

router = APIRouter(prefix="/api/inbound", tags=["inbound"])


def normalize_qty(value) -> float:
    """
    수량을 소수점 3자리까지 반올림하여 float로 반환
    """
    try:
        d = Decimal(str(value)).quantize(
            Decimal("0.000"),
            rounding=ROUND_HALF_UP
        )
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
    """✅ 입고 처리 + 이력 기록 (소수점 3자리 지원)"""

    # ✅ 수량 정규화
    qty_norm = normalize_qty(qty)

    if qty_norm <= 0:
        raise HTTPException(status_code=400, detail="수량은 0보다 커야 합니다.")

    # ✅ 재고 반영
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

    # ✅ 이력 기록 (같은 수량 사용)
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

    return {
        "ok": True,
        "qty": qty_norm,
    }
