from fastapi import APIRouter, Form, HTTPException
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

from app.db import (
    add_history,
    upsert_inventory,
    rollback_history,
)

router = APIRouter(prefix="/api/inbound", tags=["inbound"])


# =====================================================
# UTILS
# =====================================================

def normalize_qty(value) -> float:
    """
    수량 파싱 규칙 (엑셀/수기 공통)
    - 콤마 허용 (1,234.5)
    - 과학표기 허용 (1E-3)
    - 소수점 3자리 반올림
    """
    try:
        if value is None:
            raise ValueError

        s = str(value).strip()
        if s == "":
            raise ValueError

        # 콤마 제거
        s = s.replace(",", "")

        d = Decimal(s).quantize(
            Decimal("0.000"),
            rounding=ROUND_HALF_UP
        )
        return float(d)

    except (InvalidOperation, ValueError):
        raise HTTPException(
            status_code=400,
            detail="수량 형식이 올바르지 않습니다."
        )


# =====================================================
# 입고 처리
# =====================================================

@router.post("")
def inbound(
    warehouse: str = Form(""),     # ✅ 필수 제거
    location: str = Form(""),      # ✅ 필수 제거
    brand: str = Form(""),
    item_code: str = Form(""),     # ✅ 필수 제거
    item_name: str = Form(""),     # ✅ 필수 제거
    lot: str = Form(""),           # ✅ 필수 제거
    spec: str = Form(""),          # ✅ 필수 제거
    qty: float = Form(...),        # 🔥 수량만 필수
    note: str = Form(""),
    operator: str = Form(""),
):
    """
    ✅ 수기 입고 처리
    - 창고/로케이션/품번/LOT/규격 없어도 입고 가능
    - 소수점 3자리 수량 지원
    - 재고 반영
    - history 기록
    """

    qty_norm = normalize_qty(qty)

    if qty_norm <= 0:
        raise HTTPException(
            status_code=400,
            detail="수량은 0보다 커야 합니다."
        )

    # 1️⃣ 재고 반영
    ok = upsert_inventory(
        warehouse=warehouse,
        location=location,
        brand=brand,
        item_code=item_code,
        item_name=item_name,
        lot=lot,
        spec=spec,
        qty_delta=qty_norm,   # 🔥 소수점 그대로
        note=note,
    )
    if not ok:
        raise HTTPException(
            status_code=400,
            detail="입고 처리에 실패했습니다."
        )

    # 2️⃣ 이력 기록
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
        "type": "입고",
        "qty": qty_norm,
    }


# =====================================================
# 입고 롤백
# =====================================================

@router.post("/rollback")
def inbound_rollback(
    history_id: int = Form(...),
    operator: str = Form(""),
    note: str = Form(""),
):
    """
    🔁 입고 롤백
    - history 기준 롤백
    - 재고 원복
    - 롤백 이력 history에 기록됨
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
            detail="입고 롤백 처리 중 오류가 발생했습니다."
        )

    return {
        "ok": True,
        "type": "입고 롤백",
        "history_id": history_id,
    }
