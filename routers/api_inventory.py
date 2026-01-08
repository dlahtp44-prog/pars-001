from fastapi import APIRouter
from app.db import query_inventory
from app.utils.qr_format import is_item_qr, extract_item_fields

router = APIRouter(prefix="/api/inventory", tags=["api-inventory"])

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

from app.utils.qr_format import is_item_qr, extract_item_fields

@router.get("/qr")
def inventory_by_qr(code: str = ""):
    """QR 값으로 재고 조회 (로케이션 QR 또는 품목 QR)."""
    code = (code or "").strip()
    if not code:
        return {"rows": []}

    # 품목 QR(브랜드/품번/LOT/규격)
    if is_item_qr(code):
        brand, item_code, _item_name, lot, spec = extract_item_fields(code)
        rows = query_inventory(
            brand=brand,
            item_code=item_code,
            lot=lot,
            spec=spec,
        )
        return {"rows": rows}

    # 기본: 로케이션 코드
    rows = query_inventory(location=code)
    return {"rows": rows}
