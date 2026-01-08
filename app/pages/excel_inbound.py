from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR


router = APIRouter(prefix="/page/excel/inbound", tags=["page-excel-inbound"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("", response_class=HTMLResponse)
def page(request: Request):
    return templates.TemplateResponse("excel_inbound.html", {"request": request})
