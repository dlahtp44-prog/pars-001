from fastapi import APIRouter, Form, HTTPException
from app.db import rollback_history, query_history

router = APIRouter(prefix="/api/rollback", tags=["rollback"])


@router.post("/batch")
def rollback_batch_api(
    batch_id: str = Form(...),
    operator: str = Form("SYSTEM"),
    note: str = Form("")
):
    """
    엑셀 업로드 batch_id 기준 전체 롤백
    - 가능한 이력만 롤백
    - 실패 건은 스킵
    - 전체는 성공 처리
    """

    if not batch_id:
        raise HTTPException(400, "batch_id는 필수입니다.")

    # 🔹 해당 batch 이력 조회 (아직 롤백 안 된 것만)
    rows = query_history(limit=10_000)
    targets = [
        r for r in rows
        if r.get("batch_id") == batch_id and r.get("rolled_back", 0) == 0
    ]

    if not targets:
        raise HTTPException(404, "롤백 대상 이력이 없습니다.")

    success = 0
    failed = []

    for r in targets:
        try:
            rollback_history(
                r["id"],
                operator,
                note or f"배치롤백:{batch_id}"
            )
            success += 1
        except Exception as e:
            failed.append({
                "history_id": r["id"],
                "error": str(e)
            })
            continue

    return {
        "ok": True,
        "batch_id": batch_id,
        "total": len(targets),
        "success": success,
        "failed": failed,
        "message": f"총 {len(targets)}건 중 {success}건 롤백 완료"
    }
