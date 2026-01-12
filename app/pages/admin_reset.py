from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")

router = APIRouter(prefix="/page", tags=["admin-page"])

@router.get("/admin-reset", response_class=HTMLResponse)
def admin_reset_page(request: Request):
    return templates.TemplateResponse(
        "admin_reset.html",
        {"request": request}
    )
