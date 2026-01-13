from urllib.parse import urlencode

from fastapi import APIRouter, Form, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR
from app.db import query_inventory, upsert_inventory, add_history
from app.utils.qr_format import extract_location_only

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
router = APIRouter(prefix="/m/move", tags=["mobile-move"])


# =====================================================
# 시작
# =====================================================
@router.get("", response_class=HTMLResponse)
def start(request: Request):
    return templates.TemplateResponse("m/move_start.html", {"request": request})


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
    from_location = extract_location_only(qrtext)
    return RedirectResponse(
        url=f"/m/move/select?from_location={from_location}",
        status_code=303,
    )


# =====================================================
# 2️⃣ 제품 선택
# =====================================================
@router.get("/select", response_class=HTMLResponse)
def select_item(request: Request, from_location: str):
    rows = query_inventory(location=from_location)
    rows = [r for r in rows if int(r.get("qty", 0)) > 0]

    return templates.TemplateResponse(
        "m/move_select.html",
        {
            "request": request,
            "from_location": from_location,
            "rows": rows,
        },
    )


# =====================================================
# 2-1️⃣ 선택 확정
# =====================================================
@router.post("/select/submit")
def select_submit(
    from_location: str = Form(...),
    inventory_id: int = Form(...),
    qty_raw: str = Form(...),
    operator: str = Form(""),
    note: str = Form(""),
):
    # 수량 파싱
    try:
        qty = int(float(qty_raw.replace(",", ".")))
    except Exception:
        raise HTTPException(status_code=400, detail="수량 형식 오류")

    if qty <= 0:
        raise HTTPException(status_code=400, detail="수량은 0보다 커야 합니다")

    # 🔥 핵심 수정: id로 직접 조회 ❌ → 리스트에서 찾기 ✅
    rows = query_inventory(location=from_location)
    row = next((r for r in rows if r.get("id") == inventory_id), None)

    if not row:
        raise HTTPException(status_code=404, detail="재고를 찾을 수 없습니다")

    if qty > int(row["qty"]):
        raise HTTPException(status_code=400, detail="수량이 재고를 초과했습니다")

    params = {
        "warehouse": row["warehouse"],
        "from_location": from_location,
        "brand": row["brand"],
        "item_code": row["item_code"],
        "item_name": row["item_name"],
        "lot": row["lot"],
        "spec": row["spec"],
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
def to_scan(request: Request, **params):
    return templates.TemplateResponse(
        "m/qr_scan.html",
        {
            "request": request,
            "title": "도착 로케이션 스캔",
            "desc": "도착 로케이션 QR을 스캔하세요.",
            "action": "/m/move/to/submit",
            "hidden": params,
        },
    )


# =====================================================
# 4️⃣ 이동 확정
# =====================================================
@router.post("/to/submit", response_class=HTMLResponse)
def to_submit(
    request: Request,
    qrtext: str = Form(...),
    warehouse: str = Form(...),
    from_location: str = Form(...),
    brand: str = Form(...),
    item_code: str = Form(...),
    item_name: str = Form(...),
    lot: str = Form(...),
    spec: str = Form(...),
    qty: int = Form(...),
    operator: str = Form(""),
    note: str = Form(""),
):
    to_location = extract_location_only(qrtext)

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

    return templates.TemplateResponse(
        "m/move_done.html",
        {
            "request": request,
            "msg": "이동 완료",
            "to_location": to_location,
        },
    )
