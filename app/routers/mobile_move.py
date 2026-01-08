from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR

router = APIRouter(prefix="/m/move", tags=["mobile-move"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# 1️⃣ 출발 로케이션 화면
@router.get("/from", response_class=HTMLResponse)
def move_from(request: Request, location: str):
    return templates.TemplateResponse(
        "m/move_from.html",
        {"request": request, "from_location": location},
    )


# 2️⃣ 출발 로케이션 확정
@router.post("/from/submit")
def move_from_submit(
    from_location: str = Form(...)
):
    return RedirectResponse(
        url=f"/m/move/select?from_location={from_location}",
        status_code=303,
    )
