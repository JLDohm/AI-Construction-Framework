---
name: framing-practice
description: How wood framing is designed, checked, ordered and built in this project - floor and deck joists, beams, ledgers, headers, posts, connectors and fasteners; span tables and their rows; joist spacing and support checks; holes and notches; treated lumber and corrosion; the framing inspection; and what a framing work order and an owner's framing instruction must say. Read before any spec, design, review or work document with framing.
---

# Framing

## Design (the designer, with the code pack's guide)
- **Spans from the tables.** Joist spans are checked against the code pack's span tables (`irc.deck_joist_spans`, `irc.floor_joist_spans`). The owner types in the rows the design uses; the check names any missing row. The table's species and grade must match the lumber that will be bought (the grade stamp on each piece), and its footnotes (loads, deflection, wet service) must fit the use.
- **Spacing.** The model lays joists out with `spaced_positions(length, spacing)`; the span check fails if adjacent joists end up farther apart than their stated spacing.
- **Support.** Every joist rests on at least two supports (beams, ledgers, headers, plates, bearing walls: `framing.joists_supported`). Rim joists don't count. Each support itself is carried down to a footing (load path, R301.1): the structural-reviewer traces it.
- **Bearing and hangers.** Minimum bearing length (R502.6), or a joist hanger rated for the member, installed with the fasteners its maker specifies. Hangers, post caps, post bases and lateral-load connectors are products: name each one (maker, model, and its evaluation report) under **New products**.
- **Ledgers** attached to a house are one of the most common causes of deck collapse: the ledger, its fasteners and flashing follow the deck section of the code pack (R507 ledger rules) exactly, against a rim the existing-conditions survey has confirmed is sound. Never nails alone. Check the lateral load connection rule too.
- **Beams and headers** come from the code's tables (deck beam table; header tables in R602.7), sized by hand until tables are added to the code pack. Anything beyond the tables: **needs a licensed engineer**.
- **Holes and notches** for pipes, ducts and wires are modeled as `Hole`s and checked (`irc.holes`). Engineered lumber (I-joists, LVL) follows only its maker's hole chart.
- **Treated lumber** for anything outdoors or near the ground, rated for ground contact where the use calls for it. Fasteners and connectors in treated lumber must be rated for it (hot-dip galvanized or stainless, R317.3): name them.
- **Stock sizes.** Lengths in 2 ft steps up to 20 ft; the takeoff flags longer pieces. Lay out to reduce waste.

## Checks
- `irc.deck_joist_spans` / `irc.floor_joist_spans` (with spacing), `framing.joists_supported`, `irc.holes`.
- By hand (structural-reviewer): beams, headers, posts (height and size), bearing lengths, hangers and their fasteners, ledger attachment, lateral loads, cantilevers, bracing, decking span.

## Drawings
The framing plan (S-n) shows every member with size, spacing and label. A building department wants **all spans and cantilevers dimensioned** (deck submittal lists commonly ask for it): until the drawings have dimension lines, add them as notes. Details for the ledger, post-to-beam and post-to-footing connections are separate sheets.

## The work
**Sequence:** footings inspected and set → posts → beams → ledger (flashed) → joists and hangers → blocking → **framing inspection** (before decking or covering, if the permit requires it) → decking → guards and stairs → final.

**Safety** (in `docs/hazards.md` and every work document):
- Falls: work from a stable platform; guards or a harness above 6 ft; ladders 3 ft above the landing at a 4:1 angle.
- Temporary bracing: posts and beams braced until the structure is complete.
- Nail guns: trigger lock on, never carry with a finger on the trigger, eye protection.
- Saws: guards in place; hearing and eye protection; a dust mask when cutting treated lumber, and never burn its scraps.
- Lifting: beams and long boards with two people.

## Who does it
Deck and shed framing is commonly owner work under a homeowner building permit. Structural changes to a house (bearing walls, headers in existing walls, new floors) usually go to a framing contractor, and anything beyond the tables to an engineer first.
