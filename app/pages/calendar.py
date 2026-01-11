from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import date

from app.core.paths import TEMPLATES_DIR

router = APIRouter(prefix="/page/calendar", tags=["calendar"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("", response_class=HTMLResponse)
def calendar_page(request: Request):
    today = date.today()
    return templates.TemplateResponse(
        "calendar.html",
        {
            "request": request,
            "year": today.year,
            "month": today.month,
        },
    )
