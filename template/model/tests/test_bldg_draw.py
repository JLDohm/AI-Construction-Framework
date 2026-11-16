"""Tests of the bldg library: drawings."""

from pathlib import Path

from bldg import draw
from bldg.elements import Building, Footing, FootingKind, Level, Member, MemberRole, Room, RoomUse, Wall
from bldg.geometry import Pt, rect
from bldg.units import ft


def small_building() -> Building:
    b = Building(name="Test shed", address="1 Main St", levels=[Level(id="floor", elevation=12)])
    b.footings = [Footing(id="F1", kind=FootingKind.PIER, at=Pt(0, 0), width=12, thickness=8, depth=36)]
    b.walls = [Wall(id="W1", level="floor", start=Pt(0, 0), end=Pt(ft(12), 0), thickness=4.5, height=ft(8))]
    b.rooms = [
        Room(id="R1", name="Shed", level="floor", outline=rect(0, 0, ft(12), ft(10)), use=RoomUse.STORAGE,
             ceiling_height=ft(8))
    ]  # fmt: skip
    b.members = [
        Member(id="J1", role=MemberRole.JOIST, level="floor", start=Pt(0, 0), end=Pt(0, ft(10)),
               nominal="2x6", species_grade="SPF #2", spacing=16)
    ]  # fmt: skip
    return b


def test_sheets_follow_the_model() -> None:
    assert [s.id for s in draw.sheets(small_building())] == ["S-0", "A-1", "S-1"]
    assert draw.sheets(Building(name="empty")) == []


def test_render_puts_elements_on_their_layers() -> None:
    b = small_building()
    sheet = draw.sheets(b)[1]
    doc = draw.render(b, sheet, "WORKING COPY")
    layers = {e.dxf.layer for e in doc.modelspace()}
    assert {"WALL", "ROOM", "TITLE"} <= layers
    texts = [e.dxf.text for e in doc.modelspace().query("TEXT")]
    assert "120 sq ft, 8'-0\" clg" in texts
    assert "A-1  FLOOR FLOOR PLAN" in texts


def test_write_sheets_writes_dxf_and_pdf(tmp_path: Path) -> None:
    files = draw.write_sheets(small_building(), tmp_path, "WORKING COPY")
    assert sorted(f.name for f in files) == ["A-1.dxf", "A-1.pdf", "S-0.dxf", "S-0.pdf", "S-1.dxf", "S-1.pdf"]
    assert all(f.stat().st_size > 0 for f in files)


def deck() -> Building:
    """A 16 x 12 ft deck: ledger at y = 0, joists to a rim, a doubled beam 11 ft out on three posts."""
    from bldg.elements import Post
    from bldg.geometry import spaced_positions

    b = Building(name="Deck", levels=[Level(id="deck", elevation=30)])

    def m(i: str, role: MemberRole, a: Pt, c: Pt, plies: int = 1, spacing: float = 0) -> Member:
        return Member(
            id=i, role=role, level="deck", start=a, end=c, nominal="2x10", species_grade="SP #2", plies=plies,
            spacing=spacing,
        )  # fmt: skip

    b.members = [m("L1", MemberRole.LEDGER, Pt(0, 0), Pt(ft(16), 0))]
    b.members += [
        m(f"J{i}", MemberRole.JOIST, Pt(x, 0.75), Pt(x, ft(12)), spacing=16)
        for i, x in enumerate(spaced_positions(ft(16), 16), 1)
    ]
    b.members += [m("B1", MemberRole.BEAM, Pt(0, ft(11)), Pt(ft(16), ft(11)), plies=2)]
    xs = (6.0, ft(8), ft(16) - 6)
    b.posts = [
        Post(id=f"P{i}", level="deck", at=Pt(x, ft(11)), nominal="6x6", height=24, species_grade="SP #2")
        for i, x in enumerate(xs, 1)
    ]
    b.footings = [
        Footing(id=f"F{i}", kind=FootingKind.PIER, at=Pt(x, ft(11)), width=16, thickness=8, depth=42)
        for i, x in enumerate(xs, 1)
    ]
    return b


def dims(b: Building, sheet_id: str) -> list[str]:
    sheet = next(s for s in draw.sheets(b) if s.id == sheet_id)
    return sorted(e.dxf.text for e in draw.render(b, sheet, "").modelspace().query("DIMENSION"))


def test_framing_plan_dimensions_spans_and_cantilevers() -> None:
    texts = dims(deck(), "S-1")
    assert "10'-11 1/4\"" in texts  # joist span: ledger face to beam
    assert "1'-0\"" in texts  # joist cantilever past the beam
    assert texts.count("7'-6\"") == 2  # beam spans between posts
    assert texts.count("0'-6\"") == 2  # beam overhangs past the end posts
    assert "16'-0\"" in texts  # ledger


def test_foundation_plan_locates_footings_from_the_house() -> None:
    texts = dims(deck(), "S-0")
    assert texts.count("7'-6\"") == 2  # between footing centers
    assert "11'-0\"" in texts  # ledger (house) to the footings
