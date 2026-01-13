from urllib.parse import urlencode

from fastapi import APIRouter, Form, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR
from app.db import (
    query_inventory,
    upsert_inventory,
    add_history,
)
from app.utils.qr_format import extract_location_only

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
router = APIRouter(prefix="/m/move", tags=["mobile-move"])


# =====================================================
# 시작 화면
# =====================================================
@router.get("", response_class=HTMLResponse)
def start(request: Request):
    return templates.TemplateResponse(
        "m/move_start.html",
        {"request": request},
    )


# =====================================================
# 1️⃣ 출발 로케이션 스캔
# =====================================================
@router.get("/from", response_class=HTMLResponse)
def from_scan(request: Request):
    return templates.TemplateResponse(
        "m/qr_scan.html",
        {
            "request": request,
            "title": "출발 로케이션 스캔",
            "desc": "출발 로케이션 QR을 스캔하세요.",
            "action": "/m/move/from/submit",
            "hidden": {},
        },
    )


@router.post("/from/submit")
def from_submit(qrtext: str = Form(...)):
    """
    QR 예:
    type=LOC&warehouse=MAIN&location=D01-01
    → D01-01
    """
    from_location = extract_location_only(qrtext)

    return RedirectResponse(
        url=f"/m/move/select?from_location={from_location}",
        status_code=303,
    )


# =====================================================
# 2️⃣ 제품 선택 + 수량 입력
# =====================================================
@router.get("/select", response_class=HTMLResponse)
def select_item(request: Request, from_location: str):
    from_location = (from_location or "").strip()

    rows = query_inventory(location=from_location)

    # 수량 있는 것만 표시
    rows = [
        r for r in rows
        if int(r.get("qty", 0) or 0) > 0
    ]

    return templates.TemplateResponse(
        "m/move_select.html",
        {
            "request": request,
            "from_location": from_location,
            "rows": rows,
        },
    )


# =====================================================
# 2-1️⃣ 제품 선택 확정
#   🔥 신/구 방식 동시 지원 핵심
# =====================================================
@router.post("/select/submit")
def select_submit(
    from_location: str = Form(...),

    # ✅ 신규 방식
    inventory_id: int | None = Form(None),
    qty_raw: str | None = Form(None),

    # ✅ 구버전 방식
    pick: str | None = Form(None),
    qty: int | None = Form(None),

    operator: str = Form(""),
    note: str = Form(""),
):
    from_location = (from_location or "").strip()
    operator = (operator or "").strip()
    note = (note or "").strip()

    # -------------------------
    # 수량 결정
    # -------------------------
    if qty is None:
        if not qty_raw:
            raise HTTPException(status_code=400, detail="이동 수량 누락")
        try:
            qty = int(float(qty_raw.replace(",", ".")))
        except Exception:
            raise HTTPException(status_code=400, detail="이동 수량 형식 오류")

    if qty <= 0:
        return RedirectResponse(
            url=f"/m/move/select?from_location={from_location}",
            status_code=303,
        )

    # -------------------------
    # inventory 식별
    # -------------------------
    if inventory_id is not None:
        # 🔹 신규 방식: inventory_id 기준
        rows = query_inventory(id=inventory_id)
        if not rows:
            raise HTTPException(status_code=404, detail="재고를 찾을 수 없습니다")

        r = rows[0]
        warehouse = r["warehouse"]
        brand = r["brand"]
        item_code = r["item_code"]
        item_name = r["item_name"]
        lot = r["lot"]
        spec = r["spec"]

    else:
        # 🔹 구버전 방식: pick 파싱
        if not pick:
            raise HTTPException(status_code=400, detail="제품 선택 누락")

        parts = pick.split("|||")
        if len(parts) != 6:
            return RedirectResponse(
                url=f"/m/move/select?from_location={from_location}",
                status_code=303,
            )

        warehouse, brand, item_code, item_name, lot, spec = [
            p.strip() for p in parts
        ]

        rows = query_inventory(
            warehouse=warehouse,
            location=from_location,
            brand=brand,
            item_code=item_code,
            lot=lot,
            spec=spec,
        )

        if not rows:
            raise HTTPException(status_code=404, detail="재고를 찾을 수 없습니다")

    available = int(rows[0].get("qty", 0)) if rows else 0

    if qty > available:
        return RedirectResponse(
            url=f"/m/move/select?from_location={from_location}",
            status_code=303,
        )

    params = {
        "warehouse": warehouse,
        "from_location": from_location,
        "brand": brand,
        "item_code": item_code,
        "item_name": item_name,
        "lot": lot,
        "spec": spec,
        "qty": qty,
        "operator": operator,
        "note": note,
    }

    return RedirectResponse(
        url=f"/m/move/to?{urlencode(params)}",
        status_code=303,
    )


# =====================================================
# 3️⃣ 도착 로케이션 스캔
# =====================================================
@router.get("/to", response_class=HTMLResponse)
def to_scan(
    request: Request,
    warehouse: str,
    from_location: str,
    brand: str,
    item_code: str,
    item_name: str,
    lot: str,
    spec: str,
    qty: int,
    operator: str = "",
    note: str = "",
):
    hidden = {
        "warehouse": warehouse,
        "from_location": from_location,
        "brand": brand,
        "item_code": item_code,
        "item_name": item_name,
        "lot": lot,
        "spec": spec,
        "qty": str(qty),
        "operator": operator,
        "note": note,
    }

    return templates.TemplateResponse(
        "m/qr_scan.html",
        {
            "request": request,
            "title": "도착 로케이션 스캔",
            "desc": "도착 로케이션 QR을 스캔하세요.",
            "action": "/m/move/to/submit",
            "hidden": hidden,
        },
    )


# =====================================================
# 4️⃣ 이동 확정 (DB 반영)
# =====================================================
@router.post("/to/submit", response_class=HTMLResponse)
def to_submit(
    request: Request,
    qrtext: str = Form(...),
    warehouse: str = Form(...),
    from_location: str = Form(...),
    brand: str = Form(""),
    item_code: str = Form(...),
    item_name: str = Form(...),
    lot: str = Form(...),
    spec: str = Form(...),
    qty: int = Form(...),
    operator: str = Form(""),
    note: str = Form(""),
):
    to_location = extract_location_only(qrtext)
    from_location = (from_location or "").strip()
    operator = (operator or "").strip()
    note = (note or "").strip()

    try:
        qty = int(qty)
    except Exception:
        qty = 0

    # 재고 재확인
    rows = query_inventory(
        warehouse=warehouse,
        location=from_location,
        brand=brand,
        item_code=item_code,
        lot=lot,
        spec=spec,
    )

    available = int(rows[0].get("qty", 0)) if rows else 0

    if qty <= 0 or qty > available:
        return RedirectResponse(
            url=f"/m/move/select?from_location={from_location}",
            status_code=303,
        )

    # 출발 -qty
    upsert_inventory(
        warehouse=warehouse,
        location=from_location,
        brand=brand,
        item_code=item_code,
        item_name=item_name,
        lot=lot,
        spec=spec,
        qty_delta=-qty,
        note=note,
    )

    # 도착 +qty
    upsert_inventory(
        warehouse=warehouse,
        location=to_location,
        brand=brand,
        item_code=item_code,
        item_name=item_name,
        lot=lot,
        spec=spec,
        qty_delta=qty,
        note=note,
    )

    # 이력 기록
    add_history(
        type="이동",
        warehouse=warehouse,
        operator=operator,
        brand=brand,
        item_code=item_code,
        item_name=item_name,
        lot=lot,
        spec=spec,
        from_location=from_location,
        to_location=to_location,
        qty=qty,
        note=note,
    )

    msg = (
        f"OK\n"
        f"- 창고: {warehouse}\n"
        f"- 출발: {from_location}\n"
        f"- 도착: {to_location}\n"
        f"- 브랜드: {brand}\n"
        f"- 품번: {item_code}\n"
        f"- LOT: {lot}\n"
        f"- 규격: {spec}\n"
        f"- 수량: {qty}\n"
    )

    return templates.TemplateResponse(
        "m/move_done.html",
        {
            "request": request,
            "msg": msg,
            "to_location": to_location,
        },
    )
