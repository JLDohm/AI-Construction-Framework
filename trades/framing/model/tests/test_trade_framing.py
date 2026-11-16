"""Tests of the framing pack's check helpers."""

from bldg.checks import Rules
from bldg.elements import Building, Level, Member, MemberRole
from bldg.geometry import Pt
from bldg.rules import Rule, RuleBook
from bldg.units import ft
from bldg_checks import framing

LOAD_PATH = Rule(id="continuous-load-path", code="TEST", section="R301.1", title="", units="", source="test",
                 verified=True, origin="test", value=1.0)  # fmt: skip
RULES = Rules(RuleBook({LOAD_PATH.id: LOAD_PATH}), framing.JOIST_SUPPORT)


def member(i: str, role: MemberRole, a: Pt, c: Pt, plies: int = 1) -> Member:
    return Member(id=i, role=role, level="deck", start=a, end=c, nominal="2x10", species_grade="SP #2", plies=plies)


def deck(*members: Member) -> Building:
    return Building(name="t", levels=[Level(id="deck", elevation=30)], members=list(members))


def failed(b: Building) -> list[str]:
    return [r.element for r in framing.joists_supported(b, RULES, level="deck") if not r.passed]


JOIST = member("J1", MemberRole.JOIST, Pt(12, 0.75), Pt(12, ft(12)))
LEDGER = member("L1", MemberRole.LEDGER, Pt(0, 0), Pt(ft(16), 0))
BEAM = member("B1", MemberRole.BEAM, Pt(0, ft(11)), Pt(ft(16), ft(11)), plies=2)  # 1 ft cantilever past it
RIM = member("R1", MemberRole.RIM, Pt(0, ft(12)), Pt(ft(16), ft(12)))


def test_joist_on_ledger_and_beam() -> None:
    assert failed(deck(JOIST, LEDGER, BEAM, RIM)) == []


def test_rim_does_not_count_as_support() -> None:
    assert failed(deck(JOIST, LEDGER, RIM)) == ["joist J1 supports"]


def test_joist_short_of_its_beam() -> None:
    short = member("J1", MemberRole.JOIST, Pt(12, 0.75), Pt(12, ft(11) - 3))
    assert failed(deck(short, LEDGER, BEAM)) == ["joist J1 supports"]
