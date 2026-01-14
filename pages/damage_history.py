from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR
from app.db import query_damage_history, query_damage_summary_by_category
from app.utils.excel_export import rows_to_xlsx_bytes

router = APIRouter(prefix="/page/damage-history", tags=["page-damage-history"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _to_int(v: str | None):
    if not v:
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
):
    y = _to_int(year)
    m = _to_int(month)

    rows = query_damage_history(limit=500)
    summary = query_damage_summary_by_category(year=y, month=m)

    return templates.TemplateResponse(
        "damage_history.html",
        {
            "request": request,
            "rows": rows,
            "summary": summary,
            "year": year or "",
            "month": month or "",
        },
    )


@router.get("/excel")
def download_excel():
    rows = query_damage_history(limit=5000)

    columns = [
        ("occurred_at", "발생일"),
        ("warehouse", "창고"),
        ("location", "로케이션"),
        ("brand", "브랜드"),
        ("item_code", "품번"),
        ("item_name", "품명"),
        ("lot", "LOT"),
        ("spec", "규격"),
        ("qty", "수량"),
        ("category", "대분류"),
        ("type", "유형"),
        ("situation", "상황"),
        ("detail", "상세내용"),
    ]

    data = rows_to_xlsx_bytes(rows, columns, sheet_name="CS현황")

    return StreamingResponse(
        iter([data]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": 'attachment; filename="cs_history.xlsx"'
        },
    )
