from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR
from app.db import query_outbound_summary

router = APIRouter(
    prefix="/page/outbound-summary",
    tags=["page-outbound-summary"]
)

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("", response_class=HTMLResponse)
def page(request: Request, year: int | None = None, month: int | None = None):
    rows = query_outbound_summary(year=year, month=month)

    return templates.TemplateResponse(
        "outbound_summary.html",
        {
            "request": request,
            "rows": rows,
            "year": year,
            "month": month,
        },
    )
