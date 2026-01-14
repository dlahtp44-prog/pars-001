from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from datetime import date

from app.db import query_inventory_as_of
from app.core.paths import TEMPLATES_DIR

router = APIRouter(prefix="/page/inventory-as-of", tags=["재고 스냅샷"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("")
def inventory_as_of_page(
    request: Request,
    as_of: str | None = None,
    q: str = ""
):
    if not as_of:
        as_of = date.today().isoformat()

    rows = query_inventory_as_of(as_of_date=as_of, keyword=q)

    return templates.TemplateResponse(
        "inventory_as_of.html",
        {
            "request": request,
            "rows": rows,
            "as_of": as_of,
            "q": q,
        }
    )
