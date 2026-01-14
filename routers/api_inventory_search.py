from fastapi import APIRouter, Query
from app.db import get_db

router = APIRouter(prefix="/api/inventory-search", tags=["inventory-search"])


@router.get("")
def inventory_search(q: str = Query(..., min_length=1)):
    """
    품번 검색 → 현재고 목록 반환
    """
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            warehouse,
            location,
            brand,
            item_code,
            item_name,
            lot,
            spec,
            SUM(qty) as qty
        FROM inventory
        WHERE item_code LIKE ?
          AND qty > 0
        GROUP BY warehouse, location, brand, item_code, item_name, lot, spec
        ORDER BY item_code, lot
        LIMIT 20
        """,
        (f"%{q}%",)
    )

    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows
