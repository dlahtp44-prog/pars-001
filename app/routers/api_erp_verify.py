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
from fastapi.responses import StreamingResponse
import io
import openpyxl


@router.post("/verify/download")
def download_verify_excel(rows: list[dict]):
    """
    ERP 재고 검증 결과 엑셀 다운로드
    프론트에서 verify 결과 rows 그대로 전달
    """

    if not rows:
        raise HTTPException(status_code=400, detail="다운로드할 데이터가 없습니다.")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "ERP 재고 검증 결과"

    # 헤더
    headers = [
        "상태",
        "비교단위",
        "품번",
        "LOT",
        "규격",
        "ERP 수량",
        "WMS 수량",
        "차이",
        "비고",
    ]
    ws.append(headers)

    # 데이터
    for r in rows:
        ws.append([
            r.get("status", ""),
            r.get("mode", ""),
            r.get("item_code", ""),
            r.get("lot", ""),
            r.get("spec", ""),
            r.get("erp_qty", 0),
            r.get("wms_qty", 0),
            r.get("diff", 0),
            r.get("note", ""),
        ])

    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)

    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=erp_verify_result.xlsx"
        },
    )
