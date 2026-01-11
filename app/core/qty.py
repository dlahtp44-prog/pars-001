from decimal import Decimal, ROUND_HALF_UP

def normalize_qty(value) -> float:
    """
    수량을 소수점 3자리까지 반올림해서 float로 반환
    """
    if value is None:
        return 0.0

    d = Decimal(str(value)).quantize(
        Decimal("0.000"),
        rounding=ROUND_HALF_UP
    )
    return float(d)


def display_qty(value) -> str:
    """
    표시용:
    - 정수면 10
    - 소수면 최대 3자리 (10.5 / 10.125 / 10.333)
    """
    if value is None:
        return "0"

    d = Decimal(str(value)).normalize()
    return format(d, "f")
