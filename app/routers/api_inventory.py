from fastapi import APIRouter, Query
from app.db import (
    query_inventory,
    get_inventory_by_item_code,
)
from app.utils.qr_format import is_item_qr, extract_item_fields

router = APIRouter(prefix="/api/inventory", tags=["api-inventory"])


# =====================================================
# 기본 재고 조회 (기존 유지)
# =====================================================
@router.get("")
def inventory(
    warehouse: str = "",
    location: str = "",
    brand: str = "",
    item_code: str = "",
    lot: str = "",
    spec: str = "",
):
    return {
        "rows": query_inventory(
            warehouse=warehouse,
            location=location,
            brand=brand,
            item_code=item_code,
            lot=lot,
            spec=spec,
        )
    }


# =====================================================
# QR 기반 재고 조회 (기존 유지)
# =====================================================
@router.get("/qr")
def inventory_by_qr(code: str = ""):
    """QR 값으로 재고 조회 (로케이션 QR 또는 품목 QR)."""
    code = (code or "").strip()
    if not code:
        return {"rows": []}

    # 품목 QR (브랜드 / 품번 / LOT / 규격)
    if is_item_qr(code):
        brand, item_code, _item_name, lot, spec = extract_item_fields(code)
        rows = query_inventory(
            brand=brand,
            item_code=item_code,
            lot=lot,
            spec=spec,
        )
        return {"rows": rows}

    # 기본: 로케이션 QR
    rows = query_inventory(location=code)
    return {"rows": rows}


# =====================================================
# 출고용 재고 조회 (STEP 1 신규)
# =====================================================
@router.get("/by-item")
def inventory_by_item(
    item_code: str = Query(..., min_length=1),
    warehouse: str | None = None,
):
    """
    출고 재고 선택용
    - 품번 기준
    - qty > 0 현재고만
    - 로케이션 / LOT / 규격 선택용
    """
    items = get_inventory_by_item_code(
        item_code=item_code,
        warehouse=warehouse,
    )

    return {
        "ok": True,
        "item_code": item_code,
        "count": len(items),
        "items": items,
    }
