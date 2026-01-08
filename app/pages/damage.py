from datetime import date
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.db import list_damage_codes, add_damage_history

templates = Jinja2Templates(directory="app/templates")
router = APIRouter()

@router.get("/damage", response_class=HTMLResponse)
def page_damage(request: Request):
    codes = list_damage_codes(active_only=True)
    return templates.TemplateResponse(
        "damage.html",
        {"request": request, "codes": codes, "occurred_at": date.today().isoformat(), "msg": ""},
    )

@router.post("/damage", response_class=HTMLResponse)
def submit_damage(
    request: Request,
    occurred_at: str = Form(...),
    warehouse: str = Form(...),
    location: str = Form(...),
    brand: str = Form(""),
    item_code: str = Form(...),
    item_name: str = Form(...),
    lot: str = Form(...),
    spec: str = Form(...),
    qty: float = Form(...),
    damage_code_id: int = Form(...),
    detail: str = Form(""),
    deduct_inventory: str = Form(""),
):
    deduct = True if str(deduct_inventory).strip() in ("1", "true", "on", "yes") else False
    add_damage_history(
        occurred_at=occurred_at,
        warehouse=warehouse,
        location=location,
        brand=brand,
        item_code=item_code,
        item_name=item_name,
        lot=lot,
        spec=spec,
        qty=qty,
        damage_code_id=damage_code_id,
        detail=detail,
        deduct_inventory=deduct,
    )
    return RedirectResponse(url="/damage/history", status_code=303)
