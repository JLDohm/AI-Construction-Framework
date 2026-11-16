# Phase N: <name>

**Status:** draft <!-- draft | approved YYYY-MM-DD | amended YYYY-MM-DD, re-approval needed -->

<!-- For a phase where work is done on site: by subcontractors (work orders) and/or the owner (owner instructions). -->

## Goal
<One or two plain sentences: what is built at the end, and which inspection it passes.>

## Requirements covered
- R-x: <fully / partly — which part>

## Builds from
Must match this phase's **Depends on** in `docs/build-plan.md`.
- Design phases: <phase numbers>, issued-for-construction set `ifc-<rev>`.
- Permits: <permit phases and numbers; trade permits a sub pulls, as hold points below>, or "no permit needed", because <section of `jurisdiction/permits.md`>.
- Earlier work: <build phases whose work and inspections this builds on>.

## Scope
**In:**
- …

**Out (later phases):**
- …

## Work packages
Each package becomes one work order (sub) or one owner instruction (owner). Owner work must be allowed for a homeowner by `jurisdiction/permits.md`, and the owner must have said they want to do it.

| ID | Package | Who | Trade | Document | Depends on | Hold points |
|---|---|---|---|---|---|---|
| P-N.1 | e.g. Dig and pour footings | owner | foundation | `docs/work/OI-N.1-footings.md` | 811 locate, permit | footing inspection before concrete |
| P-N.2 | e.g. Run the deck circuit | sub | electrical | `docs/work/WO-N.2-electrical.md` | P-N.1 | sub pulls the electrical permit; rough-in inspection |

## Sequence
<The order of packages and inspections, with anything that must wait (concrete cure time, inspection booking lead time, material delivery).>

## Materials
<From the takeoff, grouped by package, with who buys them. Long-lead items first.>

## Hazards
<The rows of `docs/hazards.md` that apply, and anything new this phase adds.>

## Verification
Inspections from `docs/inspections.md`, and measurements taken at hold points. The phase is `done` when every row passes.

| ID | Method | What / how | Pass if | Checks |
|---|---|---|---|---|
| V-N.1 | inspection | I-x footing inspection | passed, with notes recorded | permit |
| V-N.2 | measure | footing depth below finished grade, each hole | ≥ frost depth (36 in) | IRC R403.1.4.1 |

## Open questions
1. <Question>. Recommended: <answer>, because <reason>.

<!-- Added after the draft. Never rewrite earlier entries; add new ones below. -->
## Answers (owner, YYYY-MM-DD)

## Amendments (YYYY-MM-DD)
<Field changes go here: what changed, why, and the model change that keeps the drawings matching what was built.>
