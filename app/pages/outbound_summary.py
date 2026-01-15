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
    year: int | None = None,
    month: int | None = None,
):
    """
    입·출고 통합 통계 페이지
    - 테이블 : 일자별 출고 합계
    - 차트 1 : 일자별 입고 / 출고
    - 차트 2 : 브랜드별 출고
    """

    # =================================================
    # 0️⃣ 기본 연 / 월
    # =================================================
    now = datetime.now()
    year = year or now.year
    month = month or now.month

    start_date = f"{year}-{month:02d}-01"
    last_day = monthrange(year, month)[1]
    end_date = f"{year}-{month:02d}-{last_day:02d}"

    # =================================================
    # 1️⃣ 테이블 : 일자별 출고
    # =================================================
    rows = query_outbound_summary(year=year, month=month)
    # [{"day": "2026-01-14", "total_qty": 10}, ...]

    # =================================================
    # 2️⃣ 입·출고 통합 (일자 기준)
    # =================================================
    io_rows = query_io_stats(start_date, end_date)
    # [{"day": "2026-01-08", "io_type": "IN", "total_qty": 10}, ...]

    daily_map: dict[str, dict[str, int]] = {}

    for r in io_rows:
        day = r["day"]
        io_type = r["io_type"]
        qty = r["total_qty"] or 0

        if day not in daily_map:
            daily_map[day] = {"IN": 0, "OUT": 0}

        if io_type in ("IN", "OUT"):
            daily_map[day][io_type] += qty

    daily_labels = sorted(daily_map.keys())
    daily_in = [daily_map[d]["IN"] for d in daily_labels]
    daily_out = [daily_map[d]["OUT"] for d in daily_labels]

    monthly_in_total = sum(daily_in)
    monthly_out_total = sum(daily_out)

    # =================================================
    # 3️⃣ 브랜드별 출고
    # =================================================
    brand_data = query_outbound_monthly_and_brand(
        year=year,
        month=month,
    )

    # 반환 타입 호환
    if isinstance(brand_data, dict):
        brand_rows = brand_data.get("by_brand", [])
    else:
        _, brand_rows = brand_data

    brand_labels = [r["brand"] for r in brand_rows]
    brand_values = [r["total_qty"] for r in brand_rows]

    # =================================================
    # 4️⃣ 템플릿 렌더링
    # =================================================
    return templates.TemplateResponse(
        "outbound_summary.html",
        {
            "request": request,

            # 조회 조건
            "year": year,
            "month": month,
            "start": start_date,
            "end": end_date,

            # 요약
            "monthly_in_total": monthly_in_total,
            "monthly_out_total": monthly_out_total,

            # 차트
            "daily_labels": daily_labels,
            "daily_in": daily_in,
            "daily_out": daily_out,

            "brand_labels": brand_labels,
            "brand_values": brand_values,

            # 테이블
            "rows": rows,
        },
    )
