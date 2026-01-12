from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.db import query_history
import csv
import io

router = APIRouter(
    prefix="/page/history/excel",
    tags=["history-excel"]
)

@router.get("")
def download_history_excel(
    year: int | None = None,
    month: int | None = None,
    day: int | None = None,
):
    rows = query_history(year=year, month=month, day=day, limit=5000)

    output = io.StringIO()
    writer = csv.writer(output)

    # 헤더
    writer.writerow([
        "시간", "유형", "창고", "출발", "도착",
        "브랜드", "품번", "품명", "LOT", "규격",
        "수량", "비고", "작업자"
    ])

    for r in rows:
        writer.writerow([
            r["created_at"],
            r["type"],
            r["warehouse"],
            r["from_location"],
            r["to_location"],
            r["brand"],
            r["item_code"],
            r["item_name"],
            r["lot"],
            r["spec"],
            r["qty"],
            r["note"],
            r["operator"],
        ])

    output.seek(0)

    filename = "history_export.csv"
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
