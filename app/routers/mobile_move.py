from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR
from app.db import (
    query_inventory_by_location,   # 로케이션별 재고 조회
    move_inventory,                # 실제 이동 처리
)

router = APIRouter(prefix="/m/move", tags=["mobile-move"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# -------------------------------------------------
# 1️⃣ 출발 로케이션 입력 / QR 진입
# -------------------------------------------------
@router.get("/from", response_class=HTMLResponse)
def move_from(request: Request, location: str = ""):
    return templates.TemplateResponse(
        "mobile/move_from.html",
        {
            "request": request,
            "from_location": location,
        },
    )


# -------------------------------------------------
# 2️⃣ 출발 로케이션 확정 → 재고 선택
# -------------------------------------------------
@router.post("/from/submit")
def move_from_submit(
    from_location: str = Form(...)
):
    return RedirectResponse(
        url=f"/m/move/select?from_location={from_location}",
        status_code=303,
    )


# -------------------------------------------------
# 3️⃣ 재고 선택 화면
# -------------------------------------------------
@router.get("/select", response_class=HTMLResponse)
def move_select(
    request: Request,
    from_location: str,
):
    rows = query_inventory_by_location(from_location)

    return templates.TemplateResponse(
        "mobile/move_select.html",
        {
            "request": request,
            "from_location": from_location,
            "rows": rows,
        },
    )


# -------------------------------------------------
# 4️⃣ 재고 선택 확정 → 도착 로케이션 스캔
# -------------------------------------------------
@router.post("/select/submit")
def move_select_submit(
    from_location: str = Form(...),
    inventory_id: int = Form(...),
    qty: float = Form(...),
    operator: str = Form(...),
    note: str = Form(""),
):
    return RedirectResponse(
        url=(
            "/m/move/to?"
            f"from_location={from_location}"
            f"&inventory_id={inventory_id}"
            f"&qty={qty}"
            f"&operator={operator}"
            f"&note={note}"
        ),
        status_code=303,
    )


# -------------------------------------------------
# 5️⃣ 도착 로케이션 QR 스캔
# -------------------------------------------------
@router.get("/to", response_class=HTMLResponse)
def move_to(
    request: Request,
    from_location: str,
    inventory_id: int,
    qty: float,
    operator: str,
    note: str = "",
):
    return templates.TemplateResponse(
        "mobile/move_to.html",
        {
            "request": request,
            "from_location": from_location,
            "inventory_id": inventory_id,
            "qty": qty,
            "operator": operator,
            "note": note,
        },
    )


# -------------------------------------------------
# 6️⃣ 이동 확정 (DB 반영)
# -------------------------------------------------
@router.post("/to/submit")
def move_to_submit(
    from_location: str = Form(...),
    to_location: str = Form(...),
    inventory_id: int = Form(...),
    qty: float = Form(...),
    operator: str = Form(...),
    note: str = Form(""),
):
    move_inventory(
        inventory_id=inventory_id,
        from_location=from_location,
        to_location=to_location,
        qty=qty,
        operator=operator,
        note=note,
    )

    return RedirectResponse(
        url="/m?msg=move_ok",
        status_code=303,
    )
