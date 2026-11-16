"""Check helpers from the foundation trade pack. They cite the code pack's rules (via
bldg_checks.irc's rule tuples), so the report cites the section in force.

    from bldg_checks import foundation

    @check("T-2.3", rules=foundation.POSTS_ON_FOOTINGS)
    def posts(b: Building, r: Rules) -> Iterator[Result]:
        \"\"\"Every deck post bears on a footing\"\"\"
        yield from foundation.posts_on_footings(b, r, level="deck")
"""

import math
from collections.abc import Iterator

from bldg.checks import Result, Rules
from bldg.elements import Building, Footing, FootingKind, Post, lumber_size
from bldg.geometry import distance
from bldg.units import fmt_in
from bldg_checks.irc import LOAD_PATH

POSTS_ON_FOOTINGS = LOAD_PATH
EPS = 1e-9


def _post_inside(p: Post, f: Footing) -> bool:
    """True if the post's whole footprint lies on the footing."""
    t, w = lumber_size(p.nominal)
    if f.kind is FootingKind.PIER:
        return distance(p.at, f.at) + math.hypot(t, w) / 2 <= f.width / 2 + EPS
    half_x, half_y = f.width / 2, (f.length or f.width) / 2
    return abs(p.at.x - f.at.x) + t / 2 <= half_x + EPS and abs(p.at.y - f.at.y) + w / 2 <= half_y + EPS


def posts_on_footings(b: Building, r: Rules, level: str | None = None) -> Iterator[Result]:
    """Every post (on `level`, if given: the posts that should stand on footings) bears wholly on a
    footing: part of a continuous load path to the soil. Footing size for the load is by hand."""
    r.value("continuous-load-path")  # the rule this check enforces must be filled in
    posts = [p for p in b.posts if level is None or p.level == level]
    if not posts:
        yield Result(f"posts{f' on level {level}' if level else ''}", True, "-", "-", "not applicable: no posts")
    for p in posts:
        under = [f for f in b.footings if _post_inside(p, f)]
        if under:
            yield Result(f"post {p.id}", True, f"on footing {under[0].id}", "wholly on a footing")
        else:
            nearest = min(b.footings, key=lambda f: distance(p.at, f.at), default=None)
            seen = (
                f"nearest footing {nearest.id}, {fmt_in(distance(p.at, nearest.at))} away" if nearest else "no footings"
            )
            yield Result(f"post {p.id}", False, seen, "wholly on a footing")
