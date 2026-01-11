from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.auth import (
    login_user,
    logout_user,
    change_password,
)

templates = Jinja2Templates(directory="app/templates")

router = APIRouter()


# =========================
# LOGIN PAGE
# =========================
@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request}
    )


# =========================
# LOGIN ACTION
# =========================
@router.post("/login")
def login_action(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    login_user(request, username, password)
    return RedirectResponse("/", status_code=303)


# =========================
# PASSWORD CHANGE
# =========================
@router.post("/login/change")
def password_change(
    request: Request,
    username: str = Form(...),
    old_password: str = Form(...),
    new_password: str = Form(...),
):
    change_password(
        username=username,
        old_password=old_password,
        new_password=new_password,
    )

    # 변경 성공 → 로그인 화면으로
    return RedirectResponse("/login", status_code=303)


# =========================
# LOGOUT
# =========================
@router.get("/logout")
def logout(request: Request):
    logout_user(request)
    return RedirectResponse("/login", status_code=303)
