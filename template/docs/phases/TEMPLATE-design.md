# Phase N: <name>

**Status:** draft <!-- draft | approved YYYY-MM-DD | amended YYYY-MM-DD, re-approval needed -->

<!-- For a phase that adds or changes part of the building model: e.g. foundation, floor framing, walls and openings, roof, electrical layout, plumbing, heating and ventilation. Also for the coordination phase, which roughs in every trade's layout before the building permit. -->

## Goal
<One or two plain sentences: which part of the building is designed and checked at the end of this phase.>

## Requirements covered
- R-x: <fully / partly — which part>

## Scope
**In:**
- …

**Out (later phases):**
- …

## Outline
<Which parts of docs/outline.md this phase touches. If it changes the outline (footprint, levels, load path, a system's approach), describe the change here; the owner approves it with this spec.>

## Design criteria
<The values this phase designs to, each from `jurisdiction/jurisdiction.toml`, the code pack, or a requirement. Write "not filled in" for any that are 0, and add an open question. Where the latest code (`prefer` in `packs.conf`) differs from the code in force, give both and design to both; a true conflict is an open question (the code in force wins, with a decision and a waiver).>

| Item | Value | Source |
|---|---|---|
| e.g. Floor live load | 40 psf | IRC Table R301.5 |
| e.g. Frost depth | 42 in | rule `frost-depth` in `jurisdiction/jurisdiction.toml` |

## Elements
<What the model gains or changes, with the key sizes. Exact dimensions belong in the model, not here.>

| Element | Does | Size / type | Material and grade | Rule or table it follows |
|---|---|---|---|---|
| e.g. Deck joists | carry the deck boards to the beams | 2×8 @ 16 in o.c., 11 ft 6 in span | Southern pine #2, PT ground contact | IRC Table R507.6 |

## Connections to existing work
<Where this phase meets existing structure or earlier phases: ledger attachment, tie-ins, openings cut into existing walls. Name the existing condition each relies on, and how it was found (`docs/existing.md`).>

## Limits
<Measurable numbers this phase must meet: areas, heights, clearances, counts. Each has a check below. Write "none" if there are none.>

## Trade routes and holes
<Where pipes, wires and ducts run through or under what this phase designs: sleeves through the foundation, under-slab lines, holes and notches in joists, studs and top plates, chases and soffits, equipment locations. Each hole and notch has a check against its code limit. In the coordination phase this is the main content. Write "none" if nothing passes through.>

## Engineering boundary
<Anything this phase touches that is outside the IRC's prescriptive rules. Write "none" if there is none. Each item becomes an open question marked **needs a licensed engineer or architect**, and is not designed here.>

## Check plan
Level: **rule** (one code rule on one element, run by `python -m bldg check`), **fit** (elements fit together or with existing conditions), **takeoff** (quantities or cost), **drawing** (a sheet shows what it must).

| ID | Level | Element / situation | Pass if | Section or requirement |
|---|---|---|---|---|
| T-N.1 | rule | each stair riser | ≤ 7.75 in, and risers in a flight within 3/8 in of each other | IRC R311.7.5.1 |
| T-N.2 | rule | … at exactly the limit, and one step past it | at the limit passes; past it fails | … |
| T-N.3 | fit | e.g. each drain hole in a floor joist | diameter ≤ 1/3 of joist depth, ≥ 2 in from the edges | IRC R502.8.1 |

## Drawings
<The sheets this phase adds or changes: e.g. "S-1 foundation plan", "A-2 deck framing plan", "D-1 ledger detail". Each must show the dimensions and notes the inspector needs.>

## New products
<Each product the design names (connectors, fasteners, windows, sheathing, membranes): what it's for, the data sheet or evaluation report (e.g. ICC-ES ESR number) showing it suits this use, and alternatives. Each becomes a decision. Write "none" if there are none.>

## Open questions
1. <Question>. Recommended: <answer>, because <reason>.

<!-- Added after the draft. Never rewrite earlier entries; add new ones below. -->
## Answers (owner, YYYY-MM-DD)
<The owner's answers to the open questions, numbered to match.>

## Amendments (YYYY-MM-DD)
<Each change made after approval: what changed, why, and which checks it adds or changes. Set the Status line to "amended", and the owner re-approves.>
