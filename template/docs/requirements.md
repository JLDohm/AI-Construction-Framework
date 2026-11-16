# {{PROJECT}}: requirements

Each requirement has an ID that phase specs and checks refer to. Never reuse an ID. If a requirement is dropped, mark it ~~struck through~~ and say why.

- **L** marks a requirement with a number that needs a check (rule 12): an area, height, clearance, count, cost or date. Each is listed in the Limits index below.
- Code requirements are not repeated here: the code pack and `jurisdiction/` cover them. These are the owner's own goals, plus anything stricter than code that the owner wants.

| ID | Requirement | Source |
|---|---|---|
| R-1 | … | <conversation, sketch, notes, date> |
| R-2 | **L** e.g. The deck is at least 12 × 16 ft. | … |
| R-3 | **L** e.g. Total cost at most $8,000, materials and subs, excluding the owner's labor. | … |

## Limits index

Every **L** requirement, the phase that checks it (see `docs/build-plan.md`), and how. A phase can only check what it and earlier phases have designed.

| Phase | Limits (how checked) |
|---|---|
| 1 <name> | R-2 (model check), R-3 (takeoff total in docs/budget.md) |
