from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.core.paths import TEMPLATES_DIR

import openpyxl
import qrcode
import base64
from io import BytesIO

router = APIRouter(prefix="/api/labels", tags=["라벨 API"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.post("/product", response_class=HTMLResponse)
def product_label_print(request: Request, file: UploadFile = File(...)):
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="엑셀 파일만 업로드 가능합니다.")

    wb = openpyxl.load_workbook(file.file)
    ws = wb.active

    items = []

    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or not row[0]:
            continue

        brand, code, name, lot, spec = row

        # ✅ QR 내용
        qr_text = f"PRODUCT:{code}|LOT:{lot}"

        qr = qrcode.make(qr_text)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()

        items.append({
            "brand": brand,
            "code": code,
            "name": name,
            "lot": lot,
            "spec": spec,
            "qr_base64": qr_base64,
        })

    return templates.TemplateResponse(
        "labels/product_print.html",
        {
            "request": request,
            "items": items
        }
    )
