from datetime import datetime
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import query_outbound_summary

router = APIRouter(prefix="/page/outbound-summary", tags=["출고통계"])

# ✅ 여기 핵심 수정
templates = Jinja2Templates(directory="app/templates")


@router.get("")
def outbound_summary_page(
    request: Request,
    year: int | None = None,
    month: int | None = None
):
    now = datetime.now()

    if year is None:
        year = now.year
    if month is None:
        month = now.month

    rows = query_outbound_summary(year=year, month=month)

    return templates.TemplateResponse(
        "outbound_summary.html",
        {
            "request": request,
            "rows": rows,
            "year": year,
            "month": month,
        }
    )
