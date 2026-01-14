from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR

router = APIRouter(prefix="/m/calendar", tags=["mobile-calendar"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("", response_class=HTMLResponse)
def page(request: Request, year: int | None = None, month: int | None = None):
    today = date.today()
    y = year or today.year
    m = month or today.month
    return templates.TemplateResponse(
        "mobile/calendar.html",
        {
            "request": request,
            "year": y,
            "month": m,
        },
    )
