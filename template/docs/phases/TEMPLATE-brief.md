# Phase 0: brief

**Status:** draft <!-- draft | approved YYYY-MM-DD | amended YYYY-MM-DD, re-approval needed -->

<!-- Phase 0 only. It designs nothing: it writes the documents every later phase relies on. -->

## Goal
<One or two plain sentences: the project, and what the owner wants at the end.>

## Sources
<Everything read: the owner's notes, sketches, photos, measurements, quotes, the property record, the building department's website. With dates.>

## Documents this phase writes
| Document | Contents | Status |
|---|---|---|
| `docs/requirements.md` | R-1 … from the owner's goals, each with its numbers; the Limits index | … |
| `docs/existing.md` | site and existing building as found; unknowns marked "not checked yet" | … |
| `jurisdiction/` | adopted codes, design values, amendments, permit rules, from official sources (only if still the blank template) | … |
| `docs/outline.md` | the one-page building outline | … |
| `docs/decisions.md` | choices made and still open, with reasons | … |
| `docs/hazards.md` | written by the safety-reviewer | … |
| `docs/build-plan.md` | the later phases, each with its type, who does it, what it depends on, and the requirements it covers, including a coordination phase before the building permit | … |

## Permit and professional needs
- Permit needed? <yes / no / ask the building department>, because <section of `jurisdiction/permits.md`>.
- Permits: <the building permit, and each separate trade permit, with who applies (owner or sub) and the phase it must come before>.
- Work that needs a licensed contractor: …
- Anything beyond the prescriptive code, needing a licensed engineer or architect: … (or "none found")

## Document checks
Mechanical checks the coordinator runs before approval:
- [ ] Every requirement ID is unique, and every **L** requirement is in the Limits index.
- [ ] Every requirement is covered by at least one phase in the build plan.
- [ ] Every design value in `jurisdiction/jurisdiction.toml` that the outline uses is filled in (not 0) and cites a source.
- [ ] Every trade in the build plan is in `packs.conf`.
- [ ] Every phase in a **Depends on** column exists, and no phase depends on itself, directly or in a loop.
- [ ] Every build phase depends on the permit phases it needs (or the spec says why none is needed), and on the work it builds on.
- [ ] Work that must happen early is planned early, e.g. under-slab plumbing and conduit before the slab pour.

## Open questions
1. <Question>. Recommended: <answer>, because <reason>.

<!-- Added after the draft. Never rewrite earlier entries; add new ones below. -->
## Answers (owner, YYYY-MM-DD)
<The owner's answers to the open questions, numbered to match.>

## Amendments (YYYY-MM-DD)
<Each change made after approval: what changed and why. Set the Status line to "amended", and the owner re-approves.>
