from fastapi import APIRouter, Query
from app.db import query_io_stats

router = APIRouter(
    prefix="/api/stats",
    tags=["stats"]
)

@router.get("/io")
def io_stats(
    start: str = Query(..., description="시작일 YYYY-MM-DD"),
    end: str = Query(..., description="종료일 YYYY-MM-DD"),
):
    rows = query_io_stats(start, end)

    result = {}
    for day, t, qty in rows:
        result.setdefault(day, {"IN": 0, "OUT": 0})
        result[day][t] = qty

    return result
