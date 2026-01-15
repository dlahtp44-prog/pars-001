from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.db import query_io_group_stats

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/page/io-advanced", response_class=HTMLResponse)
def io_advanced_page(
    request: Request,
    start: str | None = None,
    end: str | None = None,
    group: str = "item",
    brand: str = "",
    keyword: str = "",
):
    if not start or not end:
        now = datetime.now()
        start = f"{now.year}-{now.month:02d}-01"
        end = f"{now.year}-{now.month:02d}-{monthrange(now.year, now.month)[1]}"

    rows = query_io_group_stats(
        start=start,
        end=end,
        group=group,
        brand=brand,
        keyword=keyword,
    )

    return templates.TemplateResponse(
        "io_advanced.html",
        {
            "request": request,
            "rows": rows,
            "start": start,
            "end": end,
            "group": group,
            "brand": brand,
            "keyword": keyword,
        },
    )

    )
