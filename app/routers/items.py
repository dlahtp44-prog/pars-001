
from fastapi import APIRouter, HTTPException
from app.core.models import upsert_item
from app.core.database import get_conn

router = APIRouter(prefix="/items", tags=["Items"])


@router.get("/name")
def get_item_name(item_code: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT item_name, spec FROM items WHERE item_code=?", (item_code,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return {"item_name": "", "spec": ""}
    return {"item_name": row["item_name"], "spec": row["spec"]}


@router.post("/upsert")
def insert_item(item_code: str, item_name: str = "", spec: str = ""):
    if not item_code:
        raise HTTPException(400, "item_code is required")

    upsert_item(item_code, item_name, spec)
    return {"result": "OK"}
