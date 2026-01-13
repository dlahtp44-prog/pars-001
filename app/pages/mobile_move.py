from urllib.parse import urlencode
from typing import Optional
import uuid

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

# 1) 출발지 스캔
@router.get("/from", response_class=HTMLResponse)
def from_scan(request: Request):
    return templates.TemplateResponse("m/qr_scan.html", {
        "request": request,
        "title": "출발 로케이션 스캔",
        "desc": "출발지의 QR코드를 스캔하세요.",
        "action": "/m/move/from/submit",
        "hidden": {},
    })

@router.post("/from/submit")
def from_submit(request: Request, qrtext: str = Form(...)):
    from_location = extract_location_only(qrtext)
    # 세션 초기화 (새로운 이동 시작)
    request.session.pop("move_token", None)
    request.session.pop("last_moved_token", None) 
    
    return RedirectResponse(url=f"/m/move/select?from_location={from_location}", status_code=303)

# 2) 제품 및 수량 선택
@router.get("/select", response_class=HTMLResponse)
def select_item(request: Request, from_location: str):
    rows = query_inventory(location=from_location)
    rows = [r for r in rows if float(r.get("qty", 0) or 0) > 0]
    return templates.TemplateResponse("m/move_select.html", {
        "request": request, "from_location": from_location, "rows": rows
    })

@router.post("/select/submit")
def select_submit(
    request: Request,
    from_location: str = Form(...),
    inventory_id: int = Form(...),
    qty_raw: str = Form(...),
    operator: str = Form(""),
    note: str = Form(""),
):
    try:
        qty = float(qty_raw.replace(",", ""))
    except:
        raise HTTPException(400, "수량 입력 형식이 잘못되었습니다.")

    rows = query_inventory(location=from_location)
    row = next((r for r in rows if int(r.get("id", 0)) == inventory_id), None)
    if not row:
        raise HTTPException(404, "재고 정보를 찾을 수 없습니다.")

    # 1회용 전송 토큰 생성
    token = str(uuid.uuid4())
    request.session["move_token"] = token

    params = {
        "warehouse": row.get("warehouse", ""),
        "from_location": from_location,
        "brand": row.get("brand", ""),
        "item_code": row.get("item_code", ""),
        "item_name": row.get("item_name", ""),
        "lot": row.get("lot") or "",
        "spec": row.get("spec") or "",
        "qty": qty,
        "operator": operator,
        "note": note,
        "token": token,
    }
    return RedirectResponse(url=f"/m/move/to?{urlencode(params)}", status_code=303)

# 3) 도착지 스캔
@router.get("/to", response_class=HTMLResponse)
def to_scan(request: Request, token: str, item_name: str, qty: float):
    # 토큰이 만료되었거나 없을 경우 (이미 처리된 경우 포함)
    if request.session.get("move_token") != token:
        # 만약 방금 막 성공했다면 성공 페이지로, 아니라면 처음으로
        if request.session.get("last_moved_token") == token:
            return RedirectResponse(url="/m/move/done_page") # 아래에 정의
        return HTMLResponse("<script>alert('유효하지 않은 세션입니다. 처음부터 다시 시도하세요.'); location.href='/m/move';</script>")

    return templates.TemplateResponse("m/qr_scan.html", {
        "request": request,
        "title": "도착 로케이션 스캔",
        "desc": f"[{item_name}] {qty}개 이동 -> 도착지 스캔",
        "action": "/m/move/to/submit",
        "hidden": dict(request.query_params),
    })

# 4) 최종 이동 실행
@router.post("/to/submit")
def to_submit(
    request: Request,
    qrtext: str = Form(...),
    warehouse: str = Form(...),
    from_location: str = Form(...),
    brand: str = Form(...),
    item_code: str = Form(...),
    item_name: str = Form(...),
    qty: float = Form(...),
    token: str = Form(...),
    lot: str = Form(""),
    spec: str = Form(""),
    operator: str = Form(""),
    note: str = Form(""),
):
    to_location = extract_location_only(qrtext)
    if from_location == to_location:
        raise HTTPException(400, "출발지와 도착지가 동일합니다.")

    # 중복 체크: 이미 사용된 토큰인지 확인
    if request.session.get("move_token") != token:
        if request.session.get("last_moved_token") == token:
            # 이미 성공한 요청의 중복 클릭인 경우, 에러 대신 성공 페이지 재표시
            return RedirectResponse(url="/m/move/done_page", status_code=303)
        raise HTTPException(409, "이미 처리되었거나 유효하지 않은 요청입니다.")

    # 재고 차감 및 가산
    upsert_inventory(warehouse, from_location, brand, item_code, item_name, lot, spec, -qty)
    upsert_inventory(warehouse, to_location, brand, item_code, item_name, lot, spec, qty)
    add_history("이동", warehouse, operator, brand, item_code, item_name, lot, spec, from_location, to_location, qty, note)

    # 토큰 상태 변경 (사용 완료)
    request.session["last_moved_token"] = token
    request.session.pop("move_token", None)

    return RedirectResponse(url="/m/move/done_page", status_code=303)

@router.get("/done_page", response_class=HTMLResponse)
def done_page(request: Request):
    return templates.TemplateResponse("m/move_done.html", {
        "request": request, "msg": "재고 이동이 완료되었습니다."
    })
