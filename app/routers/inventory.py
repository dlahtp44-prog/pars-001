from fastapi import APIRouter
from app.core.database import get_conn

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("/")
def inventory(
    item_code: str = "",
    lot_no: str = "",
    warehouse: str = "",
    location: str = "",
):
    conn = get_conn()
    cur = conn.cursor()

    sql = """
        SELECT item_code, lot_no, warehouse, location, SUM(qty) AS qty
        FROM inventory_tx
        WHERE 1=1
    """
    params = []

    if item_code:
        sql += " AND item_code=?"
        params.append(item_code)
    if lot_no:
        sql += " AND lot_no=?"
        params.append(lot_no)
    if warehouse:
        sql += " AND warehouse=?"
        params.append(warehouse)
    if location:
        sql += " AND location=?"
        params.append(location)

    sql += " GROUP BY item_code, lot_no, warehouse, location HAVING qty <> 0"

    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

