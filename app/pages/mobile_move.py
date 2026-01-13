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


# 1) 출발 로케이션 스캔
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
def from_submit(request: Request, qrtext: str = Form(...)):
    from_location = extract_location_only(qrtext)
    
    # 프로세스 시작 시 이전 세션 정보 초기화
    request.session.pop("move_token", None)
    
    return RedirectResponse(
        url=f"/m/move/select?from_location={from_location}",
        status_code=303,
    )


# 2) 제품 선택
@router.get("/select", response_class=HTMLResponse)
def select_item(request: Request, from_location: str):
    rows = query_inventory(location=from_location)
    # 수량이 있는 것만 필터링
    rows = [r for r in rows if float(r.get("qty", 0) or 0) > 0]

    return templates.TemplateResponse(
        "m/move_select.html",
        {"request": request, "from_location": from_location, "rows": rows},
    )


# 2-1) 선택 확정 → 도착지 스캔 페이지로 이동
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
    except ValueError:
        raise HTTPException(400, "수량 형식이 올바르지 않습니다.")

    if qty <= 0:
        raise HTTPException(400, "이동 수량은 0보다 커야 합니다.")

    # 재고 확인
    rows = query_inventory(location=from_location)
    row = next((r for r in rows if int(r.get("id", 0)) == inventory_id), None)

    if not row:
        raise HTTPException(404, "선택한 재고 데이터를 찾을 수 없습니다.")

    available = float(row.get("qty", 0) or 0)
    if qty > available:
        raise HTTPException(400, f"이동 수량({qty})이 현재 재고({available})를 초과했습니다.")

    # 세션 기반 1회용 토큰 생성 (중복 처리 방지용)
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


# 3) 도착 로케이션 스캔
@router.get("/to", response_class=HTMLResponse)
def to_scan(
    request: Request,
    warehouse: str,
    from_location: str,
    brand: str,
    item_code: str,
    item_name: str,
    qty: float,
    token: str,
    lot: Optional[str] = Query(""),
    spec: Optional[str] = Query(""),
    operator: Optional[str] = Query(""),
    note: Optional[str] = Query(""),
):
    # GET으로 넘어온 토큰이 세션과 일치하는지 확인 (뒤로가기 방지)
    if request.session.get("move_token") != token:
        return HTMLResponse("유효하지 않거나 만료된 요청입니다. 처음부터 다시 시도해주세요. <br><a href='/m/move'>처음으로</a>", status_code=400)

    hidden = {
        "warehouse": warehouse,
        "from_location": from_location,
        "brand": brand,
        "item_code": item_code,
        "item_name": item_name,
        "lot": lot or "",
        "spec": spec or "",
        "qty": str(qty),
        "operator": operator or "",
        "note": note or "",
        "token": token,
    }

    return templates.TemplateResponse(
        "m/qr_scan.html",
        {
            "request": request,
            "title": "도착 로케이션 스캔",
            "desc": f"[{item_name}] {qty}개 이동 중 - 도착 로케이션 스캔",
            "action": "/m/move/to/submit",
            "hidden": hidden,
        },
    )


# 4) 이동 확정 처리
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

    # 1. 출발지/도착지 동일 여부
    if from_location == to_location:
        raise HTTPException(400, "출발지와 도착지가 같습니다.")

    # 2. 토큰 검증 (중복 제출 방지 핵심)
    session_token = request.session.get("move_token")
    if not session_token or session_token != token:
        raise HTTPException(409, "이미 처리되었거나 유효하지 않은 요청입니다.")

    # 3. 출발지 실시간 재고 재확인
    rows = query_inventory(
        warehouse=warehouse,
        location=from_location,
        brand=brand,
        item_code=item_code,
        lot=lot,
        spec=spec,
    )
    available = float(rows[0].get("qty", 0) or 0) if rows else 0.0
    if qty > available:
        raise HTTPException(400, f"이동 수량이 부족합니다. (현재 재고: {available})")

    # 4. DB 업데이트 실행
    clean_lot = (lot or "").strip()
    clean_spec = (spec or "").strip()

    upsert_inventory(warehouse, from_location, brand, item_code, item_name, clean_lot, clean_spec, -qty)
    upsert_inventory(warehouse, to_location, brand, item_code, item_name, clean_lot, clean_spec, qty)

    add_history(
        "이동", warehouse, operator, brand, item_code, item_name,
        clean_lot, clean_spec, from_location, to_location, qty, note
    )

    # 5. 토큰 파기 (성공 후 세션 삭제하여 중복 전송 차단)
    request.session.pop("move_token", None)

    return templates.TemplateResponse(
        "m/move_done.html",
        {"request": request, "msg": "재고 이동이 완료되었습니다.", "to_location": to_location},
    )
