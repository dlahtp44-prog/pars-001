from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
import io
import openpyxl
from datetime import datetime

from app.db import query_inventory_as_of

router = APIRouter(prefix="/api/excel", tags=["excel"])


@router.get("/inventory-as-of")
def excel_inventory_as_of(
    as_of: str = Query(...),
    q: str = Query("")
):
    rows = query_inventory_as_of(as_of_date=as_of, keyword=q)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "기준일 재고"

    # 헤더
    ws.append([
        "창고", "로케이션", "브랜드", "품번", "품명",
        "LOT", "규격", "입고 누계", "출고 누계", "현재고"
    ])

    for r in rows:
        ws.append([
            r["warehouse"],
            r["location"],
            r["brand"],
            r["item_code"],
            r["item_name"],
            r["lot"],
            r["spec"],
            float(r["inbound_qty"]),
            float(r["outbound_qty"]),
            float(r["current_qty"]),
        ])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    filename = f"inventory_as_of_{as_of}.xlsx"

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
