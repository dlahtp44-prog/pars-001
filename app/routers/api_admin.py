from fastapi import APIRouter, HTTPException

from app.db import reset_inventory_and_history

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/reset-all")
def reset_all():
    """
    ⚠️ 재고 + 이력 전체 초기화
    """
    try:
        reset_inventory_and_history()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "ok": True,
        "message": "재고 + 이력 초기화 완료"
    }
