# app/pages/erp_verify.py
from fastapi import APIRouter, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR
from app.core.auth import require_login
from app.utils.erp_verify import parse_erp_excel_bytes
from app.db import get_inventory_compare_rows

router = APIRouter(prefix="/page/erp-verify", tags=["page-erp-verify"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("", response_class=HTMLResponse)
def erp_verify_page(request: Request):
    try:
        require_login(request)
    except:
        return RedirectResponse("/login", status_code=303)

    return templates.TemplateResponse("erp_verify.html", {"request": request})


@router.post("", response_class=HTMLResponse)
async def erp_verify_run(request: Request, file: UploadFile = File(...)):
    try:
        require_login(request)
    except:
        return RedirectResponse("/login", status_code=303)

    data = await file.read()
    try:
        erp_rows = parse_erp_excel_bytes(data)
    except ValueError as e:
        return templates.TemplateResponse("erp_verify.html", {"request": request, "error": str(e)})

    result = get_inventory_compare_rows(erp_rows)
    return templates.TemplateResponse("erp_verify.html", {"request": request, "result": result})
