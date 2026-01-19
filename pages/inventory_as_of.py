from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import date

from app.db import query_inventory_as_of
from app.core.paths import TEMPLATES_DIR

router = APIRouter(prefix="/page", tags=["inventory-as-of"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/inventory-as-of", response_class=HTMLResponse)
def inventory_as_of_page(request: Request):
    as_of = request.query_params.get("as_of")
    q = request.query_params.get("q", "")

    # ✅ 기준일 기본값 = 오늘
    if not as_of:
        as_of = date.today().isoformat()

    rows = query_inventory_as_of(
        as_of_date=as_of,
        keyword=q,
    )

    return templates.TemplateResponse(
        "inventory_as_of.html",
        {
            "request": request,
            "rows": rows,
            "as_of": as_of,
            "q": q,
        }
    )
