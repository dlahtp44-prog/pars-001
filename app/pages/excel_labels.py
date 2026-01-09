from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.core.paths import TEMPLATES_DIR

import qrcode
import base64
from io import BytesIO

router = APIRouter(prefix="/page/labels", tags=["라벨"])

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# ============================
# 라벨 출력 센터
# ============================
@router.get("", response_class=HTMLResponse)
def labels_center(request: Request):
    return templates.TemplateResponse(
        "labels/label_center.html",
        {"request": request}
    )


# ============================
# 로케이션 라벨 출력 (QR 포함)
# ============================
@router.get("/location", response_class=HTMLResponse)
def location_label(request: Request, location: str):
    location = location.upper().strip()

    qr_text = f"LOCATION:{location}"

    qr = qrcode.make(qr_text)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    return templates.TemplateResponse(
        "labels/location_print.html",
        {
            "request": request,
            "location": location,
            "qr_base64": qr_base64,
        }
    )
