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
    year: int,
    month: int,
):
    cumulative, brands = query_outbound_monthly_and_brand(
        year=year,
        month=month,
    )

    return templates.TemplateResponse(
        "outbound_summary.html",
        {
            "request": request,
            "year": year,
            "month": month,
            "daily": cumulative,
            "brands": brands,
        },
    )
