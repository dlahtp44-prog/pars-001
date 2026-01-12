# app/routers/api_admin_reset.py

from fastapi import APIRouter, Form, HTTPException
from datetime import datetime

from app.db import get_db

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/reset-all")
def reset_inventory_and_history(
    confirm: str = Form(...),
    operator: str = Form("SYSTEM"),
):
    """
    ⚠️ 재고 + 이력 전체 초기화 (되돌릴 수 없음)
    - 관리자 전용
    - confirm="RESET" 필수
    """

    if confirm != "RESET":
        raise HTTPException(
            status_code=400,
            detail="확인 문구가 올바르지 않습니다. 'RESET' 을 입력하세요."
        )

    conn = get_db()
    try:
        cur = conn.cursor()

        # 🔥 전체 삭제
        cur.execute("DELETE FROM inventory")
        cur.execute("DELETE FROM history")

        conn.commit()

    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"전체 리셋 중 오류 발생: {e}"
        )
    finally:
        conn.close()

    return {
        "ok": True,
        "message": "재고 및 이력 전체 초기화 완료",
        "operator": operator,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }
