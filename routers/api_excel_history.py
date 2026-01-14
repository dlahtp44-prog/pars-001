from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from datetime import datetime

from app.db import query_history
from app.utils.excel_export import rows_to_xlsx_bytes

router = APIRouter(prefix="/api/excel/history", tags=["excel-history"])


def _to_int_or_none(v: str | None):
    s = (v or "").strip()
    if not s:
        return None
    if s.isdigit():
        return int(s)
    return None


@router.get("")
def download_history_excel(
    year: str | None = Query(None),
    month: str | None = Query(None),
    day: str | None = Query(None),
    limit: int = Query(300),
):
    """📥 이력 엑셀 다운로드
    - year/month/day 를 비워도 422가 나지 않도록 내부에서 None 처리
    """

    y = _to_int_or_none(year)
    m = _to_int_or_none(month)
    d = _to_int_or_none(day)

    rows = query_history(year=y, month=m, day=d, limit=limit) or []

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

    data = rows_to_xlsx_bytes(rows, columns, sheet_name="이력")
    filename = f"history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    return StreamingResponse(
        iter([data]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
