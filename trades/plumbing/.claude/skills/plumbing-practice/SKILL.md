---
name: plumbing-practice
description: How plumbing is planned, checked, ordered and inspected in this project - which plumbing code applies and who may do the work, supply and drain design topics, pipes through framing, freeze and backflow protection (e.g. frost-free hose bibs with vacuum breakers), pressure tests, the plumbing permit and inspections, and what a plumber's work order and an owner's plumbing instruction must say. Read before any spec, design, review or work document with water or drain piping.
---

# Plumbing

## Which code, and who does it
- The plumbing code for one- and two-family dwellings is set by the jurisdiction (`jurisdiction/jurisdiction.toml`, `[codes] plumbing`): the residential code's plumbing chapters, or a separate state plumbing code. If it's blank, ask the building department before designing.
- **Permit:** plumbing usually needs its own permit, separate from the building permit (check `jurisdiction/permits.md`). It's a dependency of the plumbing work in the build plan, or a hold point in a plumber's work order.
- **Who:** where `jurisdiction/permits.md` lets a homeowner install their own plumbing, small supply work like a hose bib can be owner work. Gas piping, water heaters, sewer connections and anything under a slab go to a licensed plumber by default; the owner may decide otherwise only by a recorded decision, and gas never.

## Design topics (checked by hand, against the plumbing code in force)
The code-reviewer and the plumber cover these; the guide names the topic, the code gives the numbers.
- **Supply:** pipe material and size for the fixtures served; shutoff valves; water hammer; pressure.
- **Drains and vents:** pipe size by fixture units, slope, cleanouts, traps and vents. Plan routes in the coordination phase: drains are big and must slope, so they constrain framing more than anything else.
- **Pipes through framing:** every hole or notch is a modeled `Hole` (checked by `irc.holes` for joists, rafters and beams; studs and plates by hand). Pipes close to the face of framing need steel protection plates where the code requires them, so drywall screws and nails can't reach them.
- **Freeze protection:** no water pipes in exterior walls, unheated spaces or crawlspaces without the protection the code requires. Outdoors, use a **frost-free sillcock** long enough that its valve seat sits inside the heated space, pitched to drain toward the outside.
- **Backflow protection:** every hose connection has a vacuum breaker (built into the sillcock, or added) so garden-hose water can't be siphoned back into the drinking water. Irrigation systems need their own backflow preventer, usually with its own permit and testing.
- **Products:** valves, sillcocks, fittings and pipe are named products (maker and model, listed for potable water); each is a decision.

## Checks
- Automatic: holes and notches in framing (`irc.holes`) for every modeled pipe route.
- By hand: everything above. When a project depends on a plumbing rule often, add a helper and rule values to the code packs.

## The work
**Sequence:** permit → shut off and drain → rough-in (pipes, fittings, valves, supports, protection plates) → **pressure test** → **rough-in inspection** before anything is covered → fixtures and trim → final inspection.

**Safety:**
- Know where the main shutoff is, and test that it closes, before cutting any pipe.
- Old houses: galvanized steel or lead pipes, or lead solder on old copper, are a stop-and-ask: lead in drinking water is a health hazard, and old pipes break when disturbed.
- Torches (sweated copper): fire watch, a heat shield behind the joint, a fire extinguisher at hand, and check the area again 30 minutes after the last joint. Prefer press or push-fit fittings where listed and allowed.
- Never work near gas piping you aren't sure of; never move or connect gas lines.
