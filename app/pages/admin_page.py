from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
router = APIRouter(prefix="/admin", tags=["Page"], include_in_schema=False)

@router.get("/", response_class=HTMLResponse)
def admin_home(request: Request):
    # admin.html이 없으면 간단 페이지로 대체
    try:
        return templates.TemplateResponse("admin.html", {"request": request})
    except Exception:
        html = """<!doctype html><html lang='ko'><head><meta charset='utf-8'>
        <meta name='viewport' content='width=device-width, initial-scale=1'>
        <title>Admin</title></head><body style='font-family:system-ui;padding:16px'>
        <h2>Admin</h2>
        <ul>
          <li><a href='/'>Home</a></li>
          <li><a href='/inventory'>Inventory</a></li>
          <li><a href='/history'>History</a></li>
          <li><a href='/m'>Mobile</a></li>
        </ul>
        </body></html>"""
        return HTMLResponse(html)
