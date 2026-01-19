from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import date

from app.core.paths import TEMPLATES_DIR
from app.db import list_damage_codes

router = APIRouter(prefix="/damage", tags=["page-damage"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("", response_class=HTMLResponse)
def damage_page(
    request: Request,
    warehouse: str = "",
    location: str = "",
    brand: str = "",
    item_code: str = "",
    item_name: str = "",
    lot: str = "",
    spec: str = "",
):
    # -----------------------------
    # 오늘 날짜 (발생일 기본값)
    # -----------------------------
    request.state.today = date.today().isoformat()

    # -----------------------------
    # 파손 분류 코드 조회
    # -----------------------------
    damage_codes = list_damage_codes(active_only=True)

    return templates.TemplateResponse(
        "damage.html",
        {
            "request": request,
            # item info
            "warehouse": warehouse,
            "location": location,
            "brand": brand,
            "item_code": item_code,
            "item_name": item_name,
            "lot": lot,
            "spec": spec,
            # damage codes
            "damage_codes": damage_codes,
        },
    )
