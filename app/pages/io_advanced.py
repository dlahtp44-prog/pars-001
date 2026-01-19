from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
from calendar import monthrange

from app.db import (
    query_outbound_summary,
    query_outbound_monthly_and_brand,
    query_io_stats,
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# =====================================================
# 출고 요약 페이지
# URL: /page/outbound-summary
# =====================================================

@router.get("/page/outbound-summary", response_class=HTMLResponse)
def outbound_summary_page(
    request: Request,
    start: str | None = None,
    end: str | None = None,
):
    # =========================
    # 0️⃣ 날짜 기본값
    # =========================
    now = datetime.now()

    if not start or not end:
        start = f"{now.year}-{now.month:02d}-01"
        end = f"{now.year}-{now.month:02d}-{monthrange(now.year, now.month)[1]}"

    year = int(start[:4])
    month = int(start[5:7])

    # =========================
    # 1️⃣ 일자별 출고 테이블
    # =========================
    rows = query_outbound_summary(year=year, month=month)

    # =========================
    # 2️⃣ 입·출고 통합 (일자별)
    # =========================
    io_rows = query_io_stats(start, end)

    daily_map: dict[str, dict[str, int]] = {}

    for r in io_rows:
        day = r.get("day")
        io = r.get("io_type")
        qty = r.get("total_qty") or 0

        if not day or not io:
            continue  # NULL 방어

        if day not in daily_map:
            daily_map[day] = {"IN": 0, "OUT": 0}

        daily_map[day][io] += qty

    daily_labels = sorted(daily_map.keys())
    daily_in = [daily_map[d]["IN"] for d in daily_labels]
    daily_out = [daily_map[d]["OUT"] for d in daily_labels]

    monthly_in_total = sum(daily_in)
    monthly_out_total = sum(daily_out)

    # =========================
    # 3️⃣ 브랜드별 출고
    # =========================
    brand_data = query_outbound_monthly_and_brand(year=year, month=month)

    if isinstance(brand_data, dict):
        brand_rows = brand_data.get("by_brand", [])
    else:
        _, brand_rows = brand_data

    brand_labels = [r["brand"] for r in brand_rows]
    brand_values = [r["total_qty"] for r in brand_rows]

    # =========================
    # 4️⃣ 렌더링
    # =========================
    return templates.TemplateResponse(
        "outbound_summary.html",
        {
            "request": request,
            "rows": rows,
            "start": start,
            "end": end,
            "daily_labels": daily_labels,
            "daily_in": daily_in,
            "daily_out": daily_out,
            "monthly_in_total": monthly_in_total,
            "monthly_out_total": monthly_out_total,
            "brand_labels": brand_labels,
            "brand_values": brand_values,
        },
    )


# =====================================================
# 입·출고 통합 상세 페이지
# URL: /page/io-advanced
# =====================================================

@router.get("/page/io-advanced", response_class=HTMLResponse)
def io_advanced_page(
    request: Request,
    start: str | None = None,
    end: str | None = None,
    group: str = "item",
):
    # =========================
    # 0️⃣ 날짜 기본값
    # =========================
    now = datetime.now()

    if not start or not end:
        start = f"{now.year}-{now.month:02d}-01"
        end = f"{now.year}-{now.month:02d}-{monthrange(now.year, now.month)[1]}"

    # =========================
    # 1️⃣ 입·출고 통합 데이터
    # =========================
    rows = query_io_stats(start, end)

    # =========================
    # 2️⃣ 렌더링
    # =========================
    return templates.TemplateResponse(
        "io_advanced.html",
        {
            "request": request,
            "rows": rows,
            "start": start,
            "end": end,
            "group": group,
        },
    )
