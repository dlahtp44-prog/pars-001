from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR
from app.db import query_inventory
from app.utils.qr_format import extract_location_only   # 🔥 핵심

router = APIRouter()
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/m/qr/inventory", response_class=HTMLResponse)
def by_location(
    request: Request,
    location: str,
):
    """
    📱 모바일 QR 로케이션 재고 조회

    - QR 원문(location)을 그대로 받음
    - extract_location_only()로 정규화
    - 정규화된 location 기준으로 재고 조회
    """

    # 🔥 QR → 순수 로케이션 값 추출
    location_norm = extract_location_only(location)

    # 🔍 재고 조회
    rows = query_inventory(location=location_norm)

    return templates.TemplateResponse(
        "m/qr_inventory.html",
        {
            "request": request,
            "location": location_norm,   # 👈 화면/다음 단계용
            "rows": rows,
        }
    )
