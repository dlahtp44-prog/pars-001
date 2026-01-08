from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR
from app.db import query_all_history
from app.utils.excel_export import rows_to_xlsx_bytes

router = APIRouter(prefix="/page/history", tags=["page-history"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _to_int(v: str | None):
    if v is None:
        return None
    v = v.strip()
    if v == "":
        return None
    try:
        return int(v)
    except ValueError:
        return None


# =====================================================
# 📌 통합 이력 화면 (이동 / 출고 / CS)
# =====================================================

@router.get("", response_class=HTMLResponse)
def page(
    request: Request,
    year: str | None = None,
    month: str | None = None,
    limit: int = 300,
):
    rows = query_all_history(
        limit=limit,
        year=_to_int(year),
        month=_to_int(month),
    )

    return templates.TemplateResponse(
        "history.html",
        {
            "request": request,
            "rows": rows,
            "year": year or "",
            "month": month or "",
            "limit": limit,
        },
    )


# =====================================================
# 📌 통합 이력 엑셀 다운로드
# =====================================================

@router.get("/excel")
def download_excel(
    year: str | None = None,
    month: str | None = None,
    limit: int = 2000,
):
    rows = query_all_history(
        limit=limit,
        year=_to_int(year),
        month=_to_int(month),
    )

    columns = [
        ("created_at", "시간"),
        ("type", "유형"),          # 입고 / 출고 / 이동 / CS
        ("warehouse", "창고"),
        ("location", "로케이션"),
        ("brand", "브랜드"),
        ("item_code", "품번"),
        ("item_name", "품명"),
        ("lot", "LOT"),
        ("spec", "규격"),
        ("qty", "수량"),           # CS는 음수
        ("note", "비고"),          # history.note / damage.detail
    ]

    data = rows_to_xlsx_bytes(
        rows,
        columns,
        sheet_name="통합이력"
    )

    return StreamingResponse(
        iter([data]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": 'attachment; filename="history_all.xlsx"'
        },
    )
