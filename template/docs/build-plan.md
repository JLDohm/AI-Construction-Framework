# {{PROJECT}}: build plan

Each phase is small and ends with something checked: a design that passes its compliance checks, a permit set, a permit issued, or work that has passed inspection.

Phases don't have to run in number order: design, permits and work overlap. A phase can start once every phase in its **Depends on** column is finished (every phase also depends on phase 0). The pre-commit hook enforces this. Finished means:
- **brief or design** phase: `ready to merge` or `done`;
- **permit or build** phase: `done` only, meaning the permit is issued, or the work's inspections have passed.

Types: `brief` · `design` · `permit` · `build`. Who: `owner`, `sub` (a subcontractor) or `both`.
Status values: `planned` · `in progress` · `ready to merge` · `waiting` (on a permit, a sub or an inspection) · `done`

| Phase | Name | Type | Goal | Who | Depends on | Requirements | Status |
|---|---|---|---|---|---|---|---|
| 0 | brief | brief | Write the requirements, existing conditions, outline, decisions, hazards and this plan; fill in `jurisdiction/`. | owner | — | — | planned |
| 1 | … | design | … | — | 0 | R-… | planned |

## Typical order
An example for a small addition on a slab with its own electrical and plumbing. Phase 0 replaces it with this project's plan.

| Phase | Name | Type | Depends on | Why |
|---|---|---|---|---|
| 1 | foundation and structure | design | 0 | the building permit needs it |
| 2 | coordination | design | 1 | rough layout of every trade (under-slab drains, holes through the foundation and framing, duct and drain chases, panel and equipment locations), so the structure leaves room for them |
| 3 | building permit | permit | 1, 2 | no site work before it's issued |
| 4 | electrical and plumbing design | design | 2 | can run while the permit is in review |
| 5 | under-slab plumbing | build | 3, 4 | must be in and inspected before the slab is poured; the plumber pulls the plumbing permit |
| 6 | foundation | build | 3, 5 | footing inspection before concrete |
| 7 | framing | build | 6 | |
| 8 | rough-ins | build | 7 | electrical and plumbing subs pull their permits; rough-in and framing inspections before insulation |

## Follow-ups
Items found outside a phase: inspector's notes, field problems, plan-review comments. Each is fixed in the next phase that touches that part, or in its own small phase.

None yet. Add each as a row:

| # | Found | What | Fix in |
|---|---|---|---|
| F-1 | <date>, <where: inspection, field, plan review> | <the problem, and why it matters> | <phase> |
