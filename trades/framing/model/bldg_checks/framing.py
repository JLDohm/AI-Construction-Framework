"""Check helpers from the framing trade pack. They cite the code pack's rules (via
bldg_checks.irc's rule tuples), so the report cites the section in force.

    from bldg_checks import framing

    @check("T-2.4", rules=framing.JOIST_SUPPORT)
    def joist_support(b: Building, r: Rules) -> Iterator[Result]:
        \"\"\"Every deck joist bears on at least two supports\"\"\"
        yield from framing.joists_supported(b, r, level="deck")
"""

from collections.abc import Iterator

from bldg.checks import Result, Rules
from bldg.elements import Building, MemberRole
from bldg.geometry import Pt, segments_distance
from bldg_checks.irc import LOAD_PATH

JOIST_SUPPORT = LOAD_PATH
SUPPORT_ROLES = (MemberRole.BEAM, MemberRole.LEDGER, MemberRole.HEADER, MemberRole.PLATE)
TOUCH = 0.5  # in: a support counts if the joist comes within half its width plus this


def joists_supported(b: Building, r: Rules, level: str) -> Iterator[Result]:
    """Every joist on `level` crosses or ends on at least two supports: beams, ledgers, headers,
    plates, or bearing walls. Rim joists and blocking don't count. Bearing length, hangers and
    cantilever limits are checked by hand (and the span against the table, by irc)."""
    r.value("continuous-load-path")
    supports: list[tuple[str, Pt, Pt, float]] = [
        (m.id, m.start, m.end, m.thickness / 2) for m in b.members if m.level == level and m.role in SUPPORT_ROLES
    ]
    supports += [(w.id, w.start, w.end, w.thickness / 2) for w in b.walls if w.level == level and w.bearing]
    joists = [m for m in b.members if m.level == level and m.role is MemberRole.JOIST]
    if not joists:
        yield Result(f"joists on level {level}", False, "none", "at least one", "wrong level?")
    for j in joists:
        touching = [sid for sid, a, c, half in supports if segments_distance(j.start, j.end, a, c) <= half + TOUCH]
        yield Result(f"joist {j.id} supports", len(touching) >= 2, ", ".join(touching) or "none", ">= 2")
