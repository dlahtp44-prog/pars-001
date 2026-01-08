from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR
from app.utils.qr_format import (
    is_item_qr,
    extract_item_fields,
    extract_location_only,
)

router = APIRouter(prefix="/m/qr", tags=["mobile-qr"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("", response_class=HTMLResponse)
def qr_scan(request: Request):
    return templates.TemplateResponse(
        "m/qr_scan.html",
        {
            "request": request,
            "title": "QR 스캔",
            "desc": "로케이션 또는 제품 QR을 스캔하세요.",
            "action": "/m/qr/submit",
            "hidden": {},
        },
    )


@router.post("/submit")
def qr_submit(qrtext: str = Form(...)):
    qrtext = (qrtext or "").strip()
    if not qrtext:
        return RedirectResponse(url="/m/qr", status_code=303)

    # 1️⃣ 품목 QR
    if is_item_qr(qrtext):
        item_code, item_name, lot, spec, brand = extract_item_fields(qrtext)
        return RedirectResponse(
            url=(
                f"/m/inventory/detail"
                f"?item_code={item_code}"
                f"&lot={lot}"
                f"&spec={spec}"
                f"&brand={brand}"
            ),
            status_code=303,
        )

    # 2️⃣ 로케이션 QR
    location = extract_location_only(qrtext)
    if not location:
        # 잘못된 QR → 다시 스캔
        return RedirectResponse(url="/m/qr", status_code=303)

    return RedirectResponse(
        url=f"/m/qr/inventory?location={location}",
        status_code=303,
    )
