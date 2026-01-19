from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from datetime import datetime
from app.db import query_history
from app.utils.excel_export import rows_to_xlsx_bytes

router = APIRouter(prefix="/api/excel/history", tags=["excel-history"])


# ============================================
# 🔧 빈 문자열 안전 처리
# ============================================
def _to_int(v: str | None):
    """
    "" 또는 None → None
    "2026" → 2026
    """
    if v is None or str(v).strip() == "":
        return None
    return int(v)


@router.get("")
def download_history_excel(
    year: str | None = Query(None),
    month: str | None = Query(None),
    day: str | None = Query(None),
    limit: int = Query(300),
):
    """
    📥 이력 엑셀 다운로드
    - 입고 / 출고 / 이동 / 롤백 전체 포함
    - 메인 이력 / 엑셀 센터 공용
    """

    year_i = _to_int(year)
    month_i = _to_int(month)
    day_i = _to_int(day)

    rows = query_history(
        year=year_i,
        month=month_i,
        day=day_i,
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
