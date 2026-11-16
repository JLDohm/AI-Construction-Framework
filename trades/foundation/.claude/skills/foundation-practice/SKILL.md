---
name: foundation-practice
description: How foundation work is designed, checked, ordered and built in this project - footings, piers, pads, slabs and deck footings; frost depth and soil bearing; the posts-on-footings and footing-depth checks; concrete; digging safety (811, trenches); the footing inspection before concrete; and what a concrete or excavation work order and an owner's digging-and-pouring instruction must say. Read before any spec, design, review or work document that touches the ground.
---

# Foundations

Everything rests on this: a mistake here can't be fixed later without taking the building apart.

## Design (the designer, with the code pack's guide)
- **Depth.** Every footing's bottom is below the frost depth (`frost-depth` in `jurisdiction/jurisdiction.toml`) and at least the code minimum (`irc.footing_depth` checks both). If `frost-depth` is 0, stop: the building department gives it.
- **Soil.** The code's footing tables assume a soil bearing value (the presumptive values in R401.4). Unless the soil has been tested, design for the lowest value the tables allow, and note it as an assumption in `docs/existing.md`. Fill, organic soil, clay that swells, high groundwater or a slope near the footing are outside the prescriptive rules: **needs a licensed engineer**.
- **Size.** Footing width and thickness come from the code's footing tables for the load and soil (house footings: the R403.1 tables; deck footings: the deck footing table in R507, which uses the joist and beam spans). Sized by hand until a table is added to the code pack; the structural-reviewer checks it.
- **Posts on footings.** Every post bears wholly on its footing (`foundation.posts_on_footings`), with a post base or anchor the design names as a product (a decision). Posts aren't buried in concrete unless the code section and the product allow it.
- **Concrete.** The strength required depends on the jurisdiction's weathering region (Table R402.2): fill in `[design] weathering` first. Name the mix (bagged mix brand and type, or ready-mix strength) in the spec.
- **Water.** Grade slopes away from the building; footing drains where the code requires them (R405). Don't dig below a neighbor's footing or next to a wall without asking a professional.

## Checks
- `irc.footing_depth(b, r, frost_rule="frost-depth")`: every footing, code minimum and frost depth.
- `foundation.posts_on_footings(b, r, level=...)`: every post wholly on a footing (cites the code's continuous load path, R301.1).
- By hand (structural-reviewer): footing size for the load and soil, concrete strength, anchorage and uplift, drainage, distance to property lines and existing footings.

## Drawings
The foundation plan (S-0) shows every footing with its size and depth below grade. A building department usually wants it **dimensioned**: footing locations from a fixed line (the house, a property line) and between footings. Until the drawings have dimension lines, add the dimensions as notes.

## The work
**Sequence:** locate utilities (811) → lay out → dig → **footing inspection before any concrete** → place concrete → cure → set post bases → backfill. Book the inspection ahead (`jurisdiction/permits.md`), and never pour before it passes.

**Safety** (add these to `docs/hazards.md` and every work document):
- **Call 811** (or your state's one-call service) before any digging, and wait the required time for marks; check the state's rule for how long. Hand-dig near the marks. Damaging a gas or power line can kill.
- **Trenches and holes:** never enter a trench deeper than 5 ft without a protective system; cover or barricade open holes overnight.
- **Concrete:** wet concrete burns skin (gloves, long sleeves, eye protection); mixing bagged concrete and cutting cured concrete make silica dust (respirator rated for it, wet methods).
- **Lifting:** an 80 lb bag is heavy; use two people or smaller bags.

## Who does it
Digging and pouring footings for a deck or shed is commonly owner work, if the jurisdiction lets a homeowner pull the building permit (`jurisdiction/permits.md`). Basements, foundation walls, slabs for living space, and anything near existing footings usually go to a concrete or excavation contractor.
