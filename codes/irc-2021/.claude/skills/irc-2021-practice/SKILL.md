---
name: irc-2021-practice
description: How this project uses the 2021 International Residential Code - the rule values in model/rules/irc-2021/ and how the owner verifies them, which check helpers in model/bldg_checks/irc.py cover what, which code topics are checked automatically and which by hand, and where the IRC's prescriptive rules end and a licensed engineer or architect is needed. Read before writing a spec, a check plan, checks, or a code or structural review.
---

# The 2021 IRC in this project

The IRC (International Residential Code) covers one- and two-family dwellings and townhouses up to three stories, and their accessory structures (sheds, garages, decks). It is **prescriptive**: follow its tables and rules and no engineering is needed. Outside them, it isn't.

Code text is copyrighted. This project stores **numbers and section IDs only**. The owner reads the code (ICC's free read-only edition at codes.iccsafe.org, or a printed copy); never paste its text into the project.

Local amendments change the model code: always read `jurisdiction/amendments.md` and `model/rules/local/` with this guide.

## What the pack gives
- `model/rules/irc-2021/*.toml`: rule values, all `verified = false` until the owner checks them.
- The shared helpers in `model/bldg_checks/irc.py` (how to call them: the model-practice guide) read these values by edition-neutral ids (`riser-max`); each rule's `section` is what the report cites.

## Verifying rule values (the owner)
1. `cd model && .venv/bin/python -m bldg rules --todo` lists every rule not yet verified, with its section.
2. The owner looks each one up in their copy of the 2021 IRC, including the section's exceptions, and tells the coordinator "R311.7.5.1 riser max is 7 3/4, verified", or the correct value.
3. The designer sets `verified = true` (or corrects the value and its `source`), on a phase branch, and records one decision: "D-x: IRC rule values verified by the owner against <edition and printing> on <date>: <ids>".
4. Verify the rules a phase relies on before its permit set: a release refuses unverified rules.

**Span tables start empty.** For each table a design uses, the owner types the rows the project needs from the code (species and grade written exactly as in the model, e.g. `Southern pine #2`; spans in inches), then marks the rule verified. A check that needs a missing row fails and names the row. Read each table's footnotes: they set the loads and conditions the spans assume.

## Topics: automatic or by hand
The code-reviewer goes through every topic that applies to the phase. **Auto** means a helper checks it on every element; **hand** means the reviewer checks it against the drawings and the code.

| Topic | Sections | Checked |
|---|---|---|
| Habitable room area and dimension | R304.1, R304.2 | auto (`room_sizes`); non-rectangular rooms by hand |
| Ceiling height | R305.1 | auto (`ceilings`); exceptions (sloped ceilings, beams and ducts, bathroom fixtures) and basements (R305.1.1) by hand |
| Emergency escape openings | R310.1, R310.2.1, R310.2.2 | auto (`egress`): presence per sleeping room, clear area, height, width, sill. Window wells and area wells (R310.4), doors as escape openings, basements: by hand |
| Stairs: risers, treads | R311.7.5.1, R311.7.5.2 | auto (`risers`, `treads`): every riser and tread, and the variation |
| Stairs: width, headroom | R311.7.1, R311.7.2 | auto (`stair_clearances`) |
| Stairs: nosings, landings, winders, spiral stairs | R311.7.5.3, R311.7.6, R311.7.5.2.1, R311.7.10 | hand |
| Handrails | R311.7.8, R311.7.8.1 | auto (`handrails`): required count, height. Continuity, grip size (R311.7.8.3–4) by hand |
| Guards | R312.1.1–R312.1.3 | auto (`guards`) for each **modeled** guard: height, openings. Whether every open side over the drop has a guard, guards on stair sides (different limits), and window fall protection (R312.2): by hand |
| Smoke alarms | R314.3, R314.4, R314.6 | auto (`smoke_alarms`, `alarm_power`): in and outside each sleeping room, each story, distance from tub or shower bathroom doors, hardwired and interconnected. Near cooking appliances (R314.3.3) and the existing-building exceptions and upgrade triggers (R314.2.2) by hand |
| Carbon monoxide alarms | R315.1–R315.3 | auto (`co_alarms`) outside sleeping rooms where there's a fuel-burning appliance or attached garage; inside bedrooms with an appliance, and existing-building triggers (R315.2.2), by hand |
| Continuous load path | R301.1 | partly auto with the trade packs: posts on footings (`foundation.posts_on_footings`), joists on two supports (`framing.joists_supported`); the rest of the path by hand |
| Fire separation: garage, dwelling units | R302.5, R302.6, R302.3 | hand |
| Footing depth and frost | R403.1.4, R403.1.4.1 | auto (`footing_depth`), with the jurisdiction's `frost-depth` rule (`jurisdiction/jurisdiction.toml`) |
| Footing size and soil bearing | R401.4, R403.1, Table R403.1(1) | hand |
| Holes and notches in sawn joists, rafters, beams | R502.8.1 | auto (`holes`); hole near a notch, and members 4 in nominal or thicker (tension-side notches), by hand |
| Holes and notches in studs and plates | R602.6, R602.6.1 | hand (the helper flags them) |
| Floor joist spans | Table R502.3.1(2) | auto (`floor_joist_spans`) once the rows are filled in, including joist spacing; Table R502.3.1(1) for 30 psf areas by hand |
| Decks: joist spans | Table R507.6 | auto (`deck_joist_spans`) once filled in; cantilevers by hand |
| Decks: footings, posts, beams, ledger, lateral load, guards | R507.3, R507.4, R507.5, R507.9, R507.9.2 | hand |
| Headers, wall bracing | R602.7, R602.10 | hand |
| Roof framing, roof coverings | R802, Chapter 9 | hand |
| Energy (insulation, windows, air sealing) | Chapter 11 (N1101–N1111) | hand, with the climate zone from `jurisdiction/` |
| Mechanical, plumbing, electrical | Chapters 12–24, 25–33, 34–43 | the trade packs and hand |

When a topic is checked by hand often, propose a helper for it: it belongs in this pack, with tests at the limit and one past it.

## Engineering boundary
Stop and mark **needs a licensed engineer or architect** whenever the design goes outside the prescriptive rules. Read the section named for the exact limit; don't rely on memory.
- **Design conditions:** the IRC's limits on wind (R301.2.1, and R301.2.1.1 for where wind design is required), seismic design category (R301.2.2: categories D0–D2 add limits; E is outside the IRC), ground snow load (R301.2.3), and flood hazard areas (R322). Compare `jurisdiction/jurisdiction.toml` with these before any structural design.
- **Spans and sizes beyond the tables**, or species, grades, loads or spacings a table doesn't list.
- **Point loads with no prescriptive path** to the foundation, girder trusses, and anything carrying more than the tables assume.
- **Bearing walls removed, moved or opened** wider than the header tables allow (R602.7).
- **Cantilevers** beyond R502.3.3 (floors) or Table R507.6 (decks).
- **Retaining walls** not laterally supported at the top retaining more than 48 in of unbalanced fill (R404.4), and foundation walls beyond the R404.1 tables.
- **Soils:** expansive, compressible or shifting soils, fill, or a bearing value below what the footing tables assume (R401.4).
- **Engineered products** (I-joists, LVL, trusses, steel beams) are allowed, but sized only from the manufacturer's published tables and evaluation report, never by eye. Trusses are designed by the truss maker.
- **Buildings outside the IRC's scope** (R101.2): more than three stories above grade, or uses other than dwellings and their accessory structures.
- Anything the jurisdiction requires a design professional for (`jurisdiction/permits.md`).
