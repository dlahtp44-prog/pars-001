from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter(prefix="/opening", tags=["Page"], include_in_schema=False)

@router.get("/")
def opening():
    # 초기 진입 페이지가 필요하면 여기서 로그인/안내 화면으로 연결하면 됩니다.
    return RedirectResponse(url="/", status_code=302)
