from decimal import Decimal

def display_qty(value) -> str:
    """
    표시용 수량 포맷
    - 정수: 10
    - 소수: 최대 소수점 3자리 (불필요한 0 제거)
    """
    if value is None:
        return "0"

    d = Decimal(str(value)).normalize()
    return format(d, "f")
