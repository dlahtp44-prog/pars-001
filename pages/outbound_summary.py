from __future__ import annotations

from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR
from app.db import query_outbound_summary

router = APIRouter(prefix="/page/outbound-summary", tags=["page-outbound-summary"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("", response_class=HTMLResponse)
def outbound_summary_page(
    request: Request,
    year: int | None = Query(None),
    month: int | None = Query(None),
):
    # year 없으면 연도별 요약, year만 있으면 월별, year+month면 일별
    rows = query_outbound_summary(year=year, month=month)

    return templates.TemplateResponse(
        "outbound_summary.html",
        {
            "request": request,
            "year": year or "",
            "month": month or "",
            "rows": rows,
        },
    )
