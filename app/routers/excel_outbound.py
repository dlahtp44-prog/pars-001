from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import openpyxl
import io
from datetime import datetime
from decimal import Decimal

from app.db import query_inventory, upsert_inventory, add_history
from app.utils.excel_kor_columns import build_col_index

router = APIRouter(prefix="/api/excel/outbound", tags=["excel-outbound"])


# =====================================
# 🔥 수량 파싱 (소수점 유지)
# =====================================
def _parse_qty(v) -> float:
    try:
        if v is None or str(v).strip() == "":
            return 0.0
        return float(Decimal(str(v)))
    except Exception:
        raise ValueError("수량 형식 오류")


@router.post("")
async def excel_outbound(
    operator: str = Form(""),
    file: UploadFile = File(...)
):
    """
    출고 엑셀 업로드 (v1.7)

    ✅ 필수 컬럼
      - 로케이션
      - 품번
      - 수량

    ⭕ 선택 컬럼
      - 창고
      - 브랜드
      - 품명
      - LOT
      - 규격
      - 비고

    📌 LOT / 규격 없어도 출고 가능
    """

    if not file.filename.lower().endswith((".xlsx", ".xlsm", ".xltx", ".xltm")):
        raise HTTPException(
            status_code=400,
            detail="엑셀(.xlsx) 파일만 업로드 가능합니다."
        )

    batch_id = datetime.now().strftime("%Y%m%d_%H%M%S_excel_outbound")

    data = await file.read()
    wb = openpyxl.load_workbook(filename=io.BytesIO(data), data_only=True)
    ws = wb.active

    headers = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]
    idx = build_col_index(headers)

    # 🔥 필수 컬럼 (LOT/규격 제거)
    required_cols = ["로케이션", "품번", "수량"]
    missing = [c for c in required_cols if c not in idx]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"필수 컬럼 누락: {', '.join(missing)}"
        )

    success = 0
    fail = 0
    errors = []

    for r_i, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if row is None or all(v is None or str(v).strip() == "" for v in row):
            continue

        try:
            warehouse = str(row[idx["창고"]] or "").strip() if "창고" in idx else ""
            brand = str(row[idx["브랜드"]] or "").strip() if "브랜드" in idx else ""
            item_name = str(row[idx["품명"]] or "").strip() if "품명" in idx else ""

            location = str(row[idx["로케이션"]] or "").strip()
            item_code = str(row[idx["품번"]] or "").strip()
            lot = str(row[idx["LOT"]] or "").strip() if "LOT" in idx else ""
            spec = str(row[idx["규격"]] or "").strip() if "규격" in idx else ""
            note = str(row[idx["비고"]] or "").strip() if "비고" in idx else ""

            qty = _parse_qty(row[idx["수량"]])

            if not (location and item_code):
                raise ValueError("필수 값(로케이션/품번) 누락")

            if qty <= 0:
                raise ValueError("수량은 0보다 커야 합니다.")

            # =====================================
            # 🔥 재고 조회 (LOT/규격 조건부)
            # =====================================
            rows = query_inventory(
                warehouse=warehouse,
                location=location,
                brand=brand,
                item_code=item_code,
                lot=lot if lot else None,
                spec=spec if spec else None,
            )

            if not rows:
                raise ValueError("출고 가능한 재고가 없습니다.")

            remain = qty

            for r in rows:
                if remain <= 0:
                    break

                take = min(float(r["qty"]), remain)

                ok = upsert_inventory(
                    r["warehouse"],
                    r["location"],
                    r["brand"],
                    r["item_code"],
                    r["item_name"],
                    r["lot"],
                    r["spec"],
                    -take,
                    note,
                )
                if not ok:
                    raise ValueError("재고 차감 실패")

                add_history(
                    "출고",
                    r["warehouse"],
                    operator,
                    r["brand"],
                    r["item_code"],
                    r["item_name"],
                    r["lot"],
                    r["spec"],
                    r["location"],
                    "",
                    take,
                    note,
                    batch_id=batch_id,
                )

                remain -= take

            if remain > 0:
                raise ValueError("출고 수량이 재고보다 많습니다.")

            success += 1

        except Exception as e:
            fail += 1
            errors.append({
                "row": r_i,
                "error": str(e),
            })

    return {
        "ok": True,
        "success": success,
        "fail": fail,
        "batch_id": batch_id,
        "errors": errors[:50],
    }
