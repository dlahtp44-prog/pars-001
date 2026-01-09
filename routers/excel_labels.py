from fastapi import APIRouter, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.core.paths import TEMPLATES_DIR
import openpyxl

router = APIRouter(prefix="/api/labels", tags=["라벨API"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.post("/product", response_class=HTMLResponse)
async def product_labels(file: UploadFile = File(...)):
    wb = openpyxl.load_workbook(file.file)
    ws = wb.active
    items = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row[0]:
            continue
        items.append({
            "brand": row[0],
            "code": row[1],
            "name": row[2],
            "lot": row[3],
            "spec": row[4],
        })
    return templates.TemplateResponse("labels/product_print.html", {"request": None, "items": items})
