from fastapi import APIRouter, Form, HTTPException
from decimal import Decimal, ROUND_HALF_UP

from app.db import (
    add_history,
    resolve_inventory_brand_and_name,
    upsert_inventory,
)

router = APIRouter(prefix="/api/outbound", tags=["outbound"])


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
def outbound(
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
    """
    ✅ 출고 처리 (소수점 3자리 지원)
    - 재고 부족 시 차단
    - 성공 시 history에 '출고' 기록
    - 브랜드 미입력 시 현재고에서 자동 보정(단, 후보 1개일 때만)
    """

    # ✅ 수량 정규화
    qty_norm = normalize_qty(qty)

    if qty_norm <= 0:
        raise HTTPException(status_code=400, detail="수량은 0보다 커야 합니다.")

    # 브랜드/품명 자동 보정 (브랜드 미입력 대응)
    try:
        resolved_brand, resolved_name = resolve_inventory_brand_and_name(
            warehouse=warehouse,
            location=location,
            item_code=item_code,
            lot=lot,
            spec=spec,
            brand=brand,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    final_brand = resolved_brand or (brand or "")
    final_name = item_name or resolved_name or ""

    # ✅ 재고 차감 (같은 수량 사용)
    ok = upsert_inventory(
        warehouse=warehouse,
        location=location,
        brand=final_brand,
        item_code=item_code,
        item_name=final_name,
        lot=lot,
        spec=spec,
        qty_delta=-qty_norm,
        note=note,
    )
    if not ok:
        raise HTTPException(status_code=400, detail="재고가 부족하여 출고할 수 없습니다.")

    # ✅ 이력 기록
    add_history(
        type="출고",
        warehouse=warehouse,
        operator=operator,
        brand=final_brand,
        item_code=item_code,
        item_name=final_name,
        lot=lot,
        spec=spec,
        from_location=location,
        to_location="출고",
        qty=qty_norm,
        note=note,
    )

    return {
        "ok": True,
        "qty": qty_norm,
    }
