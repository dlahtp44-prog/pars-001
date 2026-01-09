from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR
from app.core.auth import require_login  # ✅ 로그인 체크

router = APIRouter()
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    # ✅ 로그인 안 되어 있으면 로그인 페이지로
    try:
        require_login(request)
    except:
        return RedirectResponse("/login", status_code=303)

    # ✅ 로그인 되어 있으면 메인 화면
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )
