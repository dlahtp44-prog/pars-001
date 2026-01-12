from fastapi import APIRouter, Form, HTTPException
from app.db import get_db, rollback_history

router = APIRouter(prefix="/api/rollback", tags=["Rollback"])

@router.post("/batch")
def rollback_batch(
    batch_id: str = Form(...),
    operator: str = Form(""),
    note: str = Form("")
):
    conn = get_db()
    try:
        cur = conn.cursor()

        cur.execute("""
            SELECT id FROM history
            WHERE batch_id = ?
              AND rolled_back = 0
            ORDER BY id DESC
        """, (batch_id,))
        rows = cur.fetchall()

        if not rows:
            raise HTTPException(status_code=404, detail="롤백할 이력이 없습니다.")

        for r in rows:
            rollback_history(r["id"], operator, note or f"배치롤백:{batch_id}")

        return {
            "ok": True,
            "batch_id": batch_id,
            "count": len(rows)
        }

    finally:
        conn.close()
