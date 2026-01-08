from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from datetime import date

from app.core.paths import TEMPLATES_DIR
from app.db import add_damage_history, list_damage_codes

router = APIRouter(prefix="/m/cs", tags=["mobile-cs"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("", response_class=HTMLResponse)
def cs_page(request: Request, msg: str = ""):
    return templates.TemplateResponse(
        "mobile_cs.html",
        {
            "request": request,
            "damage_codes": list_damage_codes(active_only=True),
            "today": date.today().isoformat(),
            "msg": msg,
        },
    )


@router.post("")
def submit_cs(
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
):
    if qty <= 0:
        return RedirectResponse(
            url="/m/cs?msg=수량은_1_이상이어야_합니다",
            status_code=303,
        )

    try:
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
            deduct_inventory=True,
        )
    except Exception as e:
        return RedirectResponse(
            url=f"/m/cs?msg={str(e)}",
            status_code=303,
        )

    return RedirectResponse(
        url="/m/cs?msg=CS_등록_완료",
        status_code=303,
    )
