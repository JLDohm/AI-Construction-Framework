"""Building elements. All lengths are inches; plan positions are `Pt`s; heights are measured
up from the element's level unless a field says otherwise.

Trade packs may add elements in their own modules; the project's `Building` holds them all.
"""

import math
import re
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from enum import StrEnum

from bldg.geometry import Pt, bbox, distance, is_axis_rect, polygon_area

# Dressed (actual) sizes of dry softwood lumber, thickness x width, in inches.
# Source: American Softwood Lumber Standard, NIST PS 20, dry dressed sizes.
LUMBER_SIZES: dict[str, tuple[float, float]] = {
    "2x4": (1.5, 3.5),
    "2x6": (1.5, 5.5),
    "2x8": (1.5, 7.25),
    "2x10": (1.5, 9.25),
    "2x12": (1.5, 11.25),
    "4x4": (3.5, 3.5),
    "4x6": (3.5, 5.5),
    "6x6": (5.5, 5.5),
}


def lumber_size(nominal: str) -> tuple[float, float]:
    """Actual (thickness, width) of a nominal lumber size such as "2x10"."""
    try:
        return LUMBER_SIZES[nominal]
    except KeyError:
        known = ", ".join(LUMBER_SIZES)
        raise ValueError(f"unknown lumber size {nominal!r} (known: {known})") from None


class RoomUse(StrEnum):
    SLEEPING = "sleeping"
    HABITABLE = "habitable"  # living, dining, family room, office
    KITCHEN = "kitchen"  # habitable, but some size rules exempt it
    BATH = "bath"  # bathrooms and toilet rooms
    LAUNDRY = "laundry"
    HALL = "hall"
    STORAGE = "storage"
    GARAGE = "garage"
    OUTDOOR = "outdoor"  # decks, porches
    OTHER = "other"


class OpeningKind(StrEnum):
    WINDOW = "window"
    DOOR = "door"


class MemberRole(StrEnum):
    JOIST = "joist"
    RAFTER = "rafter"
    BEAM = "beam"
    HEADER = "header"
    LEDGER = "ledger"
    RIM = "rim"
    BLOCKING = "blocking"
    STUD = "stud"
    PLATE = "plate"


class FootingKind(StrEnum):
    PIER = "pier"  # round, width is the diameter
    PAD = "pad"  # square or rectangular spread footing
    STRIP = "strip"  # continuous, under a wall


class HoleKind(StrEnum):
    BORE = "bore"  # a round hole through the member's width
    NOTCH = "notch"  # a cut in from the top or bottom edge


class AlarmKind(StrEnum):
    SMOKE = "smoke"
    CO = "co"  # carbon monoxide
    COMBO = "smoke+co"  # one listed device that does both


@dataclass(frozen=True, kw_only=True)
class Level:
    """A floor or walking surface. `elevation` is the top of the surface above the datum
    (finished grade at the building = 0)."""

    id: str
    elevation: float


@dataclass(frozen=True, kw_only=True)
class Room:
    id: str
    name: str
    level: str
    outline: tuple[Pt, ...]
    use: RoomUse
    ceiling_height: float  # finished floor to finished ceiling; 0 for outdoor spaces

    @property
    def area(self) -> float:
        """Floor area in square inches (use units.to_sqft for square feet)."""
        return polygon_area(self.outline)

    @property
    def min_dimension(self) -> float | None:
        """Smallest horizontal dimension, for axis-aligned rectangular rooms; else None."""
        if not is_axis_rect(self.outline):
            return None
        lo, hi = bbox(self.outline)
        return min(hi.x - lo.x, hi.y - lo.y)


@dataclass(frozen=True, kw_only=True)
class Wall:
    """A wall along its centerline."""

    id: str
    level: str
    start: Pt
    end: Pt
    thickness: float  # finished, e.g. 4.5 for 2x4 studs with 1/2 in drywall both sides
    height: float
    exterior: bool = False
    bearing: bool = False

    @property
    def length(self) -> float:
        return distance(self.start, self.end)


@dataclass(frozen=True, kw_only=True)
class Opening:
    """A window or door in a wall. `offset` is from the wall's start to the near edge of the
    rough opening. Clear sizes are the net clear opening when fully open (from the product's
    data sheet), which is what egress rules measure."""

    id: str
    wall: str
    kind: OpeningKind
    offset: float
    rough_width: float
    rough_height: float
    sill_height: float = 0.0  # floor to the bottom of the clear opening; 0 for doors
    clear_width: float = 0.0  # 0 = not known yet
    clear_height: float = 0.0
    egress: bool = False  # intended as an emergency escape and rescue opening
    serves: tuple[str, ...] = ()  # room ids
    product: str = ""  # make and model, once chosen

    @property
    def clear_area(self) -> float:
        """Net clear opening area in square inches."""
        return self.clear_width * self.clear_height


@dataclass(frozen=True, kw_only=True)
class Stair:
    """One flight of stairs. Risers and treads are listed one by one, bottom to top, so a
    check sees every one of them (the code limits the variation, not only the maximum)."""

    id: str
    level_from: str
    level_to: str
    start: Pt  # plan position of the bottom nosing, at the stair's center line
    end: Pt  # plan position of the top nosing
    width: float  # clear width between finished surfaces
    risers: tuple[float, ...]
    treads: tuple[float, ...]  # one fewer than risers, normally
    headroom: float
    handrail_height: float = 0.0  # 0 = no handrail
    nosing: float = 0.0

    @property
    def total_rise(self) -> float:
        return sum(self.risers)


@dataclass(frozen=True, kw_only=True)
class Guard:
    """A guard (railing) along an open side of a walking surface."""

    id: str
    level: str
    start: Pt
    end: Pt
    height: float  # from the walking surface to the top of the guard
    drop: float  # walking surface above the floor or grade below
    max_opening: float  # largest sphere that can pass through, in inches


@dataclass(frozen=True, kw_only=True)
class Member:
    """A framing member, drawn in plan from `start` to `end`. `span` is the clear span
    between supports, which span tables use; it can differ from the length."""

    id: str
    role: MemberRole
    level: str
    start: Pt
    end: Pt
    nominal: str  # e.g. "2x10"
    species_grade: str  # e.g. "Southern pine #2"
    span: float = 0.0
    spacing: float = 0.0  # on center, for repetitive members; 0 for single members
    plies: int = 1  # e.g. 3 for a triple 2x10 beam
    treated: bool = False

    @property
    def length(self) -> float:
        return distance(self.start, self.end)

    @property
    def depth(self) -> float:
        return lumber_size(self.nominal)[1]

    @property
    def thickness(self) -> float:
        return lumber_size(self.nominal)[0] * self.plies


@dataclass(frozen=True, kw_only=True)
class Post:
    id: str
    level: str
    at: Pt
    nominal: str  # e.g. "6x6"
    height: float
    species_grade: str
    treated: bool = False


@dataclass(frozen=True, kw_only=True)
class Footing:
    id: str
    kind: FootingKind
    at: Pt  # center
    width: float  # diameter for a pier
    length: float = 0.0  # pads and strips; 0 for piers
    thickness: float = 0.0
    depth: float = 0.0  # bottom of the footing below finished grade

    @property
    def volume(self) -> float:
        """Concrete volume in cubic inches."""
        if self.kind is FootingKind.PIER:
            return math.pi * (self.width / 2) ** 2 * self.thickness
        return self.width * self.length * self.thickness


@dataclass(frozen=True, kw_only=True)
class Hole:
    """A bored hole or notch in a framing member, for a pipe, duct or wire."""

    id: str
    member: str
    kind: HoleKind
    size: float  # diameter of a bore; depth of a notch
    from_top: float  # bore: top edge of the member to the top of the hole; notch: 0 = top
    from_end: float  # nearest end of the member to the near edge of the hole or notch
    length: float = 0.0  # notches only: length along the member
    purpose: str = ""


@dataclass(frozen=True, kw_only=True)
class Alarm:
    """A smoke and/or carbon monoxide alarm. `room` is the room it's in ("" for a space that isn't
    modeled as a room, such as a hall); `covers` lists the sleeping rooms whose immediate vicinity
    it serves, for an alarm outside the bedrooms."""

    id: str
    kind: AlarmKind
    level: str
    at: Pt
    room: str = ""
    covers: tuple[str, ...] = ()
    hardwired: bool = True
    interconnected: bool = True
    product: str = ""

    @property
    def smoke(self) -> bool:
        return self.kind in (AlarmKind.SMOKE, AlarmKind.COMBO)

    @property
    def co(self) -> bool:
        return self.kind in (AlarmKind.CO, AlarmKind.COMBO)


@dataclass(frozen=True, kw_only=True)
class TakeoffItem:
    """A material the drawings don't count by themselves: fasteners, connectors, flashing."""

    item: str
    size: str
    qty: float
    unit: str
    source: str  # where the quantity comes from (product data sheet, rule of thumb + reason)


@dataclass(frozen=True)
class Provisional:
    """A stated assumption standing in for a site measurement not taken yet (docs/existing.md,
    Provisional assumptions). Every result is provisional while one is left, and a release refuses."""

    id: str  # P-1, P-2, ...
    what: str  # the value assumed, e.g. "rim joist 2x10 solid-sawn SPF, sound"
    until: str  # what replaces it, e.g. "E-4 inspection opening"


@dataclass(kw_only=True)
class Building:
    name: str
    address: str = ""
    levels: list[Level] = field(default_factory=list)
    rooms: list[Room] = field(default_factory=list)
    walls: list[Wall] = field(default_factory=list)
    openings: list[Opening] = field(default_factory=list)
    stairs: list[Stair] = field(default_factory=list)
    guards: list[Guard] = field(default_factory=list)
    members: list[Member] = field(default_factory=list)
    posts: list[Post] = field(default_factory=list)
    footings: list[Footing] = field(default_factory=list)
    holes: list[Hole] = field(default_factory=list)
    alarms: list[Alarm] = field(default_factory=list)
    extras: list[TakeoffItem] = field(default_factory=list)
    provisional: list[Provisional] = field(default_factory=list)
    # Facts the code's requirements depend on (e.g. CO alarms, R315):
    fuel_burning_appliances: bool = False  # furnace, water heater, fireplace, range... burning fuel
    attached_garage: bool = False

    def element(self, element_id: str) -> object:
        """Any element by its id."""
        for e in self._all():
            if getattr(e, "id", None) == element_id:
                return e
        raise KeyError(f"no element with id {element_id!r}")

    def _all(self) -> Iterable[object]:
        groups: Sequence[Sequence[object]] = (
            self.levels,
            self.rooms,
            self.walls,
            self.openings,
            self.stairs,
            self.guards,
            self.members,
            self.posts,
            self.footings,
            self.holes,
            self.alarms,
        )
        for group in groups:
            yield from group

    def problems(self) -> list[str]:
        """Model errors that make checks meaningless: duplicate ids, broken references, bad sizes."""
        out: list[str] = []
        ids = Counter(getattr(e, "id", "") for e in self._all())
        out += [f"duplicate id {i!r} ({n} elements)" for i, n in sorted(ids.items()) if n > 1]
        levels = {lv.id for lv in self.levels}
        walls = {w.id for w in self.walls}
        rooms = {r.id for r in self.rooms}
        members = {m.id: m for m in self.members}

        def need_level(owner: str, level: str) -> None:
            if level not in levels:
                out.append(f"{owner}: unknown level {level!r}")

        for r in self.rooms:
            need_level(f"room {r.id}", r.level)
            if len(r.outline) < 3:
                out.append(f"room {r.id}: outline needs at least 3 points")
        for w in self.walls:
            need_level(f"wall {w.id}", w.level)
            if w.length <= 0:
                out.append(f"wall {w.id}: zero length")
        for o in self.openings:
            if o.wall not in walls:
                out.append(f"opening {o.id}: unknown wall {o.wall!r}")
            out += [f"opening {o.id}: serves unknown room {r!r}" for r in o.serves if r not in rooms]
        for s in self.stairs:
            need_level(f"stair {s.id}", s.level_from)
            need_level(f"stair {s.id}", s.level_to)
            if not s.risers:
                out.append(f"stair {s.id}: no risers")
        for g in self.guards:
            need_level(f"guard {g.id}", g.level)
        for m in self.members:
            need_level(f"member {m.id}", m.level)
            if m.nominal not in LUMBER_SIZES:
                out.append(f"member {m.id}: unknown lumber size {m.nominal!r}")
            if m.plies < 1:
                out.append(f"member {m.id}: plies must be at least 1")
        for p in self.posts:
            need_level(f"post {p.id}", p.level)
            if p.nominal not in LUMBER_SIZES:
                out.append(f"post {p.id}: unknown lumber size {p.nominal!r}")
        for h in self.holes:
            if h.member not in members:
                out.append(f"hole {h.id}: unknown member {h.member!r}")
        for a in self.alarms:
            need_level(f"alarm {a.id}", a.level)
            if a.room and a.room not in rooms:
                out.append(f"alarm {a.id}: unknown room {a.room!r}")
            out += [f"alarm {a.id}: covers unknown room {r!r}" for r in a.covers if r not in rooms]
        seen: set[str] = set()
        for pa in self.provisional:
            if not re.fullmatch(r"P-\d+", pa.id):
                out.append(f"provisional {pa.id!r}: id must look like P-1")
            elif pa.id in seen:
                out.append(f"provisional {pa.id}: duplicate id")
            seen.add(pa.id)
            if not pa.what.strip() or not pa.until.strip():
                out.append(f"provisional {pa.id}: say what is assumed and what replaces it")
        return out
