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

    # 🔥 핵심: utf-8-sig (BOM 포함)
    output = io.StringIO()
    writer = csv.writer(output)

    # ✅ 컬럼명 (엑셀용 한글)
    writer.writerow([
        "시간",
        "유형",
        "창고",
        "출발지",
        "도착지",
        "브랜드",
        "품번",
        "품명",
        "LOT",
        "규격",
        "수량",
        "비고",
        "작업자",
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

    csv_text = output.getvalue()
    output.close()

    # 🔥 BOM 붙이기
    bom_csv = "\ufeff" + csv_text

    return StreamingResponse(
        io.BytesIO(bom_csv.encode("utf-8")),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": "attachment; filename=history_export.csv"
        }
    )
