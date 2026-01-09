from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(
    prefix="/page/labels",
    tags=["라벨"]
)

templates = Jinja2Templates(directory="app/templates")


@router.get("", response_class=HTMLResponse)
def labels_home(request: Request):
    return templates.TemplateResponse(
        "labels/product_print.html",
        {"request": request, "items": []}
    )
