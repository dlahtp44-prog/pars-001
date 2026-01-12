from fastapi import APIRouter, Form, HTTPException
from app.db import rollback_batch

router = APIRouter(prefix="/api/rollback", tags=["rollback"])

@router.post("/batch")
def rollback_batch_api(
    batch_id: str = Form(...),
    operator: str = Form("SYSTEM"),
    note: str = Form("")
):
    try:
        count = rollback_batch(batch_id, operator, note)
        if count == 0:
            raise HTTPException(404, "롤백 대상 없음")

        return {
            "ok": True,
            "batch_id": batch_id,
            "rolled_back_count": count
        }

    except Exception as e:
        raise HTTPException(500, str(e))
