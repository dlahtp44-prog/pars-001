from __future__ import annotations

from typing import Dict, List, Tuple, Optional

# =====================================================
# 한글 컬럼 고정 + (유연한) 별칭 허용
# =====================================================

# 표준 컬럼명 (서비스 내부에서 쓰는 키)
STD_COLS = [
    "창고",
    "로케이션",
    "브랜드",
    "품번",
    "품명",
    "LOT",
    "규격",
    "수량",
    "비고",
]

# 엑셀 헤더에 들어올 수 있는 별칭 → 표준 컬럼명
ALIASES = {
    # warehouse
    "창고": "창고", "warehouse": "창고", "WAREHOUSE": "창고",
    # location
    "로케이션": "로케이션", "location": "로케이션", "LOCATION": "로케이션",
    "위치": "로케이션",
    # brand
    "브랜드": "브랜드", "brand": "브랜드", "BRAND": "브랜드",
    # item_code
    "품번": "품번", "item_code": "품번", "ITEM_CODE": "품번", "코드": "품번",
    # item_name
    "품명": "품명", "item_name": "품명", "ITEM_NAME": "품명",
    # LOT
    "LOT": "LOT", "Lot": "LOT", "lot": "LOT",
    # spec
    "규격": "규격", "spec": "규격", "SPEC": "규격",
    # qty
    "수량": "수량", "qty": "수량", "QTY": "수량", "수 량": "수량",
    # note
    "비고": "비고", "note": "비고", "NOTE": "비고",
}

REQUIRED_DEFAULT = ["창고", "로케이션", "브랜드", "품번", "품명", "LOT", "규격", "수량"]


def _norm_header(v) -> str:
    return str(v or "").strip()


def build_col_index(headers: List[str]) -> Dict[str, int]:
    """엑셀 헤더(1행)에서 표준 컬럼명 → index 매핑 생성"""
    idx: Dict[str, int] = {}
    for i, h in enumerate(headers):
        key = _norm_header(h)
        if not key:
            continue
        std = ALIASES.get(key, key)
        if std in STD_COLS and std not in idx:
            idx[std] = i
    return idx


def validate_required(idx: Dict[str, int], required: Optional[List[str]] = None) -> Tuple[bool, List[str]]:
    required = required or REQUIRED_DEFAULT
    missing = [c for c in required if c not in idx]
    return (len(missing) == 0, missing)
