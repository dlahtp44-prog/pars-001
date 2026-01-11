# app/routers/api_erp_verify.py
from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.db import get_inventory_compare_rows
from app.utils.erp_verify import parse_erp_excel_bytes

router = APIRouter(prefix="/api/erp", tags=["ERP 재고 검증"])


@router.post("/verify")
async def verify_erp_stock(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="엑셀(xlsx) 파일만 업로드 가능합니다.")

    data = await file.read()
    try:
        erp_rows = parse_erp_excel_bytes(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    result = get_inventory_compare_rows(erp_rows)
    return result
