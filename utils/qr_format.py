import re

# =====================================================
# ✅ 품목 QR 생성 (단일 / 통일)
# =====================================================
def build_item_qr(
    item_code: str,
    item_name: str,
    lot: str,
    spec: str,
    brand: str = "",
) -> str:
    """
    [통일 QR 포맷]
    품번:xxx/품명:xxx/LOT:xxx/규격:xxx/브랜드:xxx

    - PC / 모바일 / 라벨 / CS 공용
    - brand 는 선택값
    """
    parts = [
        f"품번:{item_code.strip()}",
        f"품명:{item_name.strip()}",
        f"LOT:{lot.strip()}",
        f"규격:{spec.strip()}",
    ]

    if brand:
        parts.append(f"브랜드:{brand.strip()}")

    return "/".join(parts)


# =====================================================
# 품목 QR 판별
# =====================================================
def is_item_qr(text: str) -> bool:
    return "품번:" in text and "LOT:" in text


# =====================================================
# 품목 QR 필드 추출
# =====================================================
def extract_item_fields(text: str):
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
# ✅ 로케이션 QR → location 값만 추출 (🔥 핵심 수정)
# =====================================================
def extract_location_only(text: str) -> str:
    """
    지원 QR 포맷 (모두 정상 처리):

    1) LOCATION:A01-05-02
    2) location=A01-05-02
    3) type=LOC&warehouse=MAIN&location=D01-01
    4) A01-05-02 (순수 값)

    → 결과: A01-05-02
    """
    if not text:
        return ""

    t = text.strip()

    # LOCATION:A01-05-02
    if t.upper().startswith("LOCATION:"):
        return t.split(":", 1)[1].strip()

    # type=LOC&warehouse=MAIN&location=D01-01
    if "location=" in t:
        return t.split("location=", 1)[1].strip()

    # 그냥 순수 로케이션 값
    return t
