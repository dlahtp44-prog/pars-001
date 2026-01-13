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

# 1️⃣ 출발 로케이션 스캔 및 제품 선택 단계는 기존과 동일하게 유지하되, 
# 파라미터 전달의 안정성을 높였습니다.

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
    rows = [r for r in rows if int(r.get("qty", 0)) > 0]
    return templates.TemplateResponse(
        "m/move_select.html",
        {"request": request, "from_location": from_location, "rows": rows},
    )

# 2️⃣ 제품 선택 후 "도착지 스캔"으로 데이터를 넘기는 핵심 부분
@router.post("/select/submit")
def select_submit(
    from_location: str = Form(...),
    inventory_id: int = Form(...),
    qty_raw: str = Form(...),
    operator: str = Form(""),
    note: str = Form(""),
):
    try:
        qty = int(float(qty_raw.replace(",", "")))
    except:
        raise HTTPException(status_code=400, detail="수량 형식이 잘못되었습니다.")

    rows = query_inventory(location=from_location)
    row = next((r for r in rows if r.get("id") == inventory_id), None)

    if not row:
        raise HTTPException(status_code=404, detail="재고 정보를 찾을 수 없습니다.")

    # 쿼리 스트링으로 전달할 데이터 구성
    params = {
        "warehouse": row["warehouse"],
        "from_location": from_location,
        "brand": row["brand"],
        "item_code": row["item_code"],
        "item_name": row["item_name"],
        "lot": row.get("lot", ""),
        "spec": row.get("spec", ""),
        "qty": qty,
        "operator": operator,
        "note": note,
    }
    return RedirectResponse(url=f"/m/move/to?{urlencode(params)}", status_code=303)

# 3️⃣ [중요 수정] 도착지 스캔 화면 (422 오류 방지를 위해 모든 인자 명시)
@router.get("/to", response_class=HTMLResponse)
def to_scan(
    request: Request,
    warehouse: str,
    from_location: str,
    brand: str,
    item_code: str,
    item_name: str,
    qty: int,
    lot: Optional[str] = Query(""),
    spec: Optional[str] = Query(""),
    operator: Optional[str] = Query(""),
    note: Optional[str] = Query(""),
):
    # hidden field로 전달할 데이터 재구성
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
    return templates.TemplateResponse(
        "m/qr_scan.html",
        {
            "request": request,
            "title": "도착 로케이션 스캔",
            "desc": f"{item_name} ({qty}개) 이동 중",
            "action": "/m/move/to/submit",
            "hidden": params,
        },
    )

# 4️⃣ [중요 수정] 최종 이동 확정 (DB 반영)
@router.post("/to/submit")
def to_submit(
    request: Request,
    qrtext: str = Form(...),
    warehouse: str = Form(...),
    from_location: str = Form(...),
    brand: str = Form(...),
    item_code: str = Form(...),
    item_name: str = Form(...),
    qty: int = Form(...),
    lot: str = Form(""),
    spec: str = Form(""),
    operator: str = Form(""),
    note: str = Form(""),
):
    to_location = extract_location_only(qrtext)

    # A. 출발지 재고 차감
    upsert_inventory(
        warehouse=warehouse, location=from_location, brand=brand,
        item_code=item_code, item_name=item_name, lot=lot, spec=spec,
        qty_delta=-qty
    )

    # B. 도착지 재고 가산
    upsert_inventory(
        warehouse=warehouse, location=to_location, brand=brand,
        item_code=item_code, item_name=item_name, lot=lot, spec=spec,
        qty_delta=qty
    )

    # C. 이동 이력 저장
    add_history(
        type="이동", warehouse=warehouse, operator=operator,
        brand=brand, item_code=item_code, item_name=item_name,
        lot=lot, spec=spec, from_location=from_location,
        to_location=to_location, qty=qty, note=note
    )

    return templates.TemplateResponse(
        "m/move_done.html",
        {"request": request, "msg": f"{to_location}으로 이동 완료", "to_location": to_location}
    )
