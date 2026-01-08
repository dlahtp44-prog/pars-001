from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.core.paths import TEMPLATES_DIR
from app.db import query_inventory

router = APIRouter()
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("/m/qr/inventory", response_class=HTMLResponse)
def by_location(request: Request, location: str):
    rows = query_inventory(location=location)
    return templates.TemplateResponse("m/qr_inventory.html", {"request": request, "location": location, "rows": rows})
