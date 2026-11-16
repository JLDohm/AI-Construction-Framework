"""Plan geometry: points and polygons, in inches. x runs east, y runs north."""

import math
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class Pt:
    """A point in plan, in inches."""

    x: float
    y: float

    def __add__(self, other: "Pt") -> "Pt":
        return Pt(self.x + other.x, self.y + other.y)


def distance(a: Pt, b: Pt) -> float:
    return math.hypot(b.x - a.x, b.y - a.y)


def rect(x: float, y: float, width: float, depth: float) -> tuple[Pt, ...]:
    """An axis-aligned rectangle from its south-west corner, counter-clockwise."""
    if width <= 0 or depth <= 0:
        raise ValueError(f"rectangle needs a positive size, got {width} x {depth}")
    return (Pt(x, y), Pt(x + width, y), Pt(x + width, y + depth), Pt(x, y + depth))


def polygon_area(points: Sequence[Pt]) -> float:
    """Area of a simple polygon (shoelace formula), in square inches."""
    if len(points) < 3:
        raise ValueError("a polygon needs at least 3 points")
    twice = 0.0
    for a, b in zip(points, [*points[1:], points[0]], strict=True):
        twice += a.x * b.y - b.x * a.y
    return abs(twice) / 2.0


def bbox(points: Sequence[Pt]) -> tuple[Pt, Pt]:
    """The bounding box: (south-west corner, north-east corner)."""
    xs = [p.x for p in points]
    ys = [p.y for p in points]
    return Pt(min(xs), min(ys)), Pt(max(xs), max(ys))


def is_axis_rect(points: Sequence[Pt]) -> bool:
    """True if the polygon is an axis-aligned rectangle."""
    if len(points) != 4:
        return False
    lo, hi = bbox(points)
    return {(p.x, p.y) for p in points} == {(lo.x, lo.y), (hi.x, lo.y), (hi.x, hi.y), (lo.x, hi.y)}


def spaced_positions(length: float, spacing: float) -> list[float]:
    """Positions along a run for members at `spacing` on center, including both ends.

    The last space is shorter when the length isn't a multiple of the spacing:
    spaced_positions(40, 16) == [0, 16, 32, 40].
    """
    if length <= 0 or spacing <= 0:
        raise ValueError(f"need a positive length and spacing, got {length} and {spacing}")
    positions = [i * spacing for i in range(int(length // spacing) + 1)]
    if length - positions[-1] > 1e-9:
        positions.append(length)
    return positions


def point_segment_distance(p: Pt, a: Pt, b: Pt) -> float:
    """Shortest distance from point p to the segment a-b."""
    dx, dy = b.x - a.x, b.y - a.y
    length2 = dx * dx + dy * dy
    if length2 == 0:
        return distance(p, a)
    t = max(0.0, min(1.0, ((p.x - a.x) * dx + (p.y - a.y) * dy) / length2))
    return distance(p, Pt(a.x + t * dx, a.y + t * dy))


def segments_distance(a: Pt, b: Pt, c: Pt, d: Pt) -> float:
    """Shortest distance between segments a-b and c-d (0 if they cross)."""

    def orient(p: Pt, q: Pt, r: Pt) -> float:
        return (q.x - p.x) * (r.y - p.y) - (q.y - p.y) * (r.x - p.x)

    d1, d2, d3, d4 = orient(c, d, a), orient(c, d, b), orient(a, b, c), orient(a, b, d)
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)) and 0 not in (d1, d2, d3, d4):
        return 0.0
    return min(
        point_segment_distance(a, c, d),
        point_segment_distance(b, c, d),
        point_segment_distance(c, a, b),
        point_segment_distance(d, a, b),
    )


def line_crossing(a: Pt, b: Pt, c: Pt, d: Pt) -> float | None:
    """Where the line through c-d crosses the line through a-b, as a distance from a along a-b;
    None if the lines are parallel."""
    rx, ry, sx, sy = b.x - a.x, b.y - a.y, d.x - c.x, d.y - c.y
    cross = rx * sy - ry * sx
    if abs(cross) < 1e-12:
        return None
    t = ((c.x - a.x) * sy - (c.y - a.y) * sx) / cross
    return t * math.hypot(rx, ry)
