from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR


router = APIRouter(prefix="/page/excel", tags=["page-excel-center"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("", response_class=HTMLResponse)
def excel_center(request: Request):
    return templates.TemplateResponse("excel_center.html", {"request": request})
