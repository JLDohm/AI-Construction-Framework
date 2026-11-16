# Phase N: <which> permit

**Status:** draft <!-- draft | approved YYYY-MM-DD | amended YYYY-MM-DD, re-approval needed -->

<!-- One permit: the building permit, or a separately issued trade permit that the owner applies for. A trade permit that a licensed sub pulls is a hold point in their work order instead. The owner submits; never submit anything yourself. -->

**Permit:** <building / electrical / plumbing / mechanical / other>  ·  **Applicant:** <owner, as owner-builder / …>
**Covers:** <the work, and the build phases that depend on this permit>

## Goal
<One or two plain sentences: which work this permit covers.>

## What the building department asks for
<From `jurisdiction/permits.md` and the department's submittal checklist, with its date.>

| Item | Where it comes from | Ready? |
|---|---|---|
| e.g. Site plan with setbacks | model sheet C-1 | … |
| e.g. Framing plan and details | model sheets S-1, D-1 | … |
| e.g. Energy compliance (insulation values, window U-factors) | model energy report | … |
| e.g. Application form, owner-builder affidavit | the owner fills in | … |

## Release checks
Before `tools/release.sh permit <rev>` runs:
- [ ] Every design phase this permit covers is finished (the hook checks this through **Depends on**).
- [ ] `python -m bldg check` passes, with **no unverified rules** (`verified = false`): the owner has checked each rule value used against their copy of the code.
- [ ] No open item marked **needs a licensed engineer or architect**, or the professional's stamped documents are included.
- [ ] Every sheet has the project address, sheet number, revision and date.

## Release
- Revision: `permit-<rev>` (e.g. `permit-A`). The release folder is `model/releases/permit-<rev>/`, with `MANIFEST.txt`.
- The owner merges, tags `permit-<rev>`, and submits.

## Plan review
<Filled in when comments come back. Each comment becomes an amendment, a design change in a new phase, or an answer to the reviewer. Never rewrite earlier entries.>

| # | Reviewer's comment | Response | Changed in |
|---|---|---|---|
| 1 | … | … | <phase, sheet, revision> |

**Permit issued:** <number, date, conditions on the permit card>. Record its required inspections in `docs/inspections.md`. Set this phase to `done`: build phases that depend on it can now start.

## Open questions
1. <Question>. Recommended: <answer>, because <reason>.

<!-- Added after the draft. Never rewrite earlier entries; add new ones below. -->
## Answers (owner, YYYY-MM-DD)

## Amendments (YYYY-MM-DD)
