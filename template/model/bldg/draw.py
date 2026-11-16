"""Drawings: one DXF (for CAD) and one PDF (to look at and print) per sheet, made from the model.

Sheets are made only for what the model contains:
- S-0 foundation plan: footings and posts on them;
- A-n floor plan for each level with walls, rooms, stairs or guards;
- S-n framing plan for each level with framing members or posts.

Drawing units are inches (1 drawing unit = 1 in). The PDF is fitted to the page, not to scale:
the dimensions and notes on it are what count.
"""

import math
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from ezdxf import bbox as dxf_bbox
from ezdxf import units as dxf_units
from ezdxf.addons.drawing import matplotlib as dxf_matplotlib
from ezdxf.document import Drawing
from ezdxf.enums import TextEntityAlignment
from ezdxf.filemanagement import new as new_dxf
from ezdxf.layouts.layout import Modelspace

from bldg.elements import Building, FootingKind, Level, Member, MemberRole, lumber_size
from bldg.geometry import Pt, bbox, distance, line_crossing, segments_distance
from bldg.units import fmt_ft_in, fmt_in, to_sqft

TEXT = 6.0  # text height, inches at full size
LAYERS = {  # name: ACI color
    "WALL": 7,
    "OPENING": 4,
    "ROOM": 3,
    "STAIR": 6,
    "GUARD": 1,
    "MEMBER": 5,
    "POST": 2,
    "FOOTING": 8,
    "ALARM": 1,
    "DIM": 3,
    "TITLE": 7,
}


# Dimension style: sizes in inches at full size; the text is written by fmt_ft_in, not by ezdxf.
DIM_STYLE = {"dimtxt": TEXT * 0.8, "dimasz": TEXT * 0.6, "dimexe": 2.0, "dimexo": 2.0, "dimlfac": 1, "dimtad": 1}
DIM_GAP = TEXT * 4  # how far a dimension line sits from what it measures
SUPPORTS = (MemberRole.BEAM, MemberRole.LEDGER, MemberRole.HEADER, MemberRole.PLATE)


@dataclass(frozen=True)
class Sheet:
    id: str
    title: str
    draw: Callable[[Modelspace], None]


def _label(msp: Modelspace, text: str, at: Pt, layer: str, height: float = TEXT) -> None:
    for i, line in enumerate(text.splitlines()):
        msp.add_text(line, height=height, dxfattribs={"layer": layer}).set_placement(
            (at.x, at.y - i * height * 1.5), align=TextEntityAlignment.MIDDLE_CENTER
        )


def _dim(msp: Modelspace, a: Pt, b: Pt, side: float) -> None:
    """Dimension a-b, with the dimension line `side` inches to the left of a->b (negative: right).
    The points are ordered so the text reads upright."""
    if b.x < a.x - 1e-9 or (abs(b.x - a.x) <= 1e-9 and b.y < a.y):
        a, b, side = b, a, -side
    length = distance(a, b)
    if length < 0.25:
        return
    dim = msp.add_aligned_dim(
        p1=(a.x, a.y), p2=(b.x, b.y), distance=side, dimstyle="EZDXF", text=fmt_ft_in(length),
        override=DIM_STYLE, dxfattribs={"layer": "DIM"},
    )  # fmt: skip
    dim.render()


def _away(a: Pt, b: Pt, center: Pt, gap: float) -> float:
    """A `side` for _dim that puts the dimension line on the side of a-b away from `center`."""
    left = (center.x - a.x) * -(b.y - a.y) + (center.y - a.y) * (b.x - a.x)
    return -gap if left > 0 else gap


def _chain(msp: Modelspace, points: list[Pt], side: float) -> None:
    """Dimension each gap between consecutive points (already in order along a line)."""
    for a, b in zip(points, points[1:], strict=False):
        _dim(msp, a, b, side)


def _distinct(values: list[float]) -> list[float]:
    out: list[float] = []
    for v in sorted(values):
        if not out or v - out[-1] > 0.25:
            out.append(v)
    return out


def _mid(a: Pt, b: Pt) -> Pt:
    return Pt((a.x + b.x) / 2, (a.y + b.y) / 2)


def _band(a: Pt, b: Pt, width: float) -> list[tuple[float, float]]:
    """The four corners of a strip of `width` centered on the line a-b."""
    length = math.hypot(b.x - a.x, b.y - a.y)
    nx, ny = -(b.y - a.y) / length * width / 2, (b.x - a.x) / length * width / 2
    return [(a.x + nx, a.y + ny), (b.x + nx, b.y + ny), (b.x - nx, b.y - ny), (a.x - nx, a.y - ny)]


def _beside(a: Pt, b: Pt, at: Pt, dist: float) -> Pt:
    """A point `dist` to the right of the line a-b (outside, for walls drawn counter-clockwise), level with `at`."""
    length = math.hypot(b.x - a.x, b.y - a.y)
    return Pt(at.x + (b.y - a.y) / length * dist, at.y - (b.x - a.x) / length * dist)


def _along(a: Pt, b: Pt, dist: float) -> Pt:
    length = math.hypot(b.x - a.x, b.y - a.y)
    return Pt(a.x + (b.x - a.x) * dist / length, a.y + (b.y - a.y) * dist / length)


def _floor_plan(b: Building, level: Level) -> Callable[[Modelspace], None]:
    def draw(msp: Modelspace) -> None:
        walls = {w.id: w for w in b.walls if w.level == level.id}
        for w in walls.values():
            msp.add_lwpolyline(_band(w.start, w.end, w.thickness), close=True, dxfattribs={"layer": "WALL"})
        for o in b.openings:
            host = walls.get(o.wall)
            if host is None:
                continue
            for d in (o.offset, o.offset + o.rough_width):
                jamb = _along(host.start, host.end, d)
                corners = _band(jamb, _along(host.start, host.end, d + 0.01), host.thickness)
                msp.add_line(corners[0], corners[3], dxfattribs={"layer": "OPENING"})
            centre = _along(host.start, host.end, o.offset + o.rough_width / 2)
            size = f"{fmt_in(o.rough_width)} x {fmt_in(o.rough_height)}"
            at = _beside(host.start, host.end, centre, host.thickness + 3 * TEXT)
            _label(msp, f"{o.id}\n{size}", at, "OPENING", TEXT * 0.8)
        for r in b.rooms:
            if r.level != level.id:
                continue
            lo, hi = bbox(r.outline)
            ceiling = f", {fmt_ft_in(r.ceiling_height)} clg" if r.ceiling_height else ""
            _label(msp, f"{r.name.upper()}\n{to_sqft(r.area):.0f} sq ft{ceiling}", _mid(lo, hi), "ROOM")
        for s in b.stairs:
            if s.level_from != level.id:
                continue
            msp.add_lwpolyline(_band(s.start, s.end, s.width), close=True, dxfattribs={"layer": "STAIR"})
            msp.add_line((s.start.x, s.start.y), (s.end.x, s.end.y), dxfattribs={"layer": "STAIR"})
            text = f"{s.id} UP\n{len(s.risers)} R @ {fmt_in(max(s.risers))} max"
            _label(msp, text, _mid(s.start, s.end), "STAIR", TEXT * 0.8)
        for g in b.guards:
            if g.level != level.id:
                continue
            msp.add_line((g.start.x, g.start.y), (g.end.x, g.end.y), dxfattribs={"layer": "GUARD"})
            _label(msp, f"{g.id} GUARD {fmt_in(g.height)}", _mid(g.start, g.end), "GUARD", TEXT * 0.8)
        if walls:
            lo, hi = bbox([p for w in walls.values() for p in (w.start, w.end)])
            _dim(msp, Pt(lo.x, lo.y), Pt(hi.x, lo.y), -DIM_GAP)
            _dim(msp, Pt(lo.x, lo.y), Pt(lo.x, hi.y), DIM_GAP)
        for a in b.alarms:
            if a.level != level.id:
                continue
            msp.add_circle((a.at.x, a.at.y), TEXT, dxfattribs={"layer": "ALARM"})
            mark = {"smoke": "SD", "co": "CO", "smoke+co": "SD/CO"}[a.kind]
            _label(msp, f"{a.id} {mark}", Pt(a.at.x, a.at.y - 2.5 * TEXT), "ALARM", TEXT * 0.7)

    return draw


def _framing_plan(b: Building, level: Level) -> Callable[[Modelspace], None]:
    def draw(msp: Modelspace) -> None:
        runs: dict[tuple[str, str, str, float], list[Member]] = {}
        for m in b.members:
            if m.level != level.id:
                continue
            msp.add_line((m.start.x, m.start.y), (m.end.x, m.end.y), dxfattribs={"layer": "MEMBER"})
            if m.spacing:  # repetitive members get one label per run, below
                runs.setdefault((m.role, m.nominal, m.species_grade, m.spacing), []).append(m)
                continue
            plies = f"({m.plies}) " if m.plies > 1 else ""
            at = _beside(m.start, m.end, _mid(m.start, m.end), -TEXT)
            _label(msp, f"{m.id}: {plies}{m.nominal} {m.role}", at, "MEMBER", TEXT * 0.7)
        for (role, nominal, _, spacing), run in runs.items():
            middle = run[len(run) // 2]
            ids = run[0].id if len(run) == 1 else f"{run[0].id}-{run[-1].id}"
            text = f"{ids}: {nominal} {role} @ {fmt_in(spacing)} o.c."
            _label(
                msp,
                text,
                _beside(middle.start, middle.end, _mid(middle.start, middle.end), -TEXT),
                "MEMBER",
                TEXT * 0.7,
            )
        _framing_dims(b, level.id, runs, msp)
        _posts(b, level.id, msp)

    return draw


def _stations(m: Member, crossings: list[tuple[Pt, Pt, float]]) -> list[Pt]:
    """Points along a member: its ends, and where each support crosses it (in order, no repeats)."""
    length = m.length
    ts = [0.0, length]
    for a, c, half in crossings:
        if segments_distance(m.start, m.end, a, c) <= half + 0.5:
            t = line_crossing(m.start, m.end, a, c)
            if t is not None and -1 <= t <= length + 1:
                ts.append(min(max(t, 0.0), length))
    return [_along(m.start, m.end, t) if t else m.start for t in _distinct(ts)]


def _framing_dims(
    b: Building, level_id: str, runs: dict[tuple[str, str, str, float], list[Member]], msp: Modelspace
) -> None:
    """Spans and cantilevers: one joist of each run, dimensioned between its supports and ends;
    each beam, ledger or header, between the posts under it and its ends."""
    on_level = [m for m in b.members if m.level == level_id]
    if not on_level:
        return
    lo, hi = bbox([p for m in on_level for p in (m.start, m.end)])
    center = _mid(lo, hi)
    supports = [(m.start, m.end, m.thickness / 2) for m in on_level if m.role in SUPPORTS]
    supports += [(w.start, w.end, w.thickness / 2) for w in b.walls if w.level == level_id and w.bearing]
    for run in runs.values():
        # The outermost joist of the run, dimensioned outside the framing.
        edge = max(run, key=lambda m: distance(_mid(m.start, m.end), center))
        _chain(msp, _stations(edge, supports), _away(edge.start, edge.end, center, 2 * DIM_GAP))
    # A post crosses a member if the member passes over it: model each post as two short crossing lines.
    posts: list[tuple[Pt, Pt, float]] = []
    for p in b.posts:
        half = lumber_size(p.nominal)[1] / 2
        posts += [(Pt(p.at.x - 1, p.at.y - 1), Pt(p.at.x + 1, p.at.y + 1), half)]
        posts += [(Pt(p.at.x - 1, p.at.y + 1), Pt(p.at.x + 1, p.at.y - 1), half)]
    for m in on_level:
        if m.role in SUPPORTS:
            _chain(msp, _stations(m, posts), _away(m.start, m.end, center, DIM_GAP + m.thickness))


def _posts(b: Building, level_id: str | None, msp: Modelspace) -> None:
    for p in b.posts:
        if level_id is not None and p.level != level_id:
            continue
        t, w = lumber_size(p.nominal)
        corners = [(p.at.x - t / 2, p.at.y - w / 2), (p.at.x + t / 2, p.at.y - w / 2)]
        corners += [(p.at.x + t / 2, p.at.y + w / 2), (p.at.x - t / 2, p.at.y + w / 2)]
        msp.add_lwpolyline(corners, close=True, dxfattribs={"layer": "POST"})
        _label(msp, f"{p.id} {p.nominal}", Pt(p.at.x, p.at.y + w + TEXT), "POST", TEXT * 0.7)


def _foundation_plan(b: Building) -> Callable[[Modelspace], None]:
    def draw(msp: Modelspace) -> None:
        for f in b.footings:
            if f.kind is FootingKind.PIER:
                msp.add_circle((f.at.x, f.at.y), f.width / 2, dxfattribs={"layer": "FOOTING"})
                size = f"{fmt_in(f.width)} dia"
            else:
                x, y = f.at.x - f.width / 2, f.at.y - f.length / 2
                corners = [(x, y), (x + f.width, y), (x + f.width, y + f.length), (x, y + f.length)]
                msp.add_lwpolyline(corners, close=True, dxfattribs={"layer": "FOOTING"})
                size = f"{fmt_in(f.width)} x {fmt_in(f.length)}"
            text = f"{f.id} {f.kind}\n{size}, {fmt_in(f.depth)} below grade"
            _label(msp, text, Pt(f.at.x, f.at.y - f.width / 2 - 2 * TEXT), "FOOTING", TEXT * 0.7)
        if b.footings:
            # Footing centers, chained both ways; the vertical chain starts at any ledger (the house).
            xs = _distinct([f.at.x for f in b.footings])
            ys = _distinct([f.at.y for f in b.footings] + [m.start.y for m in b.members if m.role is MemberRole.LEDGER])
            low_y = min(f.at.y - f.width / 2 for f in b.footings) - 3 * TEXT
            left_x = min(f.at.x - f.width / 2 for f in b.footings) - 3 * TEXT
            _chain(msp, [Pt(x, low_y) for x in xs], -DIM_GAP)
            _chain(msp, [Pt(left_x, y) for y in ys], DIM_GAP)
        _posts(b, None, msp)

    return draw


def sheets(b: Building) -> list[Sheet]:
    """The sheets this model needs, in set order."""
    out: list[Sheet] = []
    if b.footings:
        out.append(Sheet("S-0", "Foundation plan", _foundation_plan(b)))
    wall_level = {w.id: w.level for w in b.walls}
    for n, level in enumerate(sorted(b.levels, key=lambda lv: lv.elevation), 1):
        on_level = (
            any(w.level == level.id for w in b.walls)
            or any(r.level == level.id for r in b.rooms)
            or any(s.level_from == level.id for s in b.stairs)
            or any(g.level == level.id for g in b.guards)
            or any(wall_level.get(o.wall) == level.id for o in b.openings)
            or any(a.level == level.id for a in b.alarms)
        )
        if on_level:
            out.append(Sheet(f"A-{n}", f"{level.id} floor plan", _floor_plan(b, level)))
        if any(m.level == level.id for m in b.members) or any(p.level == level.id for p in b.posts):
            out.append(Sheet(f"S-{n}", f"{level.id} framing plan", _framing_plan(b, level)))
    return out


def render(b: Building, sheet: Sheet, title_block: str) -> Drawing:
    """One sheet as a DXF document, with its title block under the drawing."""
    doc = new_dxf(setup=True)
    doc.units = dxf_units.IN
    for name, color in LAYERS.items():
        doc.layers.add(name, color=color)
    msp = doc.modelspace()
    sheet.draw(msp)
    extents = dxf_bbox.extents(msp)
    left = extents.extmin.x if extents.has_data else 0.0
    bottom = extents.extmin.y if extents.has_data else 0.0
    lines = [f"{sheet.id}  {sheet.title.upper()}", b.name + (f", {b.address}" if b.address else ""), title_block]
    for i, line in enumerate(lines):
        height = TEXT * (1.5 if i == 0 else 1.0)
        msp.add_text(line, height=height, dxfattribs={"layer": "TITLE"}).set_placement(
            (left, bottom - 4 * TEXT - i * TEXT * 2), align=TextEntityAlignment.LEFT
        )
    return doc


def write_sheets(b: Building, out_dir: Path, title_block: str) -> list[Path]:
    """Write every sheet as <id>.dxf and <id>.pdf; returns the files written."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for sheet in sheets(b):
        doc = render(b, sheet, title_block)
        dxf = out_dir / f"{sheet.id}.dxf"
        doc.saveas(dxf)
        pdf = out_dir / f"{sheet.id}.pdf"
        dxf_matplotlib.qsave(doc.modelspace(), pdf, bg="#FFFFFF", size_inches=(17, 11))
        written += [dxf, pdf]
    return written
