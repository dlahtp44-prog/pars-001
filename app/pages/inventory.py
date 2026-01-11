from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR
from app.db import query_inventory
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


@router.get("", response_class=HTMLResponse)
def page(
    request: Request,
    warehouse: str = "",
    location: str = "",
    brand: str = "",
    item_code: str = "",
    lot: str = "",
    spec: str = "",
):
    rows = query_inventory(
        warehouse=warehouse,
        location=location,
        brand=brand,
        item_code=item_code,
        lot=lot,
        spec=spec,
    )

    view_rows = _format_rows(rows)

    return templates.TemplateResponse(
        "inventory.html",
        {
            "request": request,
            "rows": view_rows,
            "warehouse": warehouse,
            "location": location,
            "brand": brand,
            "item_code": item_code,
            "lot": lot,
            "spec": spec,
        },
    )


@router.get("/excel")
def download_excel(
    warehouse: str = "",
    location: str = "",
    brand: str = "",
    item_code: str = "",
    lot: str = "",
    spec: str = "",
):
    rows = query_inventory(
        warehouse=warehouse,
        location=location,
        brand=brand,
        item_code=item_code,
        lot=lot,
        spec=spec,
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
