from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.db import query_io_group_stats

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/page/io-advanced", response_class=HTMLResponse)
def io_advanced_page(
    request: Request,
    start: str = "",
    end: str = "",
    group: str = "item",
    brand: str = "",
    keyword: str = "",
):
    """
    고급 입·출고 통계
    - 그룹: brand / item / spec
    - 기간 내 입고 / 출고 / 순증감
    """

    rows = []

    # 날짜가 둘 다 있을 때만 조회
    if start and end:
        rows = query_io_group_stats(
            start_date=start,
            end_date=end,
            group=group,
            brand=brand,
            keyword=keyword,
        )

    return templates.TemplateResponse(
        "io_advanced.html",
        {
            "request": request,

            # 검색 조건 유지
            "start": start,
            "end": end,
            "group": group,
            "brand": brand,
            "keyword": keyword,

            # 결과
            "rows": rows,
        },
    )
