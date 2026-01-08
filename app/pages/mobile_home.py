from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import date

from app.core.paths import TEMPLATES_DIR

router = APIRouter(prefix="/m", tags=["mobile"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("", response_class=HTMLResponse)
def m_home(request: Request):
    """
    📱 모바일 홈
    - QR 스캔
    - 재고 조회
    - 이동
    - CS 등록 진입 허브
    """
    return templates.TemplateResponse(
        "m/home.html",
        {
            "request": request,
            "today": date.today().isoformat(),
            "warehouse": "",
        },
    )
