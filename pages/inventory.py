from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR
from app.db import query_inventory, query_inventory_smart
from app.core.qty import display_qty
from app.utils.excel_export import rows_to_xlsx_bytes

router = APIRouter(prefix="/page/inventory", tags=["page-inventory"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _format_rows(rows):
    """
    화면/엑셀 공용 수량 표시 포맷 적용
    """
    view_rows = []
    for r in rows:
        d = dict(r)
        d["qty"] = display_qty(d.get("qty"))
        view_rows.append(d)
    return view_rows


# =====================================================
# 📄 재고현황 페이지 (PC / 모바일 공용)
# - v1.6: 다중 필드 검색
# - v1.7: q 한 줄 통합 검색 추가
# =====================================================
@router.get("", response_class=HTMLResponse)
def page(
    request: Request,
    q: str = "",                 # ✅ v1.7 통합 검색
    warehouse: str = "",
    location: str = "",
    brand: str = "",
    item_code: str = "",
    lot: str = "",
    spec: str = "",
):
    # ✅ 우선순위: 통합 검색 q → 기존 검색
    if q:
        rows = query_inventory_smart(q=q, limit=5000)
    else:
        rows = query_inventory(
            warehouse=warehouse,
            location=location,
            brand=brand,
            item_code=item_code,
            lot=lot,
            spec=spec,
            limit=5000,
        )

    view_rows = _format_rows(rows)

    return templates.TemplateResponse(
        "inventory.html",
        {
            "request": request,
            "rows": view_rows,
            "q": q,                 # ✅ 템플릿에서 한 줄 검색 유지
            "warehouse": warehouse,
            "location": location,
            "brand": brand,
            "item_code": item_code,
            "lot": lot,
            "spec": spec,
        },
    )


# =====================================================
# 📥 재고현황 엑셀 다운로드
# - 화면과 동일 조건
# - 통합 검색(q) 지원
# =====================================================
@router.get("/excel")
def download_excel(
    q: str = "",                 # ✅ v1.7 통합 검색
    warehouse: str = "",
    location: str = "",
    brand: str = "",
    item_code: str = "",
    lot: str = "",
    spec: str = "",
):
    # ✅ 화면과 동일 로직
    if q:
        rows = query_inventory_smart(q=q, limit=10000)
    else:
        rows = query_inventory(
            warehouse=warehouse,
            location=location,
            brand=brand,
            item_code=item_code,
            lot=lot,
            spec=spec,
            limit=10000,
        )

    view_rows = _format_rows(rows)

    columns = [
        ("warehouse", "창고"),
        ("location", "로케이션"),
        ("brand", "브랜드"),
        ("item_code", "품번"),
        ("item_name", "품명"),
        ("lot", "LOT"),
        ("spec", "규격"),
        ("qty", "수량"),
        ("note", "비고"),
        ("updated_at", "수정일시"),
    ]

    data = rows_to_xlsx_bytes(
        view_rows,
        columns,
        sheet_name="재고현황",
    )

    return StreamingResponse(
        iter([data]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": 'attachment; filename="inventory.xlsx"'
        },
    )
