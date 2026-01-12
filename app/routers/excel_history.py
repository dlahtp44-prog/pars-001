from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
import io
import pandas as pd

from app.db import query_history

router = APIRouter(
    prefix="/api/excel",
    tags=["Excel"]
)


@router.get("/history")
def download_history_excel(
    year: int | None = Query(None),
    month: int | None = Query(None),
    day: int | None = Query(None),
    limit: int = Query(300),
):
    rows = query_history(
        year=year,
        month=month,
        day=day,
        limit=limit
    )

    data = []
    for r in rows:
        data.append(dict(r))

    df = pd.DataFrame(data)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="history")

    output.seek(0)

    filename = "history.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
