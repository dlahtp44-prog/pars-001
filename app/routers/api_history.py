from fastapi import APIRouter
from app.db import query_history

router = APIRouter(prefix="/api/history", tags=["api-history"])

@router.get("")
def history(
    year: int | None = None,
    month: int | None = None,
    day: int | None = None,
    limit: int = 200,
):
    return {"rows": query_history(limit=limit, year=year, month=month, day=day)}
