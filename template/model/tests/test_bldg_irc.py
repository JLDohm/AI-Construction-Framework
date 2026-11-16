"""Tests of the IRC-family check helpers (bldg_checks/irc.py).

Each helper is tested exactly at its limit (passes) and just past it (fails), with fixed test
values (those of the 2021 IRC), so these tests don't change when the project's own rule values are
verified or amended. One test checks that this project's rules supply every id the helpers use.
"""

from collections.abc import Iterable, Sequence
from dataclasses import replace
from pathlib import Path

import pytest

from bldg.checks import Result, Rules
from bldg.elements import (
    Alarm,
    AlarmKind,
    Building,
    Footing,
    FootingKind,
    Guard,
    Hole,
    HoleKind,
    Level,
    Member,
    MemberRole,
    Opening,
    OpeningKind,
    Room,
    RoomUse,
    Stair,
    Wall,
)
from bldg.geometry import Pt, rect
from bldg.rules import Rule, RuleBook, RuleError, load_rules
from bldg.units import ft
from bldg_checks import irc

MODEL = Path(__file__).resolve().parent.parent

# Fixed test values: those of the 2021 IRC (inches unless noted).
TEST_VALUES = {
    "habitable-area-min": 70.0,  # sq ft
    "habitable-dimension-min": 84.0,
    "ceiling-height-min": 84.0,
    "egress-area-min": 5.7,  # sq ft
    "egress-area-min-grade-floor": 5.0,  # sq ft
    "egress-height-min": 24.0,
    "egress-width-min": 20.0,
    "egress-sill-max": 44.0,
    "grade-floor-sill-max": 44.0,
    "riser-max": 7.75,
    "riser-variation-max": 0.375,
    "tread-min": 10.0,
    "tread-variation-max": 0.375,
    "stair-width-min": 36.0,
    "stair-headroom-min": 80.0,
    "handrail-risers-min": 4.0,
    "handrail-height-min": 34.0,
    "handrail-height-max": 38.0,
    "guard-drop-threshold": 30.0,
    "guard-height-min": 36.0,
    "guard-opening-max": 4.0,
    "footing-depth-min": 12.0,
    "bore-diameter-max-fraction": 1 / 3,
    "bore-edge-distance-min": 2.0,
    "notch-depth-max-fraction": 1 / 6,
    "end-notch-depth-max-fraction": 0.25,
    "notch-length-max-fraction": 1 / 3,
    "smoke-alarm-in-sleeping-room": 1.0,
    "smoke-alarm-outside-sleeping-rooms": 1.0,
    "smoke-alarm-each-story": 1.0,
    "smoke-alarm-from-bath-door-min": 36.0,
    "co-alarm-outside-sleeping-rooms": 1.0,
    "smoke-alarm-interconnected": 1.0,
    "smoke-alarm-hardwired": 1.0,
    "continuous-load-path": 1.0,
}
TABLES = ("deck-joist-span", "floor-joist-span-living")


def make_rule(rule_id: str, value: float | None = None, table: tuple[dict[str, object], ...] = ()) -> Rule:
    return Rule(id=rule_id, code="TEST", section=rule_id, title=rule_id, units="", source="test", verified=True,
                origin="test", value=value, table=table)  # fmt: skip


@pytest.fixture(scope="module")
def book() -> RuleBook:
    rules = {k: make_rule(k, v) for k, v in TEST_VALUES.items()}
    rules |= {k: make_rule(k) for k in TABLES}
    return RuleBook(rules)


def failed(results: Iterable[Result]) -> list[str]:
    return [r.element for r in results if not r.passed]


def view(book: RuleBook, ids: Sequence[str]) -> Rules:
    return Rules(book, ids)


def base(elevation: float = 0) -> Building:
    return Building(name="t", levels=[Level(id="L1", elevation=elevation), Level(id="L2", elevation=elevation + 100)])


def test_this_projects_code_packs_supply_every_helper_id() -> None:
    conf = MODEL.parent / "packs.conf"
    lines = conf.read_text(encoding="utf-8").splitlines() if conf.is_file() else []
    codes: list[str | None] = [
        v for k, _, v in (line.partition("=") for line in lines) if k in ("code", "prefer") and v
    ]
    for code in codes or [None]:
        project = load_rules(MODEL / "rules", codes=[code] if code else None)
        missing = [rule_id for rule_id in irc.ALL if rule_id not in project]
        assert missing == [], f"{code}: the code pack's rule files lack {missing}"
        for rule_id in irc.ALL:
            assert project[rule_id].section, f"{code}: {rule_id} has no section"


def test_fixture_covers_every_helper_id(book: RuleBook) -> None:
    assert sorted(irc.ALL) == sorted(book)


def room(use: RoomUse, w: float, d: float, ceiling: float = ft(8)) -> Room:
    return Room(id="R1", name="r", level="L1", outline=rect(0, 0, w, d), use=use, ceiling_height=ceiling)


def test_room_area_and_dimension(book: RuleBook) -> None:
    r = view(book, irc.ROOM_SIZES)
    b = base()
    b.rooms = [room(RoomUse.SLEEPING, ft(7), ft(10))]  # 70 sq ft, 7 ft wide: both at the limit
    assert failed(irc.room_sizes(b, r)) == []
    b.rooms = [room(RoomUse.SLEEPING, ft(7) - 0.5, ft(10))]
    assert failed(irc.room_sizes(b, r)) == ["room R1 area", "room R1 dimension"]
    b.rooms = [room(RoomUse.KITCHEN, ft(5), ft(14))]  # kitchens are exempt from the dimension
    assert failed(irc.room_sizes(b, r)) == []
    b.rooms = [room(RoomUse.STORAGE, ft(3), ft(3))]
    assert [x.note for x in irc.room_sizes(b, r)] == ["not applicable"]


def test_ceiling_height(book: RuleBook) -> None:
    r = view(book, irc.CEILINGS)
    b = base()
    b.rooms = [room(RoomUse.HALL, ft(4), ft(10), ceiling=ft(7))]
    assert failed(irc.ceilings(b, r)) == []
    b.rooms = [room(RoomUse.HALL, ft(4), ft(10), ceiling=ft(6, 10))]
    assert failed(irc.ceilings(b, r)) == ["room R1 ceiling"]


def egress_building(level_elevation: float, sill: float, clear_w: float, clear_h: float) -> Building:
    b = base(level_elevation)
    b.rooms = [room(RoomUse.SLEEPING, ft(10), ft(10))]
    b.walls = [Wall(id="W1", level="L1", start=Pt(0, 0), end=Pt(ft(10), 0), thickness=4.5, height=ft(8))]
    b.openings = [
        Opening(id="N1", wall="W1", kind=OpeningKind.WINDOW, offset=24, rough_width=40, rough_height=60,
                sill_height=sill, clear_width=clear_w, clear_height=clear_h, egress=True, serves=("R1",))
    ]  # fmt: skip
    return b


def test_egress_upper_floor_needs_5_7_sq_ft(book: RuleBook) -> None:
    r = view(book, irc.EGRESS)
    exact = 5.7 * 144 / 24  # 24 in high: width giving exactly 5.7 sq ft
    assert failed(irc.egress(egress_building(ft(10), 30, exact, 24), r)) == []
    assert failed(irc.egress(egress_building(ft(10), 30, exact - 0.1, 24), r)) == ["opening N1 clear area"]


def test_egress_grade_floor_needs_5_sq_ft(book: RuleBook) -> None:
    r = view(book, irc.EGRESS)
    # level at grade, sill 44 in up: a grade-floor opening, so 5.0 sq ft is enough
    assert failed(irc.egress(egress_building(0, 44, 30, 24), r)) == []
    assert failed(irc.egress(egress_building(0, 44.5, 30, 24), r)) == ["opening N1 clear area", "opening N1 sill"]


def test_egress_size_sill_and_presence(book: RuleBook) -> None:
    r = view(book, irc.EGRESS)
    assert failed(irc.egress(egress_building(0, 30, 19.9, 50), r)) == ["opening N1 clear width"]
    assert failed(irc.egress(egress_building(0, 30, 40, 23.9), r)) == ["opening N1 clear height"]
    assert failed(irc.egress(egress_building(0, 30, 0, 0), r)) == ["opening N1"]
    no_window = egress_building(0, 30, 40, 30)
    no_window.openings = []
    assert failed(irc.egress(no_window, r)) == ["room R1 egress opening"]


def stair(risers: tuple[float, ...], treads: tuple[float, ...], **kw: float) -> Building:
    b = base()
    fields: dict[str, float] = {"width": 36, "headroom": 80, "handrail_height": 34} | kw
    b.stairs = [
        Stair(id="S1", level_from="L1", level_to="L2", start=Pt(0, 0), end=Pt(50, 0), risers=risers, treads=treads,
              **fields)
    ]  # fmt: skip
    return b


def test_risers_at_and_past_the_limits(book: RuleBook) -> None:
    r = view(book, irc.RISERS)
    assert failed(irc.risers(stair((7.75, 7.5, 7.375), (10, 10)), r)) == []  # variation exactly 3/8
    assert failed(irc.risers(stair((7.8, 7.5, 7.5), (10, 10)), r)) == ["stair S1 riser 1"]
    assert failed(irc.risers(stair((7.75, 7.5, 7.36), (10, 10)), r)) == ["stair S1 riser variation"]


def test_treads_at_and_past_the_limits(book: RuleBook) -> None:
    r = view(book, irc.TREADS)
    assert failed(irc.treads(stair((7, 7, 7), (10, 10.375)), r)) == []
    assert failed(irc.treads(stair((7, 7, 7), (9.9, 10)), r)) == ["stair S1 tread 1"]
    assert failed(irc.treads(stair((7, 7, 7), (10, 10.4)), r)) == ["stair S1 tread variation"]


def test_stair_width_and_headroom(book: RuleBook) -> None:
    r = view(book, irc.STAIR_CLEARANCES)
    assert failed(irc.stair_clearances(stair((7, 7), (10,)), r)) == []
    assert failed(irc.stair_clearances(stair((7, 7), (10,), width=35.9, headroom=79.9), r)) == [
        "stair S1 width",
        "stair S1 headroom",
    ]


def test_handrails(book: RuleBook) -> None:
    r = view(book, irc.HANDRAILS)
    four = (7.0,) * 4
    assert failed(irc.handrails(stair(four, (10,) * 3, handrail_height=38), r)) == []
    assert failed(irc.handrails(stair(four, (10,) * 3, handrail_height=38.1), r)) == ["stair S1 handrail height"]
    assert failed(irc.handrails(stair(four, (10,) * 3, handrail_height=0), r)) == ["stair S1 handrail"]
    assert failed(irc.handrails(stair((7.0,) * 3, (10,) * 2, handrail_height=0), r)) == []  # 3 risers: not required


def guard(height: float, drop: float, opening: float) -> Building:
    b = base()
    b.guards = [
        Guard(id="G1", level="L1", start=Pt(0, 0), end=Pt(100, 0), height=height, drop=drop, max_opening=opening)
    ]
    return b


def test_guards(book: RuleBook) -> None:
    r = view(book, irc.GUARDS)
    assert failed(irc.guards(guard(36, 31, 3.9), r)) == []
    assert failed(irc.guards(guard(35.9, 31, 3.9), r)) == ["guard G1 height"]
    assert failed(irc.guards(guard(36, 31, 4.0), r)) == ["guard G1 openings"]  # a 4 in sphere must not pass
    assert failed(irc.guards(guard(20, 30, 10), r)) == []  # 30 in drop: not required


def pier(depth: float) -> Building:
    b = base()
    b.footings = [Footing(id="F1", kind=FootingKind.PIER, at=Pt(0, 0), width=12, thickness=8, depth=depth)]
    return b


def test_footing_depth_and_frost(book: RuleBook) -> None:
    assert failed(irc.footing_depth(pier(12), view(book, irc.FOOTING_DEPTH))) == []
    assert failed(irc.footing_depth(pier(11.9), view(book, irc.FOOTING_DEPTH))) == ["footing F1 depth"]
    # The frost depth is a jurisdiction rule (jurisdiction/jurisdiction.toml); stand one in at 36 in.
    frost = replace(book["footing-depth-min"], id="frost", value=36.0)
    r = Rules(RuleBook(dict(book) | {"frost": frost}), (*irc.FOOTING_DEPTH, "frost"))
    assert failed(irc.footing_depth(pier(36), r, frost_rule="frost")) == []
    assert failed(irc.footing_depth(pier(35.9), r, frost_rule="frost")) == ["footing F1 frost"]


def joist_with(*holes: Hole, span: float = ft(12)) -> Building:
    b = base()
    b.members = [
        Member(id="J1", role=MemberRole.JOIST, level="L1", start=Pt(0, 0), end=Pt(span, 0), nominal="2x10",
               species_grade="SP #2", span=span, spacing=16)
    ]  # fmt: skip
    b.holes = list(holes)
    return b


def test_bored_holes_in_a_2x10(book: RuleBook) -> None:
    r = view(book, irc.HOLES)
    third = 9.25 / 3
    ok = Hole(id="H1", member="J1", kind=HoleKind.BORE, size=third, from_top=2, from_end=40)
    assert failed(irc.holes(joist_with(ok), r)) == []
    big = Hole(id="H1", member="J1", kind=HoleKind.BORE, size=third + 0.05, from_top=2, from_end=40)
    assert failed(irc.holes(joist_with(big), r)) == ["bore H1 in J1 diameter"]
    low = Hole(id="H1", member="J1", kind=HoleKind.BORE, size=3, from_top=4.3, from_end=40)  # 1.95 in left below
    assert failed(irc.holes(joist_with(low), r)) == ["bore H1 in J1 from bottom"]
    high = Hole(id="H1", member="J1", kind=HoleKind.BORE, size=1, from_top=1.9, from_end=40)
    assert failed(irc.holes(joist_with(high), r)) == ["bore H1 in J1 from top"]


def test_notches_in_a_2x10(book: RuleBook) -> None:
    r = view(book, irc.HOLES)
    span = ft(12)
    sixth, quarter = 9.25 / 6, 9.25 / 4
    ok = Hole(id="N1", member="J1", kind=HoleKind.NOTCH, size=sixth, from_top=0, from_end=10, length=3)
    assert failed(irc.holes(joist_with(ok), r)) == []
    deep = Hole(id="N1", member="J1", kind=HoleKind.NOTCH, size=sixth + 0.05, from_top=0, from_end=10, length=3)
    assert failed(irc.holes(joist_with(deep), r)) == ["notch N1 in J1 depth"]
    end = Hole(id="N1", member="J1", kind=HoleKind.NOTCH, size=quarter, from_top=0, from_end=0, length=3)
    assert failed(irc.holes(joist_with(end), r)) == []
    middle = Hole(id="N1", member="J1", kind=HoleKind.NOTCH, size=1, from_top=0, from_end=span / 2, length=2)
    assert failed(irc.holes(joist_with(middle), r)) == ["notch N1 in J1 position"]
    long = Hole(id="N1", member="J1", kind=HoleKind.NOTCH, size=1, from_top=0, from_end=10, length=9.25 / 3 + 0.05)
    assert failed(irc.holes(joist_with(long), r)) == ["notch N1 in J1 length"]


def test_span_tables_start_empty_and_name_the_missing_row(book: RuleBook) -> None:
    r = view(book, irc.DECK_JOIST_SPANS)
    with pytest.raises(RuleError, match="no row for species_grade='SP #2', size='2x10', spacing=16"):
        list(irc.deck_joist_spans(joist_with(), r, level="L1"))


def test_deck_joist_span_against_a_filled_row(book: RuleBook) -> None:
    base_rule = book["deck-joist-span"]
    row = {"species_grade": "SP #2", "size": "2x10", "spacing": 16.0, "span": float(ft(12))}
    filled = replace(base_rule, table=(row,))
    r = Rules(RuleBook({filled.id: filled}), irc.DECK_JOIST_SPANS)
    assert failed(irc.deck_joist_spans(joist_with(span=ft(12)), r, level="L1")) == []
    assert failed(irc.deck_joist_spans(joist_with(span=ft(12) + 0.5), r, level="L1")) == ["joist J1 span"]


def bedroom_wing() -> Building:
    """Two bedrooms and a bath off a hall, on one level; alarms added by each test."""
    b = base()

    def at(i: str, x: float, w: float, use: RoomUse) -> Room:
        return Room(id=i, name=i, level="L1", outline=rect(x, 0, w, ft(10)), use=use, ceiling_height=96)

    b.rooms = [at("BR1", 0, ft(10), RoomUse.SLEEPING), at("BR2", ft(10), ft(10), RoomUse.SLEEPING)]
    b.rooms.append(at("BA", ft(20), ft(6), RoomUse.BATH))
    b.walls = [Wall(id="W1", level="L1", start=Pt(0, ft(10)), end=Pt(ft(30), ft(10)), thickness=4.5, height=96)]
    # The bath door's center is 23 ft along the hall wall.
    b.openings = [Opening(id="D1", wall="W1", kind=OpeningKind.DOOR, offset=ft(23) - 15, rough_width=30,
                          rough_height=82, serves=("BA",))]  # fmt: skip
    return b


def alarm(i: str, at: Pt, room: str = "", covers: tuple[str, ...] = (), kind: AlarmKind = AlarmKind.SMOKE) -> Alarm:
    return Alarm(id=i, kind=kind, level="L1", at=at, room=room, covers=covers)


def test_smoke_alarms_in_and_outside_each_bedroom(book: RuleBook) -> None:
    r = view(book, irc.SMOKE_ALARMS)
    b = bedroom_wing()
    hall = Pt(ft(20), ft(10))  # exactly 3 ft from the bath door's center (23 ft along the hall wall)
    b.alarms = [
        alarm("A1", Pt(60, 60), "BR1"),
        alarm("A2", Pt(180, 60), "BR2"),
        alarm("A3", hall, covers=("BR1", "BR2")),
    ]
    assert failed(irc.smoke_alarms(b, r)) == []
    b.alarms = [alarm("A1", Pt(60, 60), "BR1"), alarm("A3", hall, covers=("BR1", "BR2"))]
    assert failed(irc.smoke_alarms(b, r)) == ["room BR2 smoke alarm inside"]
    b.alarms = [alarm("A1", Pt(60, 60), "BR1"), alarm("A2", Pt(180, 60), "BR2", covers=("BR1",))]
    assert failed(irc.smoke_alarms(b, r)) == [
        "room BR1 smoke alarm outside, nearby",
        "room BR2 smoke alarm outside, nearby",
    ]


def test_smoke_alarm_too_close_to_the_bath_door(book: RuleBook) -> None:
    r = view(book, irc.SMOKE_ALARMS)
    b = bedroom_wing()
    near = Pt(ft(20) + 0.5, ft(10))  # just under 3 ft from the door's center
    b.alarms = [
        alarm("A1", Pt(60, 60), "BR1"),
        alarm("A2", Pt(180, 60), "BR2"),
        alarm("A3", near, covers=("BR1", "BR2")),
    ]
    assert failed(irc.smoke_alarms(b, r)) == ["alarm A3 from bath door D1"]


def test_every_story_with_rooms_needs_a_smoke_alarm(book: RuleBook) -> None:
    r = view(book, irc.SMOKE_ALARMS)
    b = base()
    b.rooms = [
        Room(id="R1", name="den", level="L2", outline=rect(0, 0, 120, 120), use=RoomUse.HABITABLE, ceiling_height=96)
    ]
    assert failed(irc.smoke_alarms(b, r)) == ["level L2 smoke alarm"]


def test_co_alarms_only_where_fuel_or_garage(book: RuleBook) -> None:
    r = view(book, irc.CO_ALARMS)
    b = bedroom_wing()
    assert [x.note for x in irc.co_alarms(b, r)] == ["not applicable"]
    b.fuel_burning_appliances = True
    assert failed(irc.co_alarms(b, r)) == ["room BR1 CO alarm outside, nearby", "room BR2 CO alarm outside, nearby"]
    b.alarms = [alarm("A3", Pt(200, 156), covers=("BR1", "BR2"), kind=AlarmKind.COMBO)]
    assert failed(irc.co_alarms(b, r)) == []


def test_alarm_power(book: RuleBook) -> None:
    r = view(book, irc.ALARM_POWER)
    b = bedroom_wing()
    b.alarms = [Alarm(id="A1", kind=AlarmKind.SMOKE, level="L1", at=Pt(60, 60), room="BR1", hardwired=False)]
    assert failed(irc.alarm_power(b, r)) == ["alarm A1 hardwired"]


def test_joists_laid_out_wider_than_their_spacing(book: RuleBook) -> None:
    base_rule = book["deck-joist-span"]
    row = {"species_grade": "SP #2", "size": "2x10", "spacing": 16.0, "span": float(ft(12))}
    filled = replace(base_rule, table=(row,))
    r = Rules(RuleBook({filled.id: filled}), irc.DECK_JOIST_SPANS)
    b = joist_with()
    b.members = [
        replace(b.members[0], id=f"J{i}", start=Pt(0, y), end=Pt(ft(12), y)) for i, y in enumerate((0, 16, 32.5))
    ]
    assert failed(irc.deck_joist_spans(b, r, level="L1")) == ["joists J1-J2 spacing"]
