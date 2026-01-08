from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.core.paths import TEMPLATES_DIR
from app.db import query_inventory
from app.utils.qr_format import build_item_qr

router = APIRouter()
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("/m/inventory/detail", response_class=HTMLResponse)
def detail(request: Request, item_code: str, lot: str, spec: str, brand: str = ""):
    rows = query_inventory(item_code=item_code, lot=lot, spec=spec, brand=brand) if brand else query_inventory(item_code=item_code, lot=lot, spec=spec)
    qr = build_item_qr(item_code, rows[0]["item_name"] if rows else "", lot, spec, brand=rows[0].get('brand','') if rows else brand)
    return templates.TemplateResponse("m/inventory_detail.html", {"request": request, "rows": rows, "item_code": item_code, "lot": lot, "spec": spec, "brand": brand, "qr": qr})
