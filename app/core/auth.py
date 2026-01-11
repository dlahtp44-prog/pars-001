from fastapi import Request, HTTPException

# ✅ 6인 고정 계정 (이름 = 아이디)
# ⚠️ 메모리 기반 (서버 재시작 시 초기화됨)
USERS = {
    "양동규": {"password": "1234"},
    "박상칠": {"password": "1234"},
    "김광현": {"password": "1234"},
    "이모세": {"password": "1234"},
    "인어진": {"password": "1234"},
    "user1": {"password": "1234"},
}

SESSION_KEY = "login_user"


# =====================================================
# LOGIN
# =====================================================
def login_user(request: Request, username: str, password: str):
    user = USERS.get(username)
    if not user or user["password"] != password:
        raise HTTPException(status_code=401, detail="이름 또는 비밀번호 오류")

    request.session[SESSION_KEY] = username


# =====================================================
# PASSWORD CHANGE
# =====================================================
def change_password(username: str, old_password: str, new_password: str):
    user = USERS.get(username)
    if not user:
        raise HTTPException(status_code=404, detail="존재하지 않는 사용자")

    if user["password"] != old_password:
        raise HTTPException(status_code=401, detail="기존 비밀번호 오류")

    if len(new_password) < 4:
        raise HTTPException(status_code=400, detail="비밀번호는 4자리 이상이어야 합니다")

    user["password"] = new_password


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
