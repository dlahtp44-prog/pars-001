from __future__ import annotations

import re


# =====================================================
# 품목 QR 생성 (단일 / 통일)
# =====================================================
def build_item_qr(
    item_code: str,
    item_name: str,
    lot: str,
    spec: str,
    brand: str = "",
) -> str:
    """[통일 QR 포맷]
    품번:xxx/품명:xxx/LOT:xxx/규격:xxx/브랜드:xxx (브랜드 선택)
    """
    parts = [
        f"품번:{(item_code or '').strip()}",
        f"품명:{(item_name or '').strip()}",
        f"LOT:{(lot or '').strip()}",
        f"규격:{(spec or '').strip()}",
    ]
    if brand:
        parts.append(f"브랜드:{brand.strip()}")
    return "/".join(parts)


def is_item_qr(text: str) -> bool:
    text = text or ""
    return "품번:" in text and "LOT:" in text


def extract_item_fields(text: str):
    text = text or ""

    def pick(label):
        m = re.search(rf"{label}\s*:\s*([^/]+)", text)
        return m.group(1).strip() if m else ""

    item_code = pick("품번")
    item_name = pick("품명")
    lot = pick("LOT")
    spec = pick("규격")
    brand = pick("브랜드")
    return item_code, item_name, lot, spec, brand


# =====================================================
# 로케이션 QR → location 값만 추출
# =====================================================
def extract_location_only(text: str) -> str:
    """QR 스캔 결과에서 로케이션 코드만 추출

    지원 예:
    - LOCATION:A01-05-02            -> A01-05-02
    - type=LOC&warehouse=MAIN&location=D01-01 -> D01-01
    - location=D01-01               -> D01-01
    - D01-01                        -> D01-01
    """
    raw = (text or "").strip()

    # 가장 흔한 포맷: LOCATION:XXXX
    if "LOCATION:" in raw:
        raw = raw.split("LOCATION:", 1)[1].strip()

    # querystring 포맷: ...location=XXX&...
    if "location=" in raw:
        raw = raw.split("location=", 1)[1]
        raw = raw.split("&", 1)[0].strip()

    return raw.strip()
