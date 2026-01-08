from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR
from app.db import (
    query_inventory,
    upsert_inventory,
    add_history,
    resolve_inventory_brand_and_name,
)

# 페이지 라우터
router = APIRouter(prefix="/page/move", tags=["page-move"])

# 템플릿 경로
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("", response_class=HTMLResponse)
def move_page(
    request: Request,
    warehouse: str = "",
    location: str = "",
    msg: str = "",
):
    """
    이동 페이지 렌더링
    """
    rows = []
    if warehouse and location:
        rows = query_inventory(
            warehouse=warehouse,
            location=location,
            limit=200,
        )

    return templates.TemplateResponse(
        # ✅ FIX: 잘못된 pages/move.html → move.html
        "move.html",
        {
            "request": request,
            "warehouse": warehouse,
            "location": location,
            "rows": rows,
            "msg": msg,
        },
    )


@router.post("/do")
def move_do(
    warehouse: str = Form(...),
    from_location: str = Form(...),
    to_location: str = Form(...),
    brand: str = Form(""),
    item_code: str = Form(...),
    item_name: str = Form(""),
    lot: str = Form(...),
    spec: str = Form(...),
    qty: float = Form(...),
    operator: str = Form(""),
    note: str = Form(""),
):
    """
    재고 이동 처리
    """

    # 수량 체크
    if qty <= 0:
        return RedirectResponse(
            url=f"/page/move?warehouse={warehouse}&location={from_location}&msg=이동_수량은_1_이상",
            status_code=303,
        )

    # 동일 로케이션 이동 방지
    if from_location == to_location:
        return RedirectResponse(
            url=f"/page/move?warehouse={warehouse}&location={from_location}&msg=출발_도착_로케이션_동일",
            status_code=303,
        )

    # ✅ 브랜드/품명 자동 보정
    try:
        resolved_brand, resolved_name = resolve_inventory_brand_and_name(
            warehouse=warehouse,
            location=from_location,
            item_code=item_code,
            lot=lot,
            spec=spec,
            brand=brand,
        )
    except ValueError as e:
        return RedirectResponse(
            url=f"/page/move?warehouse={warehouse}&location={from_location}&msg={str(e)}",
            status_code=303,
        )

    final_brand = resolved_brand or brand
    final_name = item_name or resolved_name

    # 1️⃣ 출발지 재고 차감
    ok = upsert_inventory(
        warehouse=warehouse,
        location=from_location,
        brand=final_brand,
        item_code=item_code,
        item_name=final_name,
        lot=lot,
        spec=spec,
        qty_delta=-qty,
        note=note or "이동 출발",
    )

    if not ok:
        return RedirectResponse(
            url=f"/page/move?warehouse={warehouse}&location={from_location}&msg=재고_부족",
            status_code=303,
        )

    # 2️⃣ 도착지 재고 가산
    upsert_inventory(
        warehouse=warehouse,
        location=to_location,
        brand=final_brand,
        item_code=item_code,
        item_name=final_name,
        lot=lot,
        spec=spec,
        qty_delta=qty,
        note=note or "이동 도착",
    )

    # 3️⃣ 이력 기록
    add_history(
        type="이동",
        warehouse=warehouse,
        operator=operator,
        brand=final_brand,
        item_code=item_code,
        item_name=final_name,
        lot=lot,
        spec=spec,
        from_location=from_location,
        to_location=to_location,
        qty=qty,
        note=note or "이동",
    )

    return RedirectResponse(
        url=f"/page/move?warehouse={warehouse}&location={from_location}&msg=이동_완료",
        status_code=303,
    )
