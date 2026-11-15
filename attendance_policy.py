"""BunkWise - the crisp 75% attendance policy, projected from classes attended and held.

Pure Python, no fuzzy logic and no Streamlit. Nothing here feeds bunk_meter.infer(): the fuzzy score
never changes because of these numbers. Exact integer/Fraction arithmetic is used so the 75% boundary
is exact (for example 3 of 4 classes is exactly 75%, never 74.999...).
"""
import math
from dataclasses import dataclass
from fractions import Fraction

import bunk_meter as bm

MINIMUM = Fraction(bm.ATTENDANCE_MIN, 100)  # 3/4


def _check(attended, held):
    for name, v in (("attended", attended), ("held", held)):
        if isinstance(v, bool) or not isinstance(v, int):
            raise ValueError(f"{name} must be a whole number, got {v!r}")
    if attended < 0 or held < 0:
        raise ValueError("attended and held cannot be negative")
    if attended > held:
        raise ValueError(f"attended ({attended}) cannot be more than held ({held})")


def percent(attended, held):
    """Attendance in percent, or None when no class has been held yet."""
    _check(attended, held)
    return None if held == 0 else float(Fraction(100 * attended, held))


def meets_minimum(attended, held):
    """True when attended/held >= 75% exactly. With no classes held there is nothing to fall short of."""
    _check(attended, held)
    return Fraction(attended, held) >= MINIMUM if held else True


def max_safe_skips(attended, held):
    """Most consecutive classes you could miss and still be at or above 75% (0 if already below)."""
    _check(attended, held)
    if held == 0:
        return 0
    # attended / (held + s) >= m   <=>   s <= attended / m - held
    return max(0, math.floor(attended / MINIMUM - held))


def classes_to_recover(attended, held):
    """Fewest consecutive classes you must attend (and not miss any) to reach 75% (0 if already there)."""
    _check(attended, held)
    if held == 0 or meets_minimum(attended, held):
        return 0
    # (attended + r) / (held + r) >= m   <=>   r >= (m*held - attended) / (1 - m)
    return math.ceil((MINIMUM * held - attended) / (1 - MINIMUM))


@dataclass(frozen=True)
class PolicyProjection:
    attended: int
    held: int
    percent_now: float | None
    percent_if_skip: float | None   # after missing the next class
    percent_if_attend: float | None  # after attending the next class
    meets_now: bool
    meets_if_skip: bool
    safe_skips: int
    to_recover: int


def project(attended, held):
    """Consequences of the next class under the 75% rule, from the real counts."""
    _check(attended, held)
    return PolicyProjection(
        attended, held, percent(attended, held),
        percent(attended, held + 1), percent(attended + 1, held + 1),
        meets_minimum(attended, held), meets_minimum(attended, held + 1),
        max_safe_skips(attended, held), classes_to_recover(attended, held))
