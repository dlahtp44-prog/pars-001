# app/pages/damage.py
from datetime import date
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.db import list_damage_codes, add_damage_history

templates = Jinja2Templates(directory="app/templates")
router = APIRouter()

# =====================================================
# CS / 파손 등록 페이지
# =====================================================
@router.get("/damage", response_class=HTMLResponse)
def page_damage(request: Request):
    codes = list_damage_codes(active_only=True)

    return templates.TemplateResponse(
        "damage.html",
        {
            "request": request,
            "codes": codes,
            # ✅ 기본값 = 오늘 / 입력창에서 자유 수정
            "occurred_at": date.today().isoformat(),
            "msg": "",
        },
    )


# =====================================================
# CS / 파손 등록 처리
# =====================================================
@router.post("/damage")
def submit_damage(
    request: Request,
    occurred_at: str = Form(...),   # ✅ 사용자 입력값 그대로 사용
    warehouse: str = Form(""),
    location: str = Form(""),
    brand: str = Form(""),
    item_code: str = Form(""),
    item_name: str = Form(""),
    lot: str = Form(""),
    spec: str = Form(""),
    qty: float = Form(...),
    damage_code_id: int = Form(...),
    detail: str = Form(""),
    deduct_inventory: str = Form(""),
):
    # -------------------------------------------------
    # 체크박스 처리
    # -------------------------------------------------
    deduct = str(deduct_inventory).strip().lower() in ("1", "true", "on", "yes")

    # -------------------------------------------------
    # 수량 검증
    # -------------------------------------------------
    if qty <= 0:
        raise HTTPException(status_code=400, detail="수량은 1 이상이어야 합니다.")

    # -------------------------------------------------
    # 재고 차감 시 필수값 검증
    # -------------------------------------------------
    if deduct:
        missing = []
        if not warehouse:
            missing.append("창고")
        if not location:
            missing.append("로케이션")
        if not item_code:
            missing.append("품번")
        if not lot:
            missing.append("LOT")
        if not spec:
            missing.append("규격")

        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"재고 차감을 위해 다음 정보가 필요합니다: {', '.join(missing)}",
            )

    # -------------------------------------------------
    # CS / 파손 이력 기록
    #  - 발생일: 사용자 입력 그대로 저장
    #  - 재고 차감 여부: deduct_inventory로 제어
    # -------------------------------------------------
    add_damage_history(
        occurred_at=occurred_at,
        warehouse=warehouse,
        location=location,
        brand=brand,
        item_code=item_code,
        item_name=item_name,
        lot=lot,
        spec=spec,
        qty=qty,
        damage_code_id=damage_code_id,
        detail=detail,
        deduct_inventory=deduct,
    )

    return RedirectResponse(url="/damage/history", status_code=303)
