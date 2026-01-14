from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR

router = APIRouter(
    prefix="/page/labels",
    tags=["라벨 페이지"]
)

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# =========================
# 라벨 센터 메인
# =========================
@router.get("", response_class=HTMLResponse)
def labels_index(request: Request):
    return templates.TemplateResponse(
        "labels/index.html",
        {"request": request}
    )


# =========================
# 제품 라벨 페이지
# =========================
@router.get("/product", response_class=HTMLResponse)
def labels_product(request: Request):
    return templates.TemplateResponse(
        "labels/product.html",
        {"request": request}
    )


# =========================
# 로케이션 라벨 페이지
# =========================
@router.get("/location", response_class=HTMLResponse)
def labels_location(request: Request):
    return templates.TemplateResponse(
        "labels/location.html",
        {"request": request}
    )
