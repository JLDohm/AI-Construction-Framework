# How const-framework fits together

const-framework runs a residential construction project (remodels, additions, decks, sheds, ADUs, new homes under the IRC) the way a careful software team runs a project: small phases, a written spec the owner approves, checks written before the design, independent reviewers, and an owner who does every merge.

## Mapping from software to construction

| Software practice | Here |
|---|---|
| Code | The building model (`model/project.py`, the `bldg` package), which generates drawings (DXF, PDF) and a material takeoff |
| Tests written first | Compliance and fit checks, named by check-plan ID (`T-N.x`), each citing a code section or an owner requirement; committed failing, then the design is changed until they pass |
| Language packs | **Code packs** (rule values for an edition of the code), **jurisdiction packs** (adopted codes, local design values, amendments, permits), **trade packs** (guides, work-order hints, trade checks) |
| Release | A permit set or an issued-for-construction set, frozen with a manifest (`tools/release.sh`) |
| Hardware-in-the-loop | Inspections and field measurements (`docs/inspections.md`) |

## Phases

Four types: **brief** (phase 0: requirements, existing conditions, outline, decisions, hazards, build plan), **design** (part of the model, checks first; the **coordination** phase routes every trade through the structure before the building permit), **permit** (one permit's application set, released and submitted by the owner), and **build** (work orders for subcontractors, step-by-step instructions for the owner, done when inspections pass).

Phases don't run in number order: each phase lists the phases it **depends on**, and the pre-commit hook blocks a phase until they're finished. A brief or design phase is finished when ready to merge; a permit or build phase only when done (permit issued, inspections passed).

## Rules and checks

- Rule values live in TOML (`model/rules/<code>/`): numbers, units and section IDs, never code text (it's copyrighted). Each is `verified = false` until the owner checks it against their own copy of the code; a release refuses unverified rules. A value of 0 means "not filled in" and fails any check that uses it: design values are never guessed. Span tables start empty, and the owner types in the rows a design uses.
- Check helpers for IRC-based codes are shared (`template/model/bldg_checks/irc.py`) with edition-neutral rule ids; a code pack only supplies values and sections, so a state code based on an IRC edition is just a folder of rule files and a guide.
- A check can read only the rules it declares, and one that finds nothing to check fails.
- **Designing to the latest code:** a project names the code in force (`code` in `packs.conf`) and, optionally, the latest code (`prefer`). Every check runs against both; both must pass. A true conflict goes to the code in force through an owner decision and a waiver (`model/checks/waivers.toml`); a waiver never excuses the code in force.
- Jurisdiction design values (frost depth, snow load, wind speed) are rules in `jurisdiction/jurisdiction.toml`; local amendments go in `model/rules/local/` and apply only to the code in force.

## Boundaries

- Anything outside the IRC's prescriptive rules is not designed: it becomes an open question marked **needs a licensed engineer or architect**. Nothing here stamps or certifies.
- Owner instructions only for work the jurisdiction lets a homeowner do and the owner wants to do; everything else is a work order. Service and utility-side electrical work, and gas piping, always go to licensed contractors.
- Claude never orders, books, pays for or submits anything.

## Packs for a particular place

Real jurisdictions and state codes belong in a separate pack folder (`new-project.sh --packs DIR` or `CONST_PACKS`), laid out like this repository. Projects record the folder in `packs.conf`. Jurisdiction facts come from official sources, each cited with the date checked.

## Known limits

- PDFs are fitted to the page, not to scale; the dimensions on them are what count.
- Many code topics are checked by hand (each code pack's guide lists which); footing, beam and header sizing are among them.
- Plumbing, mechanical and envelope packs are first versions or not written yet.
