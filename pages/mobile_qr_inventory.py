from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR
from app.db import query_inventory
from app.utils.qr_format import extract_location_only

router = APIRouter()
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/m/qr/inventory", response_class=HTMLResponse)
def by_location(
    request: Request,
    location: str = "",
    warehouse: str = "",
):
    # 1️⃣ 로케이션 정제 (QR 쓰레기 방어)
    loc = extract_location_only(location)
    if not loc:
        return templates.TemplateResponse(
            "m/qr_inventory.html",
            {
                "request": request,
                "location": "",
                "rows": [],
                "msg": "로케이션 QR이 올바르지 않습니다.",
            },
        )

    # 2️⃣ 재고 조회 (현재고만, limit 충분히)
    rows = query_inventory(
        warehouse=warehouse or None,
        location=loc,
        limit=300,
    )

    # 3️⃣ 결과 렌더
    return templates.TemplateResponse(
        "m/qr_inventory.html",
        {
            "request": request,
            "location": loc,
            "rows": rows,
            "msg": "" if rows else "현재 재고가 없습니다.",
        },
    )
