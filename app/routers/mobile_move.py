from fastapi import APIRouter, Request, Form, HTTPException
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
        "m/move_start.html",
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
        "m/move_select.html",
        {
            "request": request,
            "from_location": from_location,
            "rows": rows,
        },
    )


# -------------------------------------------------
# 4️⃣ 재고 선택 확정 → 도착 로케이션 스캔
#    🔥 하위 호환 처리 핵심 구간
# -------------------------------------------------
@router.post("/select/submit")
def move_select_submit(
    from_location: str = Form(...),

    # 🔹 신규 방식
    inventory_id: int | None = Form(None),
    qty_raw: str | None = Form(None),

    # 🔹 구버전(캐시/옛 HTML) 대응
    pick: str | None = Form(None),
    qty: float | None = Form(None),

    operator: str = Form(...),
    note: str = Form(""),
):
    """
    - 신규: inventory_id + qty_raw
    - 구버전: pick + qty
    둘 중 무엇이 와도 처리
    """

    # -----------------------------
    # inventory_id 결정
    # -----------------------------
    if inventory_id is None:
        if not pick:
            raise HTTPException(status_code=400, detail="제품 선택 누락")

        # 🔧 구버전 pick 포맷:
        # warehouse|||brand|||item_code|||item_name|||lot|||spec
        # → 여기서는 item_code 기준으로 재고를 찾는다고 가정
        try:
            parts = pick.split("|||")
            item_code = parts[2]
        except Exception:
            raise HTTPException(status_code=400, detail="제품 선택 형식 오류")

        # 🔍 현재 로케이션에서 item_code로 inventory 조회
        rows = query_inventory_by_location(from_location)
        matched = next((r for r in rows if r.item_code == item_code), None)

        if not matched:
            raise HTTPException(status_code=404, detail="선택한 재고를 찾을 수 없습니다")

        inventory_id = matched.id

    # -----------------------------
    # qty 결정
    # -----------------------------
    if qty is None:
        if not qty_raw:
            raise HTTPException(status_code=400, detail="이동 수량 누락")
        try:
            qty = float(qty_raw.replace(",", "."))
        except Exception:
            raise HTTPException(status_code=400, detail="이동 수량 형식 오류")

    if qty <= 0:
        raise HTTPException(status_code=400, detail="이동 수량은 0보다 커야 합니다")

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
        "m/move_to.html",
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
