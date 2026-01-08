from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR
from app.db import query_history
from app.utils.excel_export import rows_to_xlsx_bytes

router = APIRouter(prefix="/page/history", tags=["page-history"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _to_int(v: str | None):
    if v is None:
        return None
    v = v.strip()
    if v == "":
        return None
    try:
        return int(v)
    except ValueError:
        return None


@router.get("", response_class=HTMLResponse)
def page(
    request: Request,
    year: str | None = None,
    month: str | None = None,
    day: str | None = None,
    limit: int = 300,
):
    rows = query_history(
        limit=limit,
        year=_to_int(year),
        month=_to_int(month),
        day=_to_int(day),
    )

    return templates.TemplateResponse(
        "history.html",
        {
            "request": request,
            "rows": rows,
            "year": year or "",
            "month": month or "",
            "day": day or "",
            "limit": limit,
        },
    )


@router.get("/excel")
def download_excel(
    year: str | None = None,
    month: str | None = None,
    day: str | None = None,
    limit: int = 2000,
):
    rows = query_history(
        limit=limit,
        year=_to_int(year),
        month=_to_int(month),
        day=_to_int(day),
    )

    columns = [
        ("created_at", "시간"),
        ("type", "유형"),
        ("warehouse", "창고"),
        ("from_location", "출발로케이션"),
        ("to_location", "도착로케이션"),
        ("brand", "브랜드"),
        ("item_code", "품번"),
        ("item_name", "품명"),
        ("lot", "LOT"),
        ("spec", "규격"),
        ("qty", "수량"),
        ("note", "비고"),
        ("operator", "작업자"),
    ]

    data = rows_to_xlsx_bytes(rows, columns, sheet_name="이력")

    return StreamingResponse(
        iter([data]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": 'attachment; filename="history.xlsx"'
        },
    )
