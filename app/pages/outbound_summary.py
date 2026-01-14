from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime

from app.db import (
    query_outbound_summary,                # ✅ 일자별 출고 (테이블)
    query_outbound_monthly_and_brand,      # ✅ 월 누적 + 브랜드별
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
    출고 통계 페이지
    - 테이블 : 일자별 출고 합계
    - 차트 1 : 월별 누적 출고
    - 차트 2 : 브랜드별 출고
    """

    # ✅ 기본값: 현재 연 / 월
    now = datetime.now()
    year = year or now.year
    month = month or now.month

    # -------------------------------------------------
    # 1️⃣ 테이블용 : 일자별 출고
    # -------------------------------------------------
    rows = query_outbound_summary(
        year=year,
        month=month,
    )
    # rows 예시:
    # [
    #   {"day": "2026-01-14", "total_qty": 10},
    #   {"day": "2026-01-20", "total_qty": 5},
    # ]

    # -------------------------------------------------
    # 2️⃣ 그래프용 : 월 누적 + 브랜드별
    # -------------------------------------------------
    cumulative, brands = query_outbound_monthly_and_brand(
        year=year,
        month=month,
    )
    # cumulative 예시:
    # [{"day": "2026-01-14", "cumulative_qty": 10}, ...]
    # brands 예시:
    # [{"brand": "FLORIM", "total_qty": 15}, ...]

    # -------------------------------------------------
    # 3️⃣ JS 바인딩용 데이터 가공
    # -------------------------------------------------

    # 🔹 월별 누적 (라인 차트)
    daily_labels = [r["day"] for r in cumulative]
    daily_values = [r["cumulative_qty"] for r in cumulative]

    # 🔹 브랜드별 (바 차트)
    brand_labels = [r["brand"] for r in brands]
    brand_values = [r["total_qty"] for r in brands]

    # -------------------------------------------------
    # 4️⃣ 템플릿 렌더링
    # -------------------------------------------------
    return templates.TemplateResponse(
        "outbound_summary.html",
        {
            "request": request,

            # 선택값
            "year": year,
            "month": month,

            # 📋 테이블
            "rows": rows,

            # 📈 월별 누적 출고
            "daily_labels": daily_labels,
            "daily_values": daily_values,

            # 📊 브랜드별 출고
            "brand_labels": brand_labels,
            "brand_values": brand_values,
        },
    )
