from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from datetime import datetime
from app.db import query_outbound_summary
from app.utils.excel_export import rows_to_xlsx_bytes

router = APIRouter(prefix="/api/excel/outbound-summary", tags=["excel-outbound-summary"])

@router.get("")
def download_outbound_summary_excel(
    year: int | None = Query(None),
    month: int | None = Query(None),
    day: int | None = Query(None),
):
    rows = query_outbound_summary(year, month, day)

    columns = [
        ("brand", "브랜드"),
        ("item_code", "품번"),
        ("item_name", "품명"),
        ("total_qty", "출고수량"),
    ]

    data = rows_to_xlsx_bytes(rows, columns, sheet_name="출고집계")

    filename = f"outbound_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    return StreamingResponse(
        iter([data]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
