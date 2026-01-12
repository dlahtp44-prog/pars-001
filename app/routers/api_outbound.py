from fastapi import APIRouter, Form, HTTPException
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from app.db import (
    add_history,
    resolve_inventory_brand_and_name,
    upsert_inventory,
    rollback_history,
    get_inventory_one,   # ✅ STEP 3 핵심
)

router = APIRouter(prefix="/api/outbound", tags=["outbound"])


# =====================================================
# UTILS
# =====================================================

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
        raise HTTPException(
            status_code=400,
            detail="수량 형식이 올바르지 않습니다."
        )


# =====================================================
# 출고 처리 (운영 안정판)
# =====================================================

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
    ✅ 출고 처리 (STEP 3 반영)
    - 소수점 3자리 수량 지원
    - 서버 기준 재고 재검증 (동시 출고 방어)
    - 브랜드/품명 자동 보정
    - history 기록
    """

    # 0️⃣ 수량 정규화
    qty_norm = normalize_qty(qty)
    if qty_norm <= 0:
        raise HTTPException(
            status_code=400,
            detail="수량은 0보다 커야 합니다."
        )

    # 1️⃣ 브랜드 / 품명 자동 보정
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
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    final_brand = resolved_brand or (brand or "")
    final_name = item_name or resolved_name or ""

    # 2️⃣ 🔐 서버 기준 재고 재확인 (STEP 3 핵심)
    inv = get_inventory_one(
        warehouse=warehouse,
        location=location,
        brand=final_brand,
        item_code=item_code,
        lot=lot,
        spec=spec,
    )

    if not inv:
        raise HTTPException(
            status_code=409,
            detail="선택한 재고가 존재하지 않습니다. 새로고침 후 다시 선택하세요."
        )

    current_qty = float(inv["qty"])
    if qty_norm > current_qty:
        raise HTTPException(
            status_code=409,
            detail=f"출고 수량({qty_norm})이 현재고({current_qty})를 초과했습니다."
        )

    # 3️⃣ 재고 차감
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
        # 이 케이스는 동시 출고 등 극단 상황
        raise HTTPException(
            status_code=409,
            detail="재고가 변경되어 출고에 실패했습니다. 다시 시도하세요."
        )

    # 4️⃣ 이력 기록
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
        "type": "출고",
        "qty": qty_norm,
        "remain_qty": round(current_qty - qty_norm, 3),
    }


# =====================================================
# 출고 롤백 (기존 유지)
# =====================================================

@router.post("/rollback")
def outbound_rollback(
    history_id: int = Form(...),
    operator: str = Form(""),
    note: str = Form(""),
):
    """
    🔁 출고 롤백
    - history 기준
    - 재고 원복
    - 롤백 이력 history에 자동 기록
    """

    try:
        rollback_history(
            history_id=history_id,
            operator=operator,
            note=note,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="출고 롤백 처리 중 오류가 발생했습니다."
        )

    return {
        "ok": True,
        "type": "출고 롤백",
        "history_id": history_id,
    }
