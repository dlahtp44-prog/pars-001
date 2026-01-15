from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR
from app.db import query_history
from app.core.qty import display_qty
from app.utils.excel_export import rows_to_xlsx_bytes

router = APIRouter(prefix="/page/history", tags=["page-history"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _to_int(v):
    try:
        return int(v) if v else None
    except ValueError:
        return None


def format_rows(rows):
    view_rows = []

    for r in rows:
        d = dict(r)

        # =========================
        # 기본 안전 처리
        # =========================
        d["lot"] = d.get("lot", "") or ""
        d["spec"] = d.get("spec", "") or ""

        # 수량 표시용 (0도 허용)
        raw_qty = d.get("qty")
        d["qty"] = display_qty(raw_qty)

        # =========================
        # 타입 통일 (io_type ↔ type)
        # =========================
        io_type = d.get("io_type") or d.get("type") or ""
        d["type"] = io_type

        # =========================
        # 롤백 가능 여부
        # =========================
        d["can_rollback"] = (
            io_type in ("입고", "출고", "이동", "초기재고")
            and not d.get("rolled_back", 0)
        )

        view_rows.append(d)

    return view_rows


@router.get("", response_class=HTMLResponse)
def page(
    request: Request,
    year: str | None = None,
    month: str | None = None,
    day: str | None = None,
    limit: int = 300,
):
    rows = query_history(
        limit=limit,
        year=_to_int(year),
        month=_to_int(month),
        day=_to_int(day),
    )

    return templates.TemplateResponse(
        "history.html",
        {
            "request": request,
            "rows": _format_rows(rows),
            "year": year or "",
            "month": month or "",
            "day": day or "",
            "limit": limit,
        },
    )
