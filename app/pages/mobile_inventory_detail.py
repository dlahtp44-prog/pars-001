from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR
from app.db import query_inventory
from app.utils.qr_format import build_item_qr

router = APIRouter(prefix="/m", tags=["mobile-inventory"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/inventory/detail", response_class=HTMLResponse)
def inventory_detail(
    request: Request,
    item_code: str,
    lot: str,
    spec: str,
    brand: str = "",
):
    """
    📦 모바일 재고 상세
    - QR에서 진입
    - 동일 품번/LOT/규격 기준 현재고 표시
    """

    # 1️⃣ 재고 조회 (brand 있으면 포함, 없으면 전체)
    if brand:
        rows = query_inventory(
            item_code=item_code,
            lot=lot,
            spec=spec,
            brand=brand,
        )
    else:
        rows = query_inventory(
            item_code=item_code,
            lot=lot,
            spec=spec,
        )

    # 2️⃣ 대표 품명 / 브랜드 결정 (QR 생성용)
    item_name = ""
    final_brand = brand

    if rows:
        item_name = rows[0].get("item_name", "")
        final_brand = rows[0].get("brand", brand)

    # 3️⃣ QR 생성
    qr = build_item_qr(
        item_code=item_code,
        item_name=item_name,
        lot=lot,
        spec=spec,
        brand=final_brand,
    )

    return templates.TemplateResponse(
        "m/inventory_detail.html",
        {
            "request": request,
            "rows": rows,
            "item_code": item_code,
            "lot": lot,
            "spec": spec,
            "brand": final_brand,
            "qr": qr,
        },
    )
