from fastapi import APIRouter, Form, HTTPException

from app.db import (
    add_history,
    resolve_inventory_brand_and_name,
    upsert_inventory,
)

router = APIRouter(prefix="/api/move", tags=["move"])


@router.post("")
def move(
    warehouse: str = Form(...),
    from_location: str = Form(...),
    to_location: str = Form(...),
    brand: str = Form(""),
    item_code: str = Form(...),
    item_name: str = Form(...),
    lot: str = Form(...),
    spec: str = Form(...),
    qty: float = Form(...),
    note: str = Form(""),
    operator: str = Form(""),
):
    """
    ✅ 이동 처리
    - 출발지 재고 부족 시 차단
    - 성공 시 history에 '이동' 기록
    - 브랜드 미입력 시 출발지 현재고에서 자동 보정(후보 1개일 때만)
    """
    if qty is None or float(qty) <= 0:
        raise HTTPException(status_code=400, detail="이동 수량은 1 이상이어야 합니다.")
    if from_location.strip() == to_location.strip():
        raise HTTPException(status_code=400, detail="출발/도착 로케이션이 동일합니다.")

    # 브랜드/품명 자동 보정 (출발지 기준)
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
        raise HTTPException(status_code=400, detail=str(e))

    final_brand = resolved_brand or (brand or "")
    final_name = item_name or resolved_name or ""

    # 1) 출발지 차감
    ok = upsert_inventory(
        warehouse=warehouse,
        location=from_location,
        brand=final_brand,
        item_code=item_code,
        item_name=final_name,
        lot=lot,
        spec=spec,
        qty_delta=-float(qty),
        note=note,
    )
    if not ok:
        raise HTTPException(status_code=400, detail="출발지 재고가 부족하여 이동할 수 없습니다.")

    # 2) 도착지 가산
    upsert_inventory(
        warehouse=warehouse,
        location=to_location,
        brand=final_brand,
        item_code=item_code,
        item_name=final_name,
        lot=lot,
        spec=spec,
        qty_delta=float(qty),
        note=note,
    )

    # 3) 이력 기록
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
        qty=float(qty),
        note=note,
    )

    return {"ok": True}
