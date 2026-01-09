from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR

router = APIRouter(
    prefix="/page/labels",
    tags=["라벨 페이지"]
)

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("", response_class=HTMLResponse)
def label_home(request: Request):
    """
    라벨 출력 메인 페이지
    """
    return templates.TemplateResponse(
        "labels/index.html",
        {"request": request}
    )
