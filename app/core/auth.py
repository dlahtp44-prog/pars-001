from fastapi import Request, HTTPException

# ✅ 고정 계정 (이름 → 비밀번호)
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


# =========================
# PASSWORD CHANGE
# =========================
def change_password(username: str, old_password: str, new_password: str):
    if username not in USERS:
        raise HTTPException(status_code=400, detail="존재하지 않는 사용자입니다.")

    if USERS[username] != old_password:
        raise HTTPException(status_code=400, detail="기존 비밀번호가 올바르지 않습니다.")

    if not new_password or len(new_password) < 4:
        raise HTTPException(status_code=400, detail="새 비밀번호는 4자리 이상이어야 합니다.")

    USERS[username] = new_password



# =====================================================
# LOGOUT
# =====================================================
def logout_user(request: Request):
    request.session.pop(SESSION_KEY, None)


# =====================================================
# LOGIN CHECK (페이지 보호용)
# =====================================================
def require_login(request: Request):
    if SESSION_KEY not in request.session:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다")
