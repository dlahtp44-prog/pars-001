from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
from calendar import monthrange

from app.db import (
    query_outbound_summary,            # 테이블용 (출고 기준)
    query_outbound_monthly_and_brand,  # 브랜드별 출고
    query_io_stats,                    # 입·출고 통합
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/page/outbound-summary", response_class=HTMLResponse)
def outbound_summary_page(
    request: Request,
    start: str | None = None,
    end: str | None = None,
):
    now = datetime.now()

    if not start or not end:
        start = f"{now.year}-{now.month:02d}-01"
        last_day = monthrange(now.year, now.month)[1]
        end = f"{now.year}-{now.month:02d}-{last_day}"

    # =============================
    # 1️⃣ 일자별 출고 테이블
    # =============================
    rows = query_outbound_summary(
        year=int(start[:4]),
        month=int(start[5:7]),
    )

    # =============================
    # 2️⃣ 입·출고 일자별
    # =============================
    io_rows = query_io_stats(start, end)

    daily_map = {}
    for r in io_rows:
        day = r["day"]
        io = r["io_type"]
        qty = r["total_qty"] or 0

        daily_map.setdefault(day, {"IN": 0, "OUT": 0})
        daily_map[day][io] += qty

    daily_labels = sorted(daily_map.keys())
    daily_in = [daily_map[d]["IN"] for d in daily_labels]
    daily_out = [daily_map[d]["OUT"] for d in daily_labels]

    monthly_in_total = sum(daily_in)
    monthly_out_total = sum(daily_out)

    # =============================
    # 3️⃣ 브랜드별 출고
    # =============================
    _, brand_rows = query_outbound_monthly_and_brand(
        year=int(start[:4]),
        month=int(start[5:7]),
    )

    brand_labels = [r["brand"] for r in brand_rows]
    brand_values = [r["total_qty"] for r in brand_rows]

    return templates.TemplateResponse(
        "outbound_summary.html",
        {
            "request": request,
            "start": start,
            "end": end,

            "rows": rows,

            "daily_labels": daily_labels,
            "daily_in": daily_in,
            "daily_out": daily_out,

            "monthly_in_total": monthly_in_total,
            "monthly_out_total": monthly_out_total,

            "brand_labels": brand_labels,
            "brand_values": brand_values,
        },
    )
