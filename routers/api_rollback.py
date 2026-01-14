from fastapi import APIRouter, Form, HTTPException

from app.db import rollback_history

router = APIRouter(prefix="/api/rollback", tags=["rollback"])


@router.post("")
def rollback(
    history_id: int = Form(...),
    operator: str = Form(""),
    note: str = Form(""),
):
    """
    🔁 공통 롤백 API

    대상:
    - 입고
    - 출고
    - 이동

    동작:
    1. history 단건 조회 (rolled_back=0 조건)
    2. 재고 원복
    3. 원본 history rolled_back = 1
       - rollback_at
       - rollback_by
       - rollback_note 기록
    4. history에 type='롤백' 이력 추가
    """

    if history_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="유효하지 않은 history_id 입니다.",
        )

    try:
        rollback_history(
            history_id=history_id,
            operator=operator.strip(),
            note=note.strip(),
        )

    except ValueError as e:
        # ❌ 이미 롤백되었거나 대상이 아닌 이력
        raise HTTPException(
            status_code=409,  # Conflict
            detail=str(e),
        )

    except Exception as e:
        # ❌ 시스템 오류 (DB / 로직 / 트랜잭션)
        raise HTTPException(
            status_code=500,
            detail="롤백 처리 중 오류가 발생했습니다.",
        )

    return {
        "ok": True,
        "history_id": history_id,
        "message": "롤백이 완료되었습니다.",
    }
