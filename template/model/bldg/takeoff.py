"""Material takeoff: what the model needs, counted from its elements, in buying units.

Quantities are net: no waste allowance. The work-planner adds waste when it writes the
materials list, and says how much.
"""

import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from bldg.elements import Building
from bldg.units import fmt_ft_in, fmt_in, to_cuyd

# Dimension lumber is sold in 2 ft steps; longer pieces are special orders.
STOCK_LENGTHS_FT = (8, 10, 12, 14, 16, 18, 20)


@dataclass(frozen=True, order=True)
class Row:
    item: str
    size: str
    qty: float
    unit: str
    note: str = ""


def stock_length_ft(inches: float) -> int | None:
    """The shortest stock length that covers `inches`, in feet; None if longer than 20 ft."""
    for feet in STOCK_LENGTHS_FT:
        if inches <= feet * 12 + 1e-9:
            return feet
    return None


def _lumber(nominal: str, species_grade: str, treated: bool) -> str:
    return f"{nominal} {species_grade}" + (", pressure treated" if treated else "")


def takeoff(b: Building) -> list[Row]:
    pieces: dict[tuple[str, str], int] = defaultdict(int)
    rows: list[Row] = []
    for m in b.members:
        item = _lumber(m.nominal, m.species_grade, m.treated)
        feet = stock_length_ft(m.length)
        if feet is None:
            rows.append(Row(item, fmt_ft_in(m.length), m.plies, "ea", f"{m.id}: longer than 20 ft stock"))
        else:
            pieces[(item, f"{feet} ft")] += m.plies
    for p in b.posts:
        item = _lumber(p.nominal, p.species_grade, p.treated)
        feet = stock_length_ft(p.height)
        if feet is None:
            rows.append(Row(item, fmt_ft_in(p.height), 1, "ea", f"{p.id}: longer than 20 ft stock"))
        else:
            pieces[(item, f"{feet} ft")] += 1
    rows += [Row(item, size, n, "ea") for (item, size), n in pieces.items()]

    concrete = sum(f.volume for f in b.footings)
    if concrete:
        rows.append(Row("Concrete", "footings", round(to_cuyd(concrete), 2), "cu yd", "net volume"))

    openings: dict[tuple[str, str], int] = defaultdict(int)
    for o in b.openings:
        size = f"{fmt_in(o.rough_width)} x {fmt_in(o.rough_height)} rough opening"
        openings[(f"{o.kind.capitalize()} {o.product}".strip(), size)] += 1
    rows += [Row(item, size, n, "ea") for (item, size), n in openings.items()]

    rows += [Row(x.item, x.size, x.qty, x.unit, x.source) for x in b.extras]
    return sorted(rows)


def write_csv(rows: list[Row], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["item", "size", "qty", "unit", "note"])
        for r in rows:
            qty = int(r.qty) if float(r.qty).is_integer() else r.qty
            w.writerow([r.item, r.size, qty, r.unit, r.note])
