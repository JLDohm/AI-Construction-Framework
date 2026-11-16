"""Tests of the bldg library: elements, model problems and the takeoff."""

import math

from bldg.elements import (
    Building,
    Footing,
    FootingKind,
    Hole,
    HoleKind,
    Level,
    Member,
    MemberRole,
    Opening,
    OpeningKind,
    Wall,
)
from bldg.geometry import Pt
from bldg.takeoff import stock_length_ft, takeoff
from bldg.units import ft


def joist(i: str, length: float, plies: int = 1) -> Member:
    return Member(
        id=i, role=MemberRole.JOIST, level="deck", start=Pt(0, 0), end=Pt(length, 0),
        nominal="2x8", species_grade="SP #2", plies=plies, treated=True,
    )  # fmt: skip


def test_lumber_actual_sizes() -> None:
    m = joist("J1", 100, plies=3)
    assert m.depth == 7.25
    assert m.thickness == 4.5


def test_problems_finds_duplicates_and_broken_references() -> None:
    b = Building(name="t", levels=[Level(id="deck", elevation=30)])
    b.members = [joist("J1", 100), joist("J1", 100)]
    b.walls = [Wall(id="W1", level="nope", start=Pt(0, 0), end=Pt(10, 0), thickness=4.5, height=96)]
    b.openings = [
        Opening(id="O1", wall="W9", kind=OpeningKind.DOOR, offset=0, rough_width=38, rough_height=82, serves=("R9",))
    ]
    b.holes = [Hole(id="H1", member="J7", kind=HoleKind.BORE, size=1, from_top=3, from_end=12)]
    problems = "\n".join(b.problems())
    assert "duplicate id 'J1'" in problems
    assert "wall W1: unknown level 'nope'" in problems
    assert "opening O1: unknown wall 'W9'" in problems
    assert "serves unknown room 'R9'" in problems
    assert "hole H1: unknown member 'J7'" in problems


def test_clean_model_has_no_problems() -> None:
    b = Building(name="t", levels=[Level(id="deck", elevation=30)], members=[joist("J1", 100)])
    assert b.problems() == []


def test_stock_lengths_round_up_in_two_foot_steps() -> None:
    assert stock_length_ft(ft(8)) == 8
    assert stock_length_ft(ft(8) + 0.1) == 10
    assert stock_length_ft(ft(20)) == 20
    assert stock_length_ft(ft(20) + 0.1) is None


def test_pier_volume() -> None:
    f = Footing(id="F1", kind=FootingKind.PIER, at=Pt(0, 0), width=12, thickness=10, depth=36)
    assert math.isclose(f.volume, math.pi * 36 * 10)


def test_takeoff_counts_plies_stock_lengths_and_concrete() -> None:
    b = Building(name="t", levels=[Level(id="deck", elevation=30)])
    b.members = [joist("J1", ft(11, 6)), joist("J2", ft(11, 6)), joist("B1", ft(9), plies=2), joist("L1", ft(21))]
    b.footings = [Footing(id="F1", kind=FootingKind.PAD, at=Pt(0, 0), width=36, length=36, thickness=36, depth=40)]
    rows = {(r.item, r.size): r for r in takeoff(b)}
    item = "2x8 SP #2, pressure treated"
    assert rows[(item, "12 ft")].qty == 2
    assert rows[(item, "10 ft")].qty == 2  # one double-ply beam
    assert rows[(item, "21'-0\"")].note == "L1: longer than 20 ft stock"
    assert rows[("Concrete", "footings")].qty == 1.0
