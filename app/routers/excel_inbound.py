from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import openpyxl
import io

from app.db import upsert_inventory, add_history
from app.utils.excel_kor_columns import build_col_index


router = APIRouter(prefix="/api/excel/inbound", tags=["excel-inbound"])


@router.post("")
async def excel_inbound(
    operator: str = Form(""),
    file: UploadFile = File(...)
):
    """
    입고 엑셀 업로드 (한글 컬럼 고정)

    ✅ 필수 컬럼(최소):
      - 창고
      - 로케이션
      - 품번
      - 수량

    ⭕ 선택 컬럼:
      - 브랜드
      - 품명
      - LOT
      - 규격
      - 비고

    📌 수량이 0 / 음수 / 빈값인 행은
       에러 ❌ → 자동 스킵 ⭕
    """

    if not file.filename.lower().endswith((".xlsx", ".xlsm", ".xltx", ".xltm")):
        raise HTTPException(
            status_code=400,
            detail="엑셀(.xlsx) 파일만 업로드 가능합니다."
        )

    data = await file.read()
    wb = openpyxl.load_workbook(
        filename=io.BytesIO(data),
        data_only=True
    )
    ws = wb.active

    # ===============================
    # HEADER
    # ===============================
    headers = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]
    idx = build_col_index(headers)

    # 🔑 최소 필수 컬럼만 체크
    required_cols = ["창고", "로케이션", "품번", "수량"]
    missing = [c for c in required_cols if c not in idx]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"필수 컬럼 누락: {', '.join(missing)}"
        )

    success = 0
    fail = 0
    skipped = 0
    errors = []

    # ===============================
    # ROW LOOP
    # ===============================
    for r_i, row in enumerate(
        ws.iter_rows(min_row=2, values_only=True),
        start=2
    ):
        # 완전 빈 행 스킵
        if row is None or all(v is None or str(v).strip() == "" for v in row):
            continue

        try:
            # ===============================
            # 필수
            # ===============================
            warehouse = str(row[idx["창고"]] or "").strip()
            location = str(row[idx["로케이션"]] or "").strip()
            item_code = str(row[idx["품번"]] or "").strip()
            qty_raw = row[idx["수량"]]

            # 선택
            brand = str(row[idx["브랜드"]] or "").strip() if "브랜드" in idx else ""
            item_name = str(row[idx["품명"]] or "").strip() if "품명" in idx else ""
            lot = str(row[idx["LOT"]] or "").strip() if "LOT" in idx else ""
            spec = str(row[idx["규격"]] or "").strip() if "규격" in idx else ""
            note = str(row[idx["비고"]] or "").strip() if "비고" in idx else ""

            # 필수값 검증
            if not (warehouse and location and item_code):
                raise ValueError("필수 값(창고/로케이션/품번) 누락")

            # ===============================
            # 수량 처리 (핵심 수정 부분)
            # ===============================
            if qty_raw is None or str(qty_raw).strip() == "":
                skipped += 1
                continue

            try:
                qty = int(qty_raw)
            except Exception:
                skipped += 1
                continue

            if qty <= 0:
                # ❌ 에러 아님 → 자동 스킵
                skipped += 1
                continue

            # ===============================
            # INVENTORY
            # ===============================
            ok = upsert_inventory(
                warehouse=warehouse,
                location=location,
                brand=brand,
                item_code=item_code,
                item_name=item_name,
                lot=lot,
                spec=spec,
                qty_delta=qty,
                note=note,
            )
            if not ok:
                raise ValueError("재고 반영 실패")

            # ===============================
            # HISTORY
            # ===============================
            add_history(
                "입고",
                warehouse,
                operator,
                brand,
                item_code,
                item_name,
                lot,
                spec,
                "",
                location,
                qty,
                note,
            )

            success += 1

        except Exception as e:
            fail += 1
            errors.append({
                "row": r_i,
                "error": str(e)
            })

    return {
        "ok": True,
        "success": success,
        "skipped": skipped,
        "fail": fail,
        "errors": errors[:50],  # 너무 길어지지 않게
    }
