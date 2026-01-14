from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime

from app.db import query_outbound_summary

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/page/outbound-summary", response_class=HTMLResponse)
def outbound_summary_page(
    request: Request,
    year: int | None = None,
    month: int | None = None,
):
    today = datetime.today()
    year = year or today.year
    month = month or today.month

    rows = query_outbound_summary(year=year, month=month)

    labels = [r["day"] for r in rows]
    values = [r["total_qty"] for r in rows]

    return templates.TemplateResponse(
        "outbound_summary.html",
        {
            "request": request,
            "year": year,
            "month": month,
            "rows": rows,
            "labels": labels,
            "values": values,
        },
    )
