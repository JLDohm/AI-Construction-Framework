# Trade pack: plumbing

Water supply, drains and vents, fixtures, and outdoor water (hose bibs).

**Status:** first version (framework build step 8): a guide and work-order hints. No checks of its own yet: pipe routes through framing are modeled as `Hole`s and checked by the shared helpers; fixtures go in the takeoff as `TakeoffItem`s. Drain sizing, slope and venting are checked by hand until a project needs them automated.

Adds to a project:
- `.claude/skills/plumbing-practice/SKILL.md`: which code and who, design topics, protection of pipes, freeze and backflow protection, tests and inspections, safety.
- `docs/work/hints-plumbing.md`: what a plumber's work order and an owner's plumbing instruction must say, with a worked case for a frost-free hose bib.
