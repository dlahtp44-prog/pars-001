from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.core.paths import TEMPLATES_DIR
from app.db import query_outbound_summary

router = APIRouter(prefix="/page/outbound-summary", tags=["outbound-summary"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("", response_class=HTMLResponse)
def outbound_summary_page(
    request: Request,
    year: int | None = None,
    month: int | None = None,
    day: int | None = None,
):
    rows = query_outbound_summary(year, month, day)
    return templates.TemplateResponse(
        "outbound_summary.html",
        {
            "request": request,
            "rows": rows,
            "year": year,
            "month": month,
            "day": day,
        },
    )
