# {{PROJECT}}: how we work

This project uses **const-framework**, a simple process for planning and building a residential project under the IRC (International Residential Code). Work happens in phases. Each phase goes from spec, to checks, to design or work, to review, and ends with the owner merging it.

The packs this project uses are in `packs.conf`: the code in force ({{CODE}}), the latest code the project also designs to (`prefer`, if any), the jurisdiction ({{JURISDICTION}}) and the trades.

## Roles

| Who | Does |
|---|---|
| **Owner** (the human) | Decides what to build, approves each phase spec, does every merge to `main`, submits permits, hires and pays subcontractors, does the owner's own work, and signs everything. |
| **Coordinator** (the main Claude session) | Plans, runs the agents, relays results, explains things in plain language. Does not design, write checks, or write work orders itself. |
| **spec-writer** agent | Writes the phase spec: scope, design criteria, check plan, inspections and work packages. |
| **designer** agent | Writes the failing checks, then the building model until they pass; regenerates the drawings and takeoff. |
| **work-planner** agent | Turns an approved build phase into work orders (for subcontractors) and owner instructions (for the owner). |
| **code-reviewer** agent | Checks the design against the code pack and the jurisdiction's amendments, citing a section for every finding. Read-only. |
| **structural-reviewer** agent | Checks the load path, spans, bearing, connections and foundations, and flags anything beyond the IRC's prescriptive rules as "needs a licensed engineer". Read-only. |
| **constructability-reviewer** agent | Checks that it can be built as drawn: sequence, trade conflicts, stock sizes, cost. Read-only. |
| **safety-reviewer** agent | Checks jobsite and occupant hazards, and keeps `docs/hazards.md` (its only file). Otherwise read-only. |
| **check-critic** agent | Checks whether the compliance checks would really catch a noncompliant design. Read-only. |
| **concision-reviewer** agent | Keeps specs, work orders and instructions short and precise without losing any number or condition. Read-only. |

The owner is an owner-builder, not a design professional. Explain decisions simply, define jargon the first time it appears (e.g. "header: the beam over a window or door opening"), and when asking the owner to choose, give a recommendation.

## Where things live

- `packs.conf`: the code edition, jurisdiction and trades this project was set up with.
- `docs/owner.md` (if present): the owner's own details (name, contact, the property's address), copied from the owner profile in their private pack folder. Use them instead of asking again, and confirm the address is this project's property.
- `docs/requirements.md`: what the project must achieve, with IDs (R-1, R-2, …): rooms, areas, uses, budget, deadline.
- `docs/existing.md`: the site and any existing building as found: measurements, photos, age, hazards found.
- `docs/outline.md`: the one-page building outline (site, footprint, levels, load path, systems, utilities). Every phase must fit it, or change it with the owner's approval.
- `docs/decisions.md`: choices made and why (D-1, D-2, …).
- `docs/build-plan.md`: the list of phases, their type, who does them, what each depends on, and their status.
- `docs/hazards.md`: jobsite and occupant hazards and how each is controlled.
- `docs/budget.md`: estimate from the takeoff and quotes, and actual spending.
- `docs/inspections.md`: every required inspection, booked date, result and inspector's notes.
- `docs/phases/phase-N-<name>.md`: one spec per phase, made from the template for its type in `docs/phases/`.
- `docs/work/`: work orders (`WO-N.x-<trade>.md`) and owner instructions (`OI-N.x-<task>.md`), made from the templates there.
- `jurisdiction/`: adopted codes, local design values, amendments and permit rules.
- `model/`: the building as code: the model, its compliance checks, and the generated drawings and takeoff.

## Where to start

- The first phase is **phase 0** (the brief). It writes the requirements, the existing conditions, the outline, the decisions, the build plan and the hazards, and fills in `jurisdiction/` if it's still the blank template.
- No other phase starts until phase 0 is finished.
- Notes, sketches, photos and quotes from before phase 0 are source material for it, not a substitute for it.
- Before suggesting a next step, read `docs/build-plan.md` and name the phases that can start now (see Phase order). If several can, recommend one and say why.

## Phase types

| Type | Produces | Template |
|---|---|---|
| **Brief** (phase 0 only) | requirements, existing conditions, outline, decisions, build plan, hazards | `TEMPLATE-brief.md` |
| **Design** | part of the building model, its checks, drawings and takeoff. The **coordination** phase is a design phase: see Phase order | `TEMPLATE-design.md` |
| **Permit** | one permit: its application set (drawings, energy compliance, any calculations), and the permit issued | `TEMPLATE-permit.md` |
| **Build** | the work itself, through work orders and owner instructions, ending with passed inspections | `TEMPLATE-build.md` |

## Phase order

Design, permits and work overlap, as on any real job. Each phase in `docs/build-plan.md` lists the phases it **depends on**, and the pre-commit hook blocks a `phase-N-…` commit until they're finished. Every phase also depends on phase 0.
- A **brief or design** phase is finished when it's `ready to merge` or `done`.
- A **permit or build** phase is finished only when it's `done`: the permit is issued, or the work's inspections have passed. A released permit set is not a permit.

How phases usually depend on each other:
- **Design the structure, then coordinate.** Before the building permit, a **coordination** phase roughs in every trade's layout: under-slab and in-wall routes, holes through the foundation and framing, chases for ducts and drains, and the panel, meter and equipment locations. The structure is then designed to leave room for them, and the structural reviewer checks every hole and notch. The trades can be detailed and permitted later; their layout can't.
- **One permit per permit phase.** The building permit comes before any site work. A trade permit (electrical, plumbing, mechanical) that the jurisdiction issues separately comes before that trade's work. If a licensed sub pulls it, it is a hold point in the sub's work order rather than its own phase. `jurisdiction/permits.md` says which permits exist and when each is needed.
- **Work follows the inspections.** A build phase depends on the permits it needs and on the work it builds on. Watch for work that must happen early: under-slab plumbing and conduit are installed and inspected before the slab is poured.
- To go ahead without a dependency on purpose, the owner decides, the decision is recorded in `docs/decisions.md`, and the commit uses `ALLOW_PHASE_ORDER=1`.

## The phase cycle

Run it with the `phase` skill. In short:

1. **Branch.** `git switch -c phase-N-<name>` from an up-to-date `main`, once the phases it depends on are finished.
2. **Spec.** The spec-writer drafts `docs/phases/phase-N-<name>.md`. The reviewers for its type check the draft (always the concision-reviewer; the `phase` skill lists the others), and the spec-writer revises it. Open questions go to the owner.
3. **Approve.** The owner reads the spec and says "approved" or asks for changes. The coordinator records the approval in the spec's Status line. Nothing is designed or built for an unapproved spec.
4. **Design or plan the work.**
   - Design phase: the designer writes the failing checks and commits them, then changes the model until they pass.
   - Permit phase: the designer assembles and releases the permit set (`tools/release.sh permit <rev>`).
   - Build phase: the work-planner writes the work orders and owner instructions.
5. **Review.** The reviewers that apply run independently (the `phase` skill lists which). Findings go back to the designer or work-planner, then the reviewers check again. Stop after three rounds and ask the owner.
6. **Verify.** The coordinator runs `.githooks/verify`. It must pass before merging.
7. **Merge.** The coordinator summarizes the phase for the owner and gives the merge commands. The owner merges.
8. **Out in the world** (permit and build phases). These are merged as `waiting` while the owner submits the permit, hires the subs or does the work, and books the inspections. Results are recorded on a short `phase-N-<name>-record` branch, which the owner merges. A permit phase is `done` when the permit is issued. A build phase is `done` when its inspections have passed and the results are recorded in `docs/inspections.md`. Other phases can run meanwhile, if they don't depend on it.

If the design or the work shows the spec is wrong, stop and amend the spec, and the owner re-approves it. Don't quietly build something different. Changes made in the field are amendments too, and the model is updated to match, so the drawings always show what was really built.

## Rules

1. Never commit to `main` directly. Only the owner merges into it. The pre-commit hook blocks commits on `main`.
2. **Checks first:** see each new compliance check fail, then pass. Once the failing checks are committed, they are locked: changing one needs the owner's agreement.
3. Before handing work back, formatting, lint, the compliance checks and the tests must be clean. Never say "done" with a failing or unrun check.
4. **Follow the latest code where it also meets the code in force.** The code in force (`code` in `packs.conf`) must always be met. When `packs.conf` names a newer code (`prefer`), the design meets it too: every check runs against both, and the report marks the latest-code results "(latest code)". Where the two truly conflict, or meeting the latest code isn't worth it, the code in force wins: the owner decides, the decision goes in `docs/decisions.md`, and a waiver naming it goes in `model/checks/waivers.toml`. A waiver never excuses the code in force.
5. **Every check and every compliance finding names its code section** (e.g. `IRC R310.2.1`) or the local amendment. No section, no rule.
6. **Code text is copyrighted.** Store numbers, units and section IDs, never copied code text. A rule value is used for a permit set only after the owner checks it against their copy of the code (`verified = true`). `cd model && .venv/bin/python -m bldg rules --todo` lists what's left to verify; the code pack's guide says how.
7. **Never guess a design value.** Snow load, wind speed, frost depth, soil bearing and the like come from `jurisdiction/` or a named source. A value of 0 means "not filled in yet": stop and ask.
   **Provisional assumptions.** Two unknowns need not hold up design: a site measurement not taken yet, and an inspection list the department hasn't confirmed. A spec may adopt a stated, conservative assumption instead (P-1, P-2, … in `docs/existing.md`, or the inspection list marked provisional in `docs/inspections.md`), naming what will replace it. Every result that rests on one is **provisional**: `bldg check` and the drawings say so, and the coordinator warns the owner every time results are shown. A permit set is never released while one is left (`release` refuses), no work starts on one, and an assumption never closes an engineering-boundary item. Code and jurisdiction values (frost depth, snow load, soil bearing and the like) are never assumed.
8. **Engineering boundary.** Anything outside the IRC's prescriptive rules is not designed here: spans beyond the tables, point loads with no prescriptive path, removing or changing a bearing wall without a header table, retaining walls over 4 ft, high-wind or high-seismic sites, or anything the jurisdiction says needs a design professional. Record it as an open question marked **needs a licensed engineer or architect**. Never claim to stamp, certify or approve anything.
9. **Who may do the work.** `jurisdiction/permits.md` says what a homeowner may do under their own permit. Owner instructions are written only for that work, and only for work the owner has said they want to do. Everything else is a work order for a licensed contractor.
10. **Safety in every owner instruction:** PPE, stop conditions and when to call a professional. Always: call 811 before digging, de-energize and test before electrical work, test for lead (homes built before 1978) and asbestos before disturbing old materials, and never enter a trench deeper than 5 ft without protection.
11. **Units are explicit.** The model works in inches. Every dimension is a named constant with its source (requirement, code section, product data sheet, or field measurement).
12. Every number in the requirements (area, height, clearance, budget, date) gets a check that measures it. Phase specs list these under **Limits**.
13. **Products and materials** named in a design (windows, connectors, fasteners, sheathing) are a decision. The spec lists them under **New products**, with the data sheet or listing that proves they suit the use. Record each in `docs/decisions.md`.
14. Record any decision someone would later ask "why did we do it this way?" about in `docs/decisions.md`.
15. **Never order, book, pay or submit anything yourself.** Ordering materials, hiring subs, submitting permits and booking inspections are the owner's.

## The building model

The model is Python code in `model/`. Read `.claude/skills/model-practice/SKILL.md` before writing or reviewing it, and each trade's guide (`.claude/skills/<trade>-practice/SKILL.md`) before working on that trade. Run `ls .claude/skills` to see which are installed.

To add a trade, run `{{FRAMEWORK}}/new-project.sh . --trades <trade>` (the const-framework folder this project was set up from).

## Checks

The `.githooks/pre-commit` hook runs automatically on every commit:
- it runs every check in `.githooks/checks.d/`: formatting, lint, types, the model's compliance checks (`python -m bldg check`) and its tests;
- a missing tool fails the commit with an install hint, because a check that didn't run is not a pass;
- for the failing-checks commit only, `CONST_FAILING_CHECKS=1 git commit ...` lets the new checks fail while every other step still runs. Never use `--no-verify`.

Run the same checks by hand with `.githooks/pre-commit`.

**Before merging:** `.githooks/verify` runs every check on a clean copy of the committed branch, which catches files that were never committed, and audits the model's dependencies.

**Formatting:** run `.githooks/format` before committing. The hook only *checks* formatting, so a blocked commit means: run `.githooks/format`, review with `git diff`, then commit again.
