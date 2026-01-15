from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
from calendar import monthrange

from app.db import query_io_group_stats

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/page/io-advanced", response_class=HTMLResponse)
def io_advanced_page(
    request: Request,
    start: str | None = None,
    end: str | None = None,
    group: str = "item",     # brand | item | spec
    brand: str = "",
    keyword: str = "",
):
    # =====================================
    # 1️⃣ 기본 날짜 (이번 달)
    # =====================================
    if not start or not end:
        now = datetime.now()
        start = f"{now.year}-{now.month:02d}-01"
        end = f"{now.year}-{now.month:02d}-{monthrange(now.year, now.month)[1]}"

    # =====================================
    # 2️⃣ 통계 조회
    # =====================================
    rows = query_io_group_stats(
        start_date=start,
        end_date=end,
        group=group,
        brand=brand,
        keyword=keyword,
    )

    # =====================================
    # 3️⃣ 렌더링
    # =====================================
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
