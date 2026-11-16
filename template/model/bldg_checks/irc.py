"""Check helpers for the IRC family of codes (the IRC, and state residential codes based on it).
Rule ids are edition-neutral ("riser-max"); the code pack's rule files give each one its value and
its section in that edition, which is what the report cites.

Each helper checks one topic across every element it applies to, and comes with the tuple of rule
ids it reads, for the project's check to declare:

    from bldg_checks import irc

    @check("T-2.1", rules=irc.RISERS)
    def risers(b: Building, r: Rules) -> Iterator[Result]:
        \"\"\"Stair risers\"\"\"
        yield from irc.risers(b, r)

What these helpers do NOT check is listed in the code pack's guide
(.claude/skills/<code>-practice/SKILL.md); the code-reviewer checks those topics by hand.
"""

from collections.abc import Iterator

from bldg.checks import Result, Rules
from bldg.elements import Building, HoleKind, MemberRole, Opening, OpeningKind, RoomUse
from bldg.geometry import Pt, distance
from bldg.units import fmt_ft_in, fmt_in, to_sqft

# Rule ids, grouped as the helpers use them.
ROOM_SIZES = ("habitable-area-min", "habitable-dimension-min")
CEILINGS = ("ceiling-height-min",)
EGRESS = (
    "egress-area-min",
    "egress-area-min-grade-floor",
    "egress-height-min",
    "egress-width-min",
    "egress-sill-max",
    "grade-floor-sill-max",
)
RISERS = ("riser-max", "riser-variation-max")
TREADS = ("tread-min", "tread-variation-max")
STAIR_CLEARANCES = ("stair-width-min", "stair-headroom-min")
HANDRAILS = ("handrail-risers-min", "handrail-height-min", "handrail-height-max")
GUARDS = ("guard-drop-threshold", "guard-height-min", "guard-opening-max")
FOOTING_DEPTH = ("footing-depth-min",)
HOLES = (
    "bore-diameter-max-fraction",
    "bore-edge-distance-min",
    "notch-depth-max-fraction",
    "end-notch-depth-max-fraction",
    "notch-length-max-fraction",
)
DECK_JOIST_SPANS = ("deck-joist-span",)
FLOOR_JOIST_SPANS = ("floor-joist-span-living",)
SMOKE_ALARMS = (
    "smoke-alarm-in-sleeping-room",
    "smoke-alarm-outside-sleeping-rooms",
    "smoke-alarm-each-story",
    "smoke-alarm-from-bath-door-min",
)
CO_ALARMS = ("co-alarm-outside-sleeping-rooms",)
ALARM_POWER = ("smoke-alarm-interconnected", "smoke-alarm-hardwired")
LOAD_PATH = ("continuous-load-path",)
ALL = (
    *ROOM_SIZES, *CEILINGS, *EGRESS, *RISERS, *TREADS, *STAIR_CLEARANCES, *HANDRAILS, *GUARDS,
    *FOOTING_DEPTH, *HOLES, *DECK_JOIST_SPANS, *FLOOR_JOIST_SPANS, *SMOKE_ALARMS, *CO_ALARMS, *ALARM_POWER, *LOAD_PATH,
)  # fmt: skip

HABITABLE = (RoomUse.HABITABLE, RoomUse.KITCHEN, RoomUse.SLEEPING)
NEEDS_CEILING = (*HABITABLE, RoomUse.HALL, RoomUse.BATH, RoomUse.LAUNDRY)
SAWN_MEMBERS = (MemberRole.JOIST, MemberRole.RAFTER, MemberRole.BEAM, MemberRole.BLOCKING, MemberRole.RIM)
EPS = 1e-9  # values exactly at a limit pass


def _none(what: str) -> Result:
    return Result(what, True, "-", "-", "not applicable")


def room_sizes(b: Building, r: Rules) -> Iterator[Result]:
    """Habitable rooms: floor area, and smallest horizontal dimension (kitchens exempt)."""
    area_min = r.value("habitable-area-min")
    dim_min = r.value("habitable-dimension-min")
    rooms = [room for room in b.rooms if room.use in HABITABLE]
    if not rooms:
        yield _none("no habitable rooms")
    for room in rooms:
        area = to_sqft(room.area)
        yield Result(f"room {room.id} area", area >= area_min - EPS, f"{area:.1f} sq ft", f">= {area_min:g} sq ft")
        if room.use is RoomUse.KITCHEN:
            continue
        dim = room.min_dimension
        if dim is None:
            yield Result(f"room {room.id} dimension", False, "not a rectangle", "", "check by hand")
        else:
            yield Result(f"room {room.id} dimension", dim >= dim_min - EPS, fmt_ft_in(dim), f">= {fmt_ft_in(dim_min)}")


def ceilings(b: Building, r: Rules) -> Iterator[Result]:
    """Ceiling height of habitable rooms, halls, baths and laundries (exceptions checked by hand)."""
    low = r.value("ceiling-height-min")
    rooms = [room for room in b.rooms if room.use in NEEDS_CEILING]
    if not rooms:
        yield _none("no rooms that need a minimum ceiling height")
    for room in rooms:
        h = room.ceiling_height
        yield Result(f"room {room.id} ceiling", h >= low - EPS, fmt_ft_in(h), f">= {fmt_ft_in(low)}")


def _level_of_opening(b: Building, o: Opening) -> float:
    wall = next(w for w in b.walls if w.id == o.wall)
    return next(lv.elevation for lv in b.levels if lv.id == wall.level)


def egress(b: Building, r: Rules) -> Iterator[Result]:
    """Every sleeping room has an emergency escape opening, and each one is big enough and low enough."""
    sleeping = [room for room in b.rooms if room.use is RoomUse.SLEEPING]
    if not sleeping:
        yield _none("no sleeping rooms")
    for room in sleeping:
        found = [o for o in b.openings if o.egress and room.id in o.serves]
        yield Result(f"room {room.id} egress opening", bool(found), f"{len(found)} marked egress", ">= 1")
    grade_sill = r.value("grade-floor-sill-max")
    for o in (o for o in b.openings if o.egress):
        if not (o.clear_width and o.clear_height):
            yield Result(f"opening {o.id}", False, "clear opening not known", "", "take it from the data sheet")
            continue
        sill_above_grade = _level_of_opening(b, o) + o.sill_height
        grade_floor = abs(sill_above_grade) <= grade_sill + EPS
        rule = "egress-area-min-grade-floor" if grade_floor else "egress-area-min"
        area_min, area = r.value(rule), to_sqft(o.clear_area)
        where = "grade floor or below grade" if grade_floor else "above grade floor"
        yield Result(
            f"opening {o.id} clear area", area >= area_min - EPS, f"{area:.2f} sq ft", f">= {area_min:g} sq ft", where
        )
        h_min, w_min = r.value("egress-height-min"), r.value("egress-width-min")
        yield Result(
            f"opening {o.id} clear height", o.clear_height >= h_min - EPS, fmt_in(o.clear_height), f">= {fmt_in(h_min)}"
        )
        yield Result(
            f"opening {o.id} clear width", o.clear_width >= w_min - EPS, fmt_in(o.clear_width), f">= {fmt_in(w_min)}"
        )
        sill_max = r.value("egress-sill-max")
        yield Result(
            f"opening {o.id} sill", o.sill_height <= sill_max + EPS, fmt_in(o.sill_height), f"<= {fmt_in(sill_max)}"
        )


def risers(b: Building, r: Rules) -> Iterator[Result]:
    """Every riser's height, and the variation within each flight."""
    top, spread = r.value("riser-max"), r.value("riser-variation-max")
    if not b.stairs:
        yield _none("no stairs")
    for s in b.stairs:
        for i, h in enumerate(s.risers, 1):
            yield Result(f"stair {s.id} riser {i}", h <= top + EPS, fmt_in(h), f"<= {fmt_in(top)}")
        var = max(s.risers) - min(s.risers)
        yield Result(f"stair {s.id} riser variation", var <= spread + EPS, fmt_in(var), f"<= {fmt_in(spread)}")


def treads(b: Building, r: Rules) -> Iterator[Result]:
    """Every tread's depth, and the variation within each flight."""
    low, spread = r.value("tread-min"), r.value("tread-variation-max")
    if not b.stairs:
        yield _none("no stairs")
    for s in b.stairs:
        if not s.treads:
            yield Result(f"stair {s.id} treads", False, "none listed", f">= {fmt_in(low)}")
            continue
        for i, d in enumerate(s.treads, 1):
            yield Result(f"stair {s.id} tread {i}", d >= low - EPS, fmt_in(d), f">= {fmt_in(low)}")
        var = max(s.treads) - min(s.treads)
        yield Result(f"stair {s.id} tread variation", var <= spread + EPS, fmt_in(var), f"<= {fmt_in(spread)}")


def stair_clearances(b: Building, r: Rules) -> Iterator[Result]:
    """Each stair's clear width and headroom."""
    width, head = r.value("stair-width-min"), r.value("stair-headroom-min")
    if not b.stairs:
        yield _none("no stairs")
    for s in b.stairs:
        yield Result(f"stair {s.id} width", s.width >= width - EPS, fmt_in(s.width), f">= {fmt_in(width)}")
        yield Result(f"stair {s.id} headroom", s.headroom >= head - EPS, fmt_ft_in(s.headroom), f">= {fmt_ft_in(head)}")


def handrails(b: Building, r: Rules) -> Iterator[Result]:
    """A handrail at the right height on every flight with enough risers to need one."""
    needs = r.value("handrail-risers-min")
    low, high = r.value("handrail-height-min"), r.value("handrail-height-max")
    if not b.stairs:
        yield _none("no stairs")
    for s in b.stairs:
        if len(s.risers) < needs:
            yield Result(
                f"stair {s.id} handrail", True, f"{len(s.risers)} risers", f"needed from {needs:g}", "not required"
            )
        elif not s.handrail_height:
            yield Result(f"stair {s.id} handrail", False, "none", f"{fmt_in(low)} to {fmt_in(high)}")
        else:
            h = s.handrail_height
            ok = low - EPS <= h <= high + EPS
            yield Result(f"stair {s.id} handrail height", ok, fmt_in(h), f"{fmt_in(low)} to {fmt_in(high)}")


def guards(b: Building, r: Rules) -> Iterator[Result]:
    """Each modeled guard where one is required: height and openings. Whether every open side that
    needs a guard has one is checked by hand (see the guide)."""
    drop_max = r.value("guard-drop-threshold")
    low, sphere = r.value("guard-height-min"), r.value("guard-opening-max")
    if not b.guards:
        yield _none("no guards modeled")
    for g in b.guards:
        if g.drop <= drop_max + EPS:
            yield Result(
                f"guard {g.id}", True, f"drop {fmt_in(g.drop)}", f"required over {fmt_in(drop_max)}", "not required"
            )
            continue
        yield Result(f"guard {g.id} height", g.height >= low - EPS, fmt_in(g.height), f">= {fmt_in(low)}")
        # A sphere of exactly the limit must not pass, so the largest opening must be smaller.
        ok = g.max_opening < sphere - EPS
        yield Result(f"guard {g.id} openings", ok, f"{fmt_in(g.max_opening)} sphere passes", f"< {fmt_in(sphere)}")


def footing_depth(b: Building, r: Rules, frost_rule: str = "") -> Iterator[Result]:
    """Every footing's bottom below grade: the code minimum, and the frost depth when given (the
    jurisdiction's "frost-depth" rule, declared by the project's check)."""
    low = r.value("footing-depth-min")
    frost = r.value(frost_rule) if frost_rule else 0.0
    if not b.footings:
        yield _none("no footings")
    for f in b.footings:
        yield Result(f"footing {f.id} depth", f.depth >= low - EPS, fmt_in(f.depth), f">= {fmt_in(low)}")
        if frost_rule:
            yield Result(
                f"footing {f.id} frost", f.depth >= frost - EPS, fmt_in(f.depth), f">= {fmt_in(frost)} (frost)"
            )


def holes(b: Building, r: Rules) -> Iterator[Result]:
    """Bored holes and notches in sawn-lumber joists, rafters, beams, blocking and rims."""
    if not b.holes:
        yield _none("no holes or notches")
    members = {m.id: m for m in b.members}
    for h in b.holes:
        m = members[h.member]
        name = f"{h.kind} {h.id} in {m.id}"
        if m.role not in SAWN_MEMBERS:
            yield Result(
                name, False, str(m.role), "joist, rafter, beam, blocking or rim", "studs and plates: R602.6, by hand"
            )
            continue
        depth = m.depth
        if h.kind is HoleKind.BORE:
            dmax = r.value("bore-diameter-max-fraction") * depth
            edge = r.value("bore-edge-distance-min")
            yield Result(f"{name} diameter", h.size <= dmax + EPS, fmt_in(h.size), f"<= {fmt_in(dmax)}")
            yield Result(f"{name} from top", h.from_top >= edge - EPS, fmt_in(h.from_top), f">= {fmt_in(edge)}")
            below = depth - h.from_top - h.size
            yield Result(f"{name} from bottom", below >= edge - EPS, fmt_in(below), f">= {fmt_in(edge)}")
            continue
        at_end = h.from_end <= EPS
        frac = "end-notch-depth-max-fraction" if at_end else "notch-depth-max-fraction"
        nmax = r.value(frac) * depth
        yield Result(
            f"{name} depth", h.size <= nmax + EPS, fmt_in(h.size), f"<= {fmt_in(nmax)}", "at end" if at_end else ""
        )
        lmax = r.value("notch-length-max-fraction") * depth
        yield Result(f"{name} length", h.length <= lmax + EPS, fmt_in(h.length), f"<= {fmt_in(lmax)}")
        if not at_end:
            if not m.span:
                yield Result(f"{name} position", False, "member span not set", "outside the middle third")
                continue
            start, end = h.from_end, h.from_end + h.length
            clear = end <= m.span / 3 + EPS or start >= 2 * m.span / 3 - EPS
            where = f"{fmt_in(start)} to {fmt_in(end)} from the end"
            yield Result(f"{name} position", clear, where, "outside the middle third of the span")


def _joist_spans(b: Building, r: Rules, rule_id: str, level: str) -> Iterator[Result]:
    joists = [m for m in b.members if m.role is MemberRole.JOIST and m.level == level]
    if not joists:
        yield Result(f"joists on level {level}", False, "none", "at least one", "wrong level?")
    rule = r[rule_id]
    # The table assumes the stated spacing: adjacent parallel joists must be no farther apart.
    for horizontal in (True, False):
        run = [m for m in joists if (abs(m.end.x - m.start.x) >= abs(m.end.y - m.start.y)) == horizontal]
        run.sort(key=lambda m: m.start.y if horizontal else m.start.x)
        for a, c in zip(run, run[1:], strict=False):
            gap = abs(c.start.y - a.start.y) if horizontal else abs(c.start.x - a.start.x)
            limit = max(a.spacing, c.spacing)
            if limit:
                yield Result(
                    f"joists {a.id}-{c.id} spacing", gap <= limit + EPS, fmt_in(gap), f"<= {fmt_in(limit)} o.c."
                )
    for m in joists:
        if not m.span:
            yield Result(f"joist {m.id} span", False, "span not set", "from the table")
            continue
        allowed = rule.lookup("span", species_grade=m.species_grade, size=m.nominal, spacing=m.spacing)
        yield Result(f"joist {m.id} span", m.span <= allowed + EPS, fmt_ft_in(m.span), f"<= {fmt_ft_in(allowed)}")


def deck_joist_spans(b: Building, r: Rules, level: str) -> Iterator[Result]:
    """Every joist on a deck level against the deck joist span table (cantilevers are checked by hand)."""
    yield from _joist_spans(b, r, "deck-joist-span", level)


def floor_joist_spans(b: Building, r: Rules, level: str) -> Iterator[Result]:
    """Every joist on a floor level against the floor joist span table for living areas (40 psf)."""
    yield from _joist_spans(b, r, "floor-joist-span-living", level)


def _opening_center(b: Building, o: Opening) -> Pt:
    wall = next(w for w in b.walls if w.id == o.wall)
    t = (o.offset + o.rough_width / 2) / wall.length
    return Pt(wall.start.x + (wall.end.x - wall.start.x) * t, wall.start.y + (wall.end.y - wall.start.y) * t)


def smoke_alarms(b: Building, r: Rules) -> Iterator[Result]:
    """Smoke alarms: one in each sleeping room, one outside each sleeping room in its immediate
    vicinity, one on each story with a room (basements included), and none too close to a bathroom
    door. Interconnection and power are checked by hand (see the guide)."""
    in_room = r.value("smoke-alarm-in-sleeping-room")
    outside = r.value("smoke-alarm-outside-sleeping-rooms")
    per_story = r.value("smoke-alarm-each-story")
    bath_gap = r.value("smoke-alarm-from-bath-door-min")
    smoke = [a for a in b.alarms if a.smoke]
    sleeping = [room for room in b.rooms if room.use is RoomUse.SLEEPING]
    for room in sleeping:
        n = sum(1 for a in smoke if a.room == room.id)
        yield Result(f"room {room.id} smoke alarm inside", n >= in_room, f"{n}", f">= {in_room:g}")
        n = sum(1 for a in smoke if room.id in a.covers and a.room not in {s.id for s in sleeping})
        yield Result(f"room {room.id} smoke alarm outside, nearby", n >= outside, f"{n}", f">= {outside:g}")
    stories = sorted({room.level for room in b.rooms if room.use is not RoomUse.OUTDOOR})
    for level in stories:
        n = sum(1 for a in smoke if a.level == level)
        yield Result(f"level {level} smoke alarm", n >= per_story, f"{n}", f">= {per_story:g}")
    baths = {room.id for room in b.rooms if room.use is RoomUse.BATH}
    doors = [o for o in b.openings if o.kind is OpeningKind.DOOR and baths & set(o.serves)]
    for a in smoke:
        for d in doors:
            gap = distance(a.at, _opening_center(b, d))
            yield Result(
                f"alarm {a.id} from bath door {d.id}",
                gap >= bath_gap - EPS,
                fmt_ft_in(gap),
                f">= {fmt_ft_in(bath_gap)}",
            )
    if not sleeping and not stories:
        yield _none("no rooms")


def co_alarms(b: Building, r: Rules) -> Iterator[Result]:
    """Carbon monoxide alarms outside each sleeping room, where the dwelling has a fuel-burning
    appliance or an attached garage. CO alarms inside bedrooms (a fuel-burning appliance in the
    bedroom or its bathroom) are checked by hand."""
    outside = r.value("co-alarm-outside-sleeping-rooms")
    if not (b.fuel_burning_appliances or b.attached_garage):
        yield _none("no fuel-burning appliance and no attached garage")
        return
    sleeping = {room.id for room in b.rooms if room.use is RoomUse.SLEEPING}
    if not sleeping:
        yield _none("no sleeping rooms")
    for room_id in sorted(sleeping):
        n = sum(1 for a in b.alarms if a.co and room_id in a.covers and a.room not in sleeping)
        yield Result(f"room {room_id} CO alarm outside, nearby", n >= outside, f"{n}", f">= {outside:g}")


def alarm_power(b: Building, r: Rules) -> Iterator[Result]:
    """Every smoke alarm interconnected and powered from the building wiring (with battery backup).
    The exceptions for existing buildings are checked by hand: use a different check for them."""
    need_link, need_wired = r.value("smoke-alarm-interconnected"), r.value("smoke-alarm-hardwired")
    smoke = [a for a in b.alarms if a.smoke]
    if not smoke:
        yield _none("no smoke alarms modeled")
    for a in smoke:
        yield Result(
            f"alarm {a.id} interconnected", a.interconnected or not need_link, str(a.interconnected), "required"
        )
        yield Result(f"alarm {a.id} hardwired", a.hardwired or not need_wired, str(a.hardwired), "required")
