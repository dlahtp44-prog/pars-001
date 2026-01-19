from fastapi import APIRouter, Form, HTTPException
from decimal import Decimal, ROUND_HALF_UP

from app.db import (
    add_history,
    resolve_inventory_brand_and_name,
    upsert_inventory,
    rollback_history,
)

router = APIRouter(prefix="/api/move", tags=["move"])


# =====================================================
# UTILS
# =====================================================

def normalize_qty(value) -> float:
    """
    수량을 소수점 3자리까지 반올림하여 float로 반환
    """
    try:
        if value is None:
            raise ValueError

        s = str(value).strip()
        if s == "":
            raise ValueError

        d = Decimal(s).quantize(
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
# 이동 처리
# =====================================================

@router.post("")
def move(
    warehouse: str = Form(""),          # ✅ 필수 제거
    from_location: str = Form(""),      # ✅ 필수 제거
    to_location: str = Form(""),        # ✅ 필수 제거
    brand: str = Form(""),
    item_code: str = Form(""),          # ✅ 필수 제거
    item_name: str = Form(""),          # ✅ 필수 제거
    lot: str = Form(""),                # ✅ 필수 제거
    spec: str = Form(""),               # ✅ 필수 제거
    qty: float = Form(...),             # 🔥 수량만 필수
    note: str = Form(""),
    operator: str = Form(""),
):
    """
    ✅ 이동 처리
    - 창고/로케이션/품번/LOT/규격 없어도 이동 가능
    - 소수점 3자리 수량 지원
    - 출발/도착 동일 로케이션 차단
    - history 기록
    """

    qty_norm = normalize_qty(qty)

    if qty_norm <= 0:
        raise HTTPException(
            status_code=400,
            detail="이동 수량은 0보다 커야 합니다."
        )

    # 출발/도착 동일 로케이션 차단 (빈 값 포함)
    if (from_location or "").strip() == (to_location or "").strip():
        raise HTTPException(
            status_code=400,
            detail="출발/도착 로케이션이 동일합니다."
        )

    # 1️⃣ 브랜드 / 품명 자동 보정 (출발지 기준)
    try:
        resolved_brand, resolved_name = resolve_inventory_brand_and_name(
            warehouse=warehouse,
            location=from_location,
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

    # 2️⃣ 출발지 차감
    ok = upsert_inventory(
        warehouse=warehouse,
        location=from_location,
        brand=final_brand,
        item_code=item_code,
        item_name=final_name,
        lot=lot,
        spec=spec,
        qty_delta=-qty_norm,
        note=note,
    )
    if not ok:
        raise HTTPException(
            status_code=400,
            detail="출발지 재고가 부족하여 이동할 수 없습니다."
        )

    # 3️⃣ 도착지 가산
    upsert_inventory(
        warehouse=warehouse,
        location=to_location,
        brand=final_brand,
        item_code=item_code,
        item_name=final_name,
        lot=lot,
        spec=spec,
        qty_delta=qty_norm,
        note=note,
    )

    # 4️⃣ 이력 기록
    add_history(
        type="이동",
        warehouse=warehouse,
        operator=operator,
        brand=final_brand,
        item_code=item_code,
        item_name=final_name,
        lot=lot,
        spec=spec,
        from_location=from_location,
        to_location=to_location,
        qty=qty_norm,
        note=note,
    )

    return {
        "ok": True,
        "type": "이동",
        "qty": qty_norm,
    }


# =====================================================
# 이동 롤백
# =====================================================

@router.post("/rollback")
def move_rollback(
    history_id: int = Form(...),
    operator: str = Form(""),
    note: str = Form(""),
):
    """
    🔁 이동 롤백
    - history 기준
    - 도착지 차감 + 출발지 원복
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
            detail="이동 롤백 처리 중 오류가 발생했습니다."
        )

    return {
        "ok": True,
        "type": "이동 롤백",
        "history_id": history_id,
    }
