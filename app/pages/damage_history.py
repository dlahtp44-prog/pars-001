from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.db import query_damage_history, query_damage_summary_by_category

templates = Jinja2Templates(directory="app/templates")
router = APIRouter()

def _to_int(v):
    if v is None or v == "":
        return None
    try:
        return int(v)
    except Exception:
        return None

@router.get("/damage/history", response_class=HTMLResponse)
def page_damage_history(request: Request, year: str = "", month: str = "", limit: int = 500):
    y = _to_int(year)
    m = _to_int(month)
    rows = query_damage_history(year=y, month=m, limit=limit)
    summary = query_damage_summary_by_category(year=y, month=m)
    return templates.TemplateResponse(
        "damage_history.html",
        {"request": request, "rows": rows, "summary": summary, "year": y, "month": m, "limit": limit},
    )
