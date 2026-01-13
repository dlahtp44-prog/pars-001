from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from datetime import datetime
from app.db import query_history
from app.utils.excel_export import rows_to_xlsx_bytes

router = APIRouter(prefix="/api/excel/history", tags=["excel-history"])


@router.get("")
def download_history_excel(
    year: int | None = Query(None),
    month: int | None = Query(None),
    day: int | None = Query(None),
    limit: int = Query(300),
):
    """
    📥 이력 엑셀 다운로드
    - 입고 / 출고 / 이동 / 롤백 전체 포함
    """

    rows = query_history(
        year=year,
        month=month,
        day=day,
        limit=limit,
    )

    if not rows:
        rows = []

    columns = [
        ("type", "구분"),
        ("warehouse", "창고"),
        ("operator", "작업자"),
        ("brand", "브랜드"),
        ("item_code", "품번"),
        ("item_name", "품명"),
        ("lot", "LOT"),
        ("spec", "규격"),
        ("from_location", "출발로케이션"),
        ("to_location", "도착로케이션"),
        ("qty", "수량"),
        ("note", "비고"),
        ("created_at", "일시"),
    ]

    data = rows_to_xlsx_bytes(
        rows,
        columns,
        sheet_name="이력",
    )

    filename = f"history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    return StreamingResponse(
        iter([data]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        },
    )
