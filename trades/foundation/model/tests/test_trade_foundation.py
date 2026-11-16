"""Tests of the foundation pack's check helpers."""

from bldg.checks import Rules
from bldg.elements import Building, Footing, FootingKind, Level, Post
from bldg.geometry import Pt
from bldg.rules import Rule, RuleBook
from bldg_checks import foundation

LOAD_PATH = Rule(id="continuous-load-path", code="TEST", section="R301.1", title="", units="", source="test",
                 verified=True, origin="test", value=1.0)  # fmt: skip
RULES = Rules(RuleBook({LOAD_PATH.id: LOAD_PATH}), foundation.POSTS_ON_FOOTINGS)


def deck(post_at: Pt, footing: Footing) -> Building:
    b = Building(name="t", levels=[Level(id="deck", elevation=30)])
    b.posts = [Post(id="P1", level="deck", at=post_at, nominal="6x6", height=24, species_grade="SP #2")]
    b.footings = [footing]
    return b


def failed(b: Building) -> list[str]:
    return [r.element for r in foundation.posts_on_footings(b, RULES, level="deck") if not r.passed]


def test_post_centered_on_a_pier() -> None:
    pier = Footing(id="F1", kind=FootingKind.PIER, at=Pt(0, 0), width=5.5 * 2**0.5, thickness=8, depth=42)
    assert failed(deck(Pt(0, 0), pier)) == []  # a 6x6's diagonal exactly fits the diameter


def test_post_hanging_off_a_pier() -> None:
    pier = Footing(id="F1", kind=FootingKind.PIER, at=Pt(0, 0), width=12, thickness=8, depth=42)
    assert failed(deck(Pt(3, 0), pier)) == ["post P1"]


def test_post_on_a_pad_edge() -> None:
    pad = Footing(id="F1", kind=FootingKind.PAD, at=Pt(0, 0), width=24, length=24, thickness=8, depth=42)
    assert failed(deck(Pt(12 - 2.75, 0), pad)) == []
    assert failed(deck(Pt(12 - 2.7, 0), pad)) == ["post P1"]
