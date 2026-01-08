from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(prefix="/location", tags=["Page"], include_in_schema=False)


@router.get("/", response_class=HTMLResponse)
def location_page(request: Request):
    return templates.TemplateResponse("location.html", {"request": request})

