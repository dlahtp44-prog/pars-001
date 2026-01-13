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


# =====================================================
# 시작
# =====================================================
@router.get("", response_class=HTMLResponse)
def start(request: Request):
    return templates.TemplateResponse("m/move_start.html", {"request": request})


# =====================================================
# 1) 출발 로케이션 스캔
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
def from_submit(request: Request, qrtext: str = Form(...)):
    from_location = extract_location_only(qrtext)

    # 이동 프로세스 시작 시 토큰/사용토큰 초기화(선택)
    request.session.pop("move_token", None)
    request.session.setdefault("used_move_tokens", [])

    return RedirectResponse(
        url=f"/m/move/select?from_location={from_location}",
        status_code=303,
    )


# =====================================================
# 2) 제품 선택
# =====================================================
@router.get("/select", response_class=HTMLResponse)
def select_item(request: Request, from_location: str):
    rows = query_inventory(location=from_location)
    rows = [r for r in rows if float(r.get("qty", 0) or 0) > 0]

    return templates.TemplateResponse(
        "m/move_select.html",
        {"request": request, "from_location": from_location, "rows": rows},
    )


# =====================================================
# 2-1) 선택 확정 → 도착지 스캔
# =====================================================
@router.post("/select/submit")
def select_submit(
    request: Request,
    from_location: str = Form(...),
    inventory_id: int = Form(...),
    qty_raw: str = Form(...),
    operator: str = Form(""),
    note: str = Form(""),
):
    # 수량 파싱
    try:
        qty = float(qty_raw.replace(",", ""))
    except Exception:
        raise HTTPException(400, "수량 형식 오류")

    if qty <= 0:
        raise HTTPException(400, "수량은 0보다 커야 합니다")

    # 재고 재확인 (id 필터는 query_inventory가 지원 안하므로 location에서 찾기)
    rows = query_inventory(location=from_location)
    row = next((r for r in rows if int(r.get("id", 0)) == int(inventory_id)), None)

    if not row:
        raise HTTPException(404, "재고를 찾을 수 없습니다")

    available = float(row.get("qty", 0) or 0)
    if qty > available:
        raise HTTPException(400, f"수량이 재고({available})를 초과했습니다")

    # ✅ 1회용 토큰 생성 후 세션 저장
    token = str(uuid.uuid4())
    request.session["move_token"] = token
    request.session.setdefault("used_move_tokens", [])

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


# =====================================================
# 3) 도착 로케이션 스캔
# =====================================================
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
            "desc": f"[{item_name}] {qty} 이동 - 도착 로케이션을 스캔하세요.",
            "action": "/m/move/to/submit",
            "hidden": hidden,
        },
    )


# =====================================================
# 4) 이동 확정 (중복 방지)
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
    qty: float = Form(...),
    token: str = Form(...),
    lot: str = Form(""),
    spec: str = Form(""),
    operator: str = Form(""),
    note: str = Form(""),
):
    to_location = extract_location_only(qrtext)

    if from_location == to_location:
        raise HTTPException(400, "출발지와 도착지가 동일합니다")

    # ✅ 세션 토큰 검증
    session_token = request.session.get("move_token")
    used_tokens = request.session.get("used_move_tokens", [])

    if not session_token or session_token != token:
        raise HTTPException(409, "유효하지 않은 이동 세션(토큰)입니다. 처음부터 다시 진행하세요.")

    if token in used_tokens:
        # 이미 처리됨 → 중복 실행 차단
        raise HTTPException(409, "이미 처리된 이동입니다(중복 요청 차단)")

    # 출발지 재고 재확인(안전)
    rows = query_inventory(
        warehouse=warehouse,
        location=from_location,
        brand=brand,
        item_code=item_code,
        lot=lot,
        spec=spec,
    )
    available = float(rows[0].get("qty", 0) or 0) if rows else 0.0
    if qty <= 0 or qty > available:
        raise HTTPException(400, f"출발지 재고 부족(현재 {available})")

    # ✅ 이동 실행
    clean_lot = (lot or "").strip()
    clean_spec = (spec or "").strip()

    upsert_inventory(warehouse, from_location, brand, item_code, item_name, clean_lot, clean_spec, -qty)
    upsert_inventory(warehouse, to_location, brand, item_code, item_name, clean_lot, clean_spec, qty)

    add_history(
        "이동",
        warehouse,
        operator,
        brand,
        item_code,
        item_name,
        clean_lot,
        clean_spec,
        from_location,
        to_location,
        qty,
        note,
    )

    # ✅ 토큰 사용 처리 (이제 재전송해도 막힘)
    used_tokens.append(token)
    request.session["used_move_tokens"] = used_tokens
    request.session.pop("move_token", None)

    return templates.TemplateResponse(
        "m/move_done.html",
        {"request": request, "msg": "재고 이동 완료", "to_location": to_location},
    )
