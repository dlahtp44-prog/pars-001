from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.core.paths import TEMPLATES_DIR

router = APIRouter(prefix="/m", tags=["mobile"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("", response_class=HTMLResponse)
def m_home(request: Request):
    return templates.TemplateResponse("m/home.html", {"request": request})
