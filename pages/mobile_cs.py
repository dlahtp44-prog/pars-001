from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import date

from app.core.paths import TEMPLATES_DIR
from app.db import list_damage_codes
from app.utils.qr_format import extract_item_fields

router = APIRouter(prefix="/m/cs", tags=["mobile-cs"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("", response_class=HTMLResponse)
def mobile_cs_page(
    request: Request,
    qr: str = "",          # QR 스캔 결과
    warehouse: str = "",
    location: str = "",
):
    # QR → 품목 정보 추출
    item_code, item_name, lot, spec, brand = ("", "", "", "", "")
    if qr:
        item_code, item_name, lot, spec, brand = extract_item_fields(qr)

    damage_codes = list_damage_codes(active_only=True)

    request.state.today = date.today().isoformat()

    return templates.TemplateResponse(
        "mobile_cs.html",
        {
            "request": request,
            "warehouse": warehouse,
            "location": location,
            "brand": brand,
            "item_code": item_code,
            "item_name": item_name,
            "lot": lot,
            "spec": spec,
            "damage_codes": damage_codes,
        },
    )
