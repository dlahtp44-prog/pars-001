from __future__ import annotations

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
):
    """📥 출고 통계 엑셀 다운로드
    - year 없으면: 연도별 합계
    - year만 있으면: 월별 합계
    - year+month면: 일별 합계
    """

    rows = query_outbound_summary(year=year, month=month)

    # rows: {period, total_qty}
    columns = [
        ("period", "기간"),
        ("total_qty", "출고합계"),
    ]

    sheet = "연도별출고" if not year else ("월별출고" if year and not month else "일별출고")
    data = rows_to_xlsx_bytes(rows, columns, sheet_name=sheet)

    tag = sheet
    filename = f"outbound_summary_{tag}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    return StreamingResponse(
        iter([data]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
