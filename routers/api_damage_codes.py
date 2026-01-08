from fastapi import APIRouter
from app.db import list_damage_codes

router = APIRouter(prefix="/api/damage-codes", tags=["api-damage-codes"])

@router.get("")
def damage_codes(
    category: str = "",
    type: str = "",
    situation: str = "",
    active_only: bool = True,
):
    """파손/CS 분류 코드 조회 API
    - 프론트(페이지/모바일/관리자)에서 드롭다운 옵션으로 사용
    """
    rows = list_damage_codes(
        category=category,
        type=type,
        situation=situation,
        active_only=active_only,
    )
    return {"rows": rows}
