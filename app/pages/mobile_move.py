from urllib.parse import urlencode
from typing import Optional

from fastapi import APIRouter, Form, Request, HTTPException, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR
from app.db import query_inventory, upsert_inventory, add_history
from app.utils.qr_format import extract_location_only

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
router = APIRouter(prefix="/m/move", tags=["mobile-move"])

@router.get("", response_class=HTMLResponse)
def start(request: Request):
    return templates.TemplateResponse("m/move_start.html", {"request": request})

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

@router.get("/select", response_class=HTMLResponse)
def select_item(request: Request, from_location: str):
    rows = query_inventory(location=from_location)
    # 소수점 재고가 0보다 큰 항목만 필터링
    rows = [r for r in rows if float(r.get("qty", 0)) > 0]

    return templates.TemplateResponse(
        "m/move_select.html",
        {"request": request, "from_location": from_location, "rows": rows},
    )

@router.post("/select/submit")
def select_submit(
    from_location: str = Form(...),
    inventory_id: int = Form(...),
    qty_raw: str = Form(...),
    operator: str = Form(""),
    note: str = Form(""),
):
    # 소수점 수량 파싱 (콤마 제거 후 float 변환)
    try:
        qty = float(qty_raw.replace(",", ""))
    except Exception:
        raise HTTPException(400, "수량 형식 오류")

    if qty <= 0:
        raise HTTPException(400, "수량은 0보다 커야 합니다")

    rows = query_inventory(location=from_location)
    row = next((r for r in rows if r["id"] == inventory_id), None)

    if not row:
        raise HTTPException(404, "재고를 찾을 수 없습니다")

    if qty > float(row["qty"]):
        raise HTTPException(400, f"수량이 재고({row['qty']})를 초과했습니다")

    params = {
        "warehouse": row["warehouse"],
        "from_location": from_location,
        "brand": row["brand"],
        "item_code": row["item_code"],
        "item_name": row["item_name"],
        "lot": row.get("lot") or "",
        "spec": row.get("spec") or "",
        "qty": qty,
        "operator": operator,
        "note": note,
    }
    return RedirectResponse(url=f"/m/move/to?{urlencode(params)}", status_code=303)

@router.get("/to", response_class=HTMLResponse)
def to_scan(
    request: Request,
    warehouse: str,
    from_location: str,
    brand: str,
    item_code: str,
    item_name: str,
    qty: float,
    lot: Optional[str] = Query(""),
    spec: Optional[str] = Query(""),
    operator: Optional[str] = Query(""),
    note: Optional[str] = Query(""),
):
    hidden = {
        "warehouse": warehouse, "from_location": from_location, "brand": brand,
        "item_code": item_code, "item_name": item_name, "lot": lot or "",
        "spec": spec or "", "qty": qty, "operator": operator or "", "note": note or "",
    }
    return templates.TemplateResponse(
        "m/qr_scan.html",
        {
            "request": request,
            "title": "도착 로케이션 스캔",
            "desc": f"[{item_name}] {qty} 이동",
            "action": "/m/move/to/submit",
            "hidden": hidden,
        },
    )

@router.post("/to/submit", response_class=HTMLResponse)
def to_submit(
    request: Request,
    qrtext: str = Form(...),
    warehouse: str = Form(...),
    from_location: str = Form(...),
    brand: str = Form(...),
    item_code: str = Form(...),
    item_name: str = Form(...),
    qty: float = Form(...),
    lot: str = Form(""),
    spec: str = Form(""),
    operator: str = Form(""),
    note: str = Form(""),
):
    to_location = extract_location_only(qrtext)
    if from_location == to_location:
        raise HTTPException(400, "출발지와 도착지가 동일합니다")

    clean_lot = lot.strip() if lot else ""
    clean_spec = spec.strip() if spec else ""

    # 출발지 차감 및 도착지 가산
    upsert_inventory(warehouse, from_location, brand, item_code, item_name, clean_lot, clean_spec, -qty)
    upsert_inventory(warehouse, to_location, brand, item_code, item_name, clean_lot, clean_spec, qty)
    
    add_history("이동", warehouse, operator, brand, item_code, item_name, clean_lot, clean_spec, 
                from_location, to_location, qty, note)

    return templates.TemplateResponse(
        "m/move_done.html",
        {"request": request, "msg": "재고 이동 완료", "to_location": to_location},
    )
