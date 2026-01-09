from fastapi import Request, HTTPException

# ✅ 6인 고정 계정
USERS = {
    "user1": "1234",
    "user2": "1234",
    "user3": "1234",
    "user4": "1234",
    "user5": "1234",
    "user6": "1234",
}

SESSION_KEY = "login_user"


def login_user(request: Request, username: str, password: str):
    if USERS.get(username) != password:
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호 오류")

    request.session[SESSION_KEY] = username


def logout_user(request: Request):
    request.session.pop(SESSION_KEY, None)


def require_login(request: Request):
    if SESSION_KEY not in request.session:
        raise HTTPException(status_code=401)
