from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# =====================================================
# TEMPLATES
# =====================================================

templates = Jinja2Templates(directory="app/templates")

# =====================================================
# ROUTER
# =====================================================

router = APIRouter(
    prefix="/page/history",
    tags=["Page"],
    include_in_schema=False
)

# =====================================================
# PAGE
# =====================================================

@router.get("/", response_class=HTMLResponse)
def history_page(request: Request):
    return templates.TemplateResponse(
        "history.html",
        {"request": request}
    )
