from fastapi import Request, HTTPException

# ✅ 6인 고정 계정
USERS = {
    "양동규": "1234",
    "박상칠": "1234",
    "김광현": "1234",
    "이모세": "1234",
    "인어진": "1234",
    "user1": "1234",
}

SESSION_KEY = "login_user"


def login_user(request: Request, username: str, password: str):
    if USERS.get(username) != password:
        raise HTTPException(status_code=401, detail="이름 또는 비밀번호 오류")


    request.session[SESSION_KEY] = username


def logout_user(request: Request):
    request.session.pop(SESSION_KEY, None)


def require_login(request: Request):
    if SESSION_KEY not in request.session:
        raise HTTPException(status_code=401)
