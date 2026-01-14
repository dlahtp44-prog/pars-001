from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime

from app.db import (
    query_outbound_summary,                # 일자별 출고 (테이블)
    query_outbound_monthly_and_brand,      # 월 누적 + 브랜드별
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/page/outbound-summary", response_class=HTMLResponse)
def outbound_summary_page(
    request: Request,
    year: int | None = None,
    month: int | None = None,
):
    # ✅ 기본값: 현재 연/월
    now = datetime.now()
    year = year or now.year
    month = month or now.month

    # 1️⃣ 테이블용 (일자별 출고)
    rows = query_outbound_summary(
        year=year,
        month=month,
    )

    # 2️⃣ 그래프용 (월 누적 + 브랜드별)
    cumulative, brands = query_outbound_monthly_and_brand(
        year=year,
        month=month,
    )

    # 🔹 월별 누적
    daily_labels = [r["day"] for r in cumulative]
    daily_values = [r["cumulative_qty"] for r in cumulative]

    # 🔹 브랜드별
    brand_labels = [r["brand"] for r in brands]
    brand_values = [r["total_qty"] for r in brands]

    return templates.TemplateResponse(
        "outbound_summary.html",
        {
            "request": request,
            "year": year,
            "month": month,

            # 테이블
            "rows": rows,

            # 월별 누적 차트
            "daily_labels": daily_labels,
            "daily_values": daily_values,

            # 브랜드별 차트
            "brand_labels": brand_labels,
            "brand_values": brand_values,
        },
    )
