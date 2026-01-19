# app/pages/init_inventory.py
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
router = APIRouter(prefix="/page", tags=["page-init-inventory"])


@router.get("/init-inventory", response_class=HTMLResponse)
def page_init_inventory(request: Request):
    return templates.TemplateResponse(
        "init_inventory.html",
        {"request": request}
    )
