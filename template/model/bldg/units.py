"""Units. The model works in inches; these helpers make every other unit explicit."""

from fractions import Fraction

SQ_IN_PER_SQ_FT = 144.0
CU_IN_PER_CU_YD = 46656.0  # 36 in x 36 in x 36 in


def ft(feet: float, inches: float = 0.0) -> float:
    """A length given in feet (and inches), in inches: ft(7, 6) == 90.0."""
    return feet * 12.0 + inches


def to_ft(inches: float) -> float:
    """Inches to decimal feet."""
    return inches / 12.0


def to_sqft(sq_in: float) -> float:
    """Square inches to square feet."""
    return sq_in / SQ_IN_PER_SQ_FT


def to_cuyd(cu_in: float) -> float:
    """Cubic inches to cubic yards (how concrete is ordered)."""
    return cu_in / CU_IN_PER_CU_YD


def fmt_in(inches: float, denom: int = 16) -> str:
    """Inches as a builder writes them, to the nearest 1/denom: 7.75 -> '7 3/4"'."""
    if inches < 0:
        return "-" + fmt_in(-inches, denom)
    frac = Fraction(round(inches * denom), denom)
    whole = frac.numerator // frac.denominator
    rest = frac - whole
    if rest == 0:
        return f'{whole}"'
    if whole == 0:
        return f'{rest.numerator}/{rest.denominator}"'
    return f'{whole} {rest.numerator}/{rest.denominator}"'


def fmt_ft_in(inches: float, denom: int = 16) -> str:
    """Feet and inches, to the nearest 1/denom inch: 147.5 -> "12'-3 1/2\"" ."""
    if inches < 0:
        return "-" + fmt_ft_in(-inches, denom)
    total = Fraction(round(inches * denom), denom)
    feet = int(total // 12)
    return f"{feet}'-{fmt_in(float(total - feet * 12), denom)}"
