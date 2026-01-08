
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(prefix="/qr", tags=["Page"], include_in_schema=False)


@router.get("/scan", response_class=HTMLResponse)
def qr_scan_page(request: Request):
    return templates.TemplateResponse("qr_scan.html", {"request": request})
