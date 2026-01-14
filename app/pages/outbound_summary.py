from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.core.paths import TEMPLATES_DIR
from app.db import query_outbound_summary

router = APIRouter(prefix="/page/outbound-summary", tags=["outbound-summary"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("", response_class=HTMLResponse)
def outbound_summary_page(
    request: Request,
    year: int | None = Query(None),
    month: int | None = Query(None),
):
    """
    출고 통계 페이지
    - year 없음 → 연도별
    - year 있음 → 월별
    - year + month → 일별
    """
    rows = query_outbound_summary(year=year, month=month)

    return templates.TemplateResponse(
        "outbound_summary.html",
        {
            "request": request,
            "rows": rows,
            "year": year,
            "month": month,
        },
    )
