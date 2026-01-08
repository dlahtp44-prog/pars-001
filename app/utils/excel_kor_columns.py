from typing import Dict, List, Tuple

# v1.6.1: 출고 엑셀 한글 컬럼 고정(운영 안정판)
REQUIRED = ["창고","로케이션","브랜드","품번","품명","LOT","규격","수량"]
OPTIONAL = ["비고"]

def normalize_header(s: str) -> str:
    if s is None:
        return ""
    s = str(s).strip()
    s = s.replace(" ", "")
    mapping = {
        # 창고
        "창고":"창고","WAREHOUSE":"창고","Warehouse":"창고",
        # 로케이션
        "로케이션":"로케이션","LOCATION":"로케이션","Loc":"로케이션",
        # 브랜드
        "브랜드":"브랜드","BRAND":"브랜드","Brand":"브랜드",
        # 품번/품명
        "품번":"품번","ITEMCODE":"품번","ItemCode":"품번",
        "품명":"품명","ITEMNAME":"품명","ItemName":"품명",
        # LOT/규격/수량/비고
        "LOT":"LOT","Lot":"LOT",
        "규격":"규격","SPEC":"규격","Spec":"규격",
        "수량":"수량","QTY":"수량","Qty":"수량","수량(PCS)":"수량",
        "비고":"비고","NOTE":"비고","Note":"비고",
    }
    return mapping.get(s, s)

def build_col_index(headers: List[str]) -> Dict[str,int]:
    idx={}
    for i,h in enumerate(headers):
        nh=normalize_header(h)
        if nh and nh not in idx:
            idx[nh]=i
    return idx

def validate_required(idx: Dict[str,int]) -> Tuple[bool, List[str]]:
    missing=[c for c in REQUIRED if c not in idx]
    return (len(missing)==0, missing)
