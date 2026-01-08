from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import re

from app.core.paths import TEMPLATES_DIR
from app.utils.qr_format import (
    is_item_qr,
    extract_item_fields,
    extract_location_only,
)

router = APIRouter(prefix="/m/qr", tags=["mobile-qr"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# =====================================================
# 유틸: 로케이션 검증
# =====================================================

_LOC_RE = re.compile(r"^[A-Za-z0-9\-_/]+$")

def _validate_location(raw: str) -> str:
    loc = (raw or "").strip()
    if not loc:
        return ""
    if any(x in loc for x in ["&", "?", "="]):
        return ""
    if len(loc) > 60:
        return ""
    if not _LOC_RE.match(loc):
        return ""
    return loc


# =====================================================
# 📸 QR 스캔 화면
# =====================================================

@router.get("", response_class=HTMLResponse)
def qr_scan(
    request: Request,
    mode: str = "",
    warehouse: str = "",
    msg: str = "",
):
    return templates.TemplateResponse(
        "m/qr_scan.html",
        {
            "request": request,
            "mode": mode,
            "warehouse": warehouse,
            "msg": msg,
        },
    )


# =====================================================
# ✅ QR 처리 (단일 진입점)
# =====================================================

@router.post("/submit")
def qr_submit(
    request: Request,
    qrtext: str = Form(...),
    mode: str = Form(""),
    warehouse: str = Form(""),
):
    qrtext = (qrtext or "").strip()

    if not qrtext:
        return qr_scan(
            request,
            mode=mode,
            warehouse=warehouse,
            msg="QR 값이 비어 있습니다.",
        )

    # 1️⃣ ITEM QR
    if is_item_qr(qrtext):
        if mode == "move":
            return qr_scan(
                request,
                mode=mode,
                warehouse=warehouse,
                msg="이동은 로케이션 QR만 가능합니다.",
            )

        item_code, item_name, lot, spec = extract_item_fields(qrtext)
        return RedirectResponse(
            url=(
                f"/m/inventory/detail"
                f"?item_code={item_code}&lot={lot}&spec={spec}"
            ),
            status_code=303,
        )

    # 2️⃣ LOCATION QR
    raw_location = extract_location_only(qrtext)
    location = _validate_location(raw_location)

    if not location:
        return qr_scan(
            request,
            mode=mode,
            warehouse=warehouse,
            msg="올바른 로케이션 QR이 아닙니다.",
        )

    # 3️⃣ 이동 모드
    if mode == "move":
        return RedirectResponse(
            url=f"/m/move/from?location={location}&warehouse={warehouse}",
            status_code=303,
        )

    # 4️⃣ 기본 → 로케이션 재고 조회
    return RedirectResponse(
        url=f"/m/qr/inventory?location={location}&warehouse={warehouse}",
        status_code=303,
    )
