from fastapi import APIRouter, Form
from fastapi.responses import RedirectResponse

from app.db import (
    upsert_inventory,
    add_history,
    resolve_inventory_brand_and_name,
)

router = APIRouter(prefix="/api/move", tags=["이동"])


@router.post("")
def move(
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
    # ❌ 기본 검증
    if qty <= 0:
        return {"ok": False, "msg": "이동 수량은 1 이상이어야 합니다."}

    if from_location.strip() == to_location.strip():
        return {"ok": False, "msg": "출발/도착 로케이션이 동일합니다."}

    # ✅ 브랜드 자동 보정
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
        return {"ok": False, "msg": str(e)}

    final_brand = resolved_brand or brand
    final_name = item_name or resolved_name

    # 1️⃣ 출발지 차감
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
        return {"ok": False, "msg": "출발지 재고가 부족합니다."}

    # 2️⃣ 도착지 가산
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

    # 3️⃣ 이력
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

    return {"ok": True}
