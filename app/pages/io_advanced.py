from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import date

from app.db import query_io_group_stats

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/page/io-advanced", response_class=HTMLResponse)
def io_advanced_page(
    request: Request,
    start: str | None = None,
    end: str | None = None,
    group: str = "brand",      # brand | item | spec
    keyword: str = "",
    brand: str = "",
):
    # 기본: 이번 달
    today = date.today()
    if not start or not end:
        start = today.replace(day=1).isoformat()
        end = today.isoformat()

    group = group if group in ("brand", "item", "spec") else "brand"

    rows = query_io_group_stats(
        start_date=start,
        end_date=end,
        group=group,
        keyword=keyword.strip(),
        brand=brand.strip(),
    )

return templates.TemplateResponse(
    "io_advanced.html",
    {
        "request": request,
        "start": start,   # 🔑 반드시 넘김
        "end": end,       # 🔑 반드시 넘김
        "group": group,
        "keyword": keyword,
        "brand": brand,
        "rows": rows,
    },
)
