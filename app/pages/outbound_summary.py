from datetime import datetime
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import query_outbound_summary

router = APIRouter(prefix="/page/outbound-summary", tags=["출고통계"])

# ✅ 여기 핵심 수정
templates = Jinja2Templates(directory="app/templates")


@router.get("/page/outbound-summary", response_class=HTMLResponse)
def outbound_summary_page(
    request: Request,
    year: int | None = None,
    month: int | None = None,
):
    today = date.today()
    year = year or today.year
    month = month or today.month

    rows = query_outbound_summary(year, month)

    labels = [r["day"] for r in rows]
    values = [r["total_qty"] for r in rows]

    return templates.TemplateResponse(
        "outbound_summary.html",
        {
            "request": request,
            "year": year,
            "month": month,
            "labels": labels,
            "values": values,
            "rows": rows,
        },
    )
