
from fastapi import APIRouter, HTTPException
from app.core.database import get_conn

router = APIRouter(prefix="/location", tags=["Location"])


@router.post("/add")
def add_location(warehouse: str, location: str):
    conn = get_conn()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO locations (warehouse, location)
            VALUES (?, ?)
        """, (warehouse, location))
        conn.commit()
    except:
        raise HTTPException(400, "이미 등록된 Location")

    finally:
        conn.close()

    return {"result": "OK"}


@router.get("/list")
def list_locations():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM locations ORDER BY warehouse, location")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows
