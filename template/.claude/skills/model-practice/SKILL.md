---
name: model-practice
description: How the building model in model/ is written, checked, drawn and released - the bldg package's elements, project.py conventions (inches, named constants with sources), compliance checks named by check-plan ID and citing rules, rule files and their verification, the failing-checks commit, drawings, takeoff and releases. Read before writing or reviewing anything in model/.
---

# The building model

The building is Python code in `model/`. The model is the source of truth: drawings, the takeoff and the compliance report are generated from it, never edited by hand.

```
model/
  project.py          this project's building: building() -> Building
  checks/phase_N.py   this project's checks, one module per phase, named by check-plan ID
  rules/<code>/       rule values from the code pack (e.g. rules/irc-2021/)
  rules/local/        the jurisdiction's amendments, loaded last
  bldg/               the library: elements, geometry, units, checks runner, drawings, takeoff
  tests/test_bldg_*   the library's own tests (don't edit; they come from the framework)
  tests/test_*.py     this project's tests
  out/                generated: drawings, takeoff.csv, check-report.txt (not committed)
  releases/<kind>-<rev>/  frozen permit and construction sets (committed, never changed)
```

## Setup and commands
```sh
cd model && python3 -m venv .venv && .venv/bin/pip install -r requirements.lock   # once
.venv/bin/python -m bldg check        # run the checks; -v shows every result
.venv/bin/python -m bldg build        # drawings (DXF + PDF) and takeoff into out/
.venv/bin/python -m bldg rules --todo # rule values not yet verified or filled in, with sections
tools/release.sh permit A             # from the project root: freeze a permit set (also: ifc)
```
The pre-commit hook runs ruff, mypy (strict), `bldg check` and pytest. Run `.githooks/format` before committing.

## Writing project.py
- **Inches everywhere.** Use `ft(10, 6)` for 10 ft 6 in. Square feet only for display (`to_sqft`).
- **Every dimension is a named constant with its source** in a comment: a requirement, a code section, a data sheet, or a field measurement from `docs/existing.md`.
  ```python
  DECK_WIDTH = ft(16)        # R-2: at least 12 x 16 ft
  JOIST_SPACING = 16         # in o.c.; IRC Table R507.6 column used
  LEDGER_HEIGHT = ft(2, 6)   # measured 2026-05-02, docs/existing.md
  ```
- **Never guess a value.** If a design value is 0 or missing in `jurisdiction/` or `docs/existing.md`, stop and report it, unless the approved spec lists a **provisional assumption** for it (CLAUDE.md rule 7). Then mark the constant and register it on the building:
  ```python
  RIM_DEPTH = 9.25  # PROVISIONAL P-1, docs/existing.md: assumed 2x10 until E-4
  b.provisional = [Provisional("P-1", "rim joist 2x10 solid-sawn, sound", "E-4 inspection opening")]
  ```
  `bldg check` then ends with a PROVISIONAL warning listing each one, working drawings are stamped with them, and `release` refuses until they're gone. When the measurement comes in, replace the value and remove the `Provisional`.
- Build repetitive members with `spaced_positions(length, spacing)`, so each joist is its own element and every one gets checked.
- **Stock sizes:** lumber from `LUMBER_SIZES` (nominal names; actual sizes are looked up, so a 2x10 is 9 1/4 in deep). Members over 20 ft are flagged in the takeoff.
- Ids are short and unique across the whole building (`J1`, `B2`, `F3`, `W12`). `Building.problems()` reports duplicates and broken references, and a problem fails the checks.
- Elements: `Level`, `Room`, `Wall`, `Opening`, `Stair`, `Guard`, `Member`, `Post`, `Footing`, `Hole`, plus `TakeoffItem` for materials the drawings don't count (connectors, fasteners, flashing), each with its source. Read their docstrings in `bldg/elements.py` for what each field measures (e.g. `Opening.clear_width` is the net clear opening from the window's data sheet, not the rough opening).

## Writing checks
One module per phase in `checks/` (`checks/phase_2.py`), one function per check-plan case:
```python
from collections.abc import Iterator

from bldg.checks import Result, Rules, check
from bldg.elements import Building
from bldg.units import fmt_in


@check("T-2.1", rules=["R311.7.5.1-riser-max"])
def riser_height(b: Building, r: Rules) -> Iterator[Result]:
    """Stair riser height"""
    limit = r.value("R311.7.5.1-riser-max")
    for s in b.stairs:
        for i, h in enumerate(s.risers, 1):
            yield Result(f"stair {s.id} riser {i}", h <= limit, fmt_in(h), f"<= {fmt_in(limit)}")
```
- **Name it by the check-plan ID** (`T-N.x`) and **cite** `rules=[...]` (code rules) and/or `requirements=[...]` (owner requirements, `R-3`). A check can only read the rules it declares.
- **Limits come from rule files**, never typed into the check. A requirement's number comes from a named constant that cites the requirement.
- **Check every element of the kind**, not the first one: every riser of every stair, every egress opening of every sleeping room.
- **Measure what the rule measures**: clear opening, not rough opening; actual lumber size, not nominal; from the surface the rule names.
- **Edges:** the check plan has a case at the limit and one past it. Test them in `tests/test_phase_N.py` with small models built in the test (the library tests show how), so the check is proven to fail when it should.
- A check that finds nothing to check **fails**. If a rule truly doesn't apply, yield a passing `Result` saying why (e.g. "no stairs: deck is 18 in above grade").
- Exceptions inside a check, missing rules, and rules with `value = 0` are reported as errors, never skipped.
- **Use the helpers** in `bldg_checks/` rather than rewriting a rule; write your own only for what no helper covers, and propose it for the framework. `bldg_checks/irc.py` serves every IRC-based code (the 2021 IRC, a state code based on an IRC edition, ...): its rule ids are edition-neutral (`riser-max`), and the code pack's rule files give each its value and its section in that edition, which the report cites:
  ```python
  from bldg_checks import irc

  @check("T-3.2", rules=irc.EGRESS)
  def egress(b: Building, r: Rules) -> Iterator[Result]:
      """Emergency escape openings"""
      yield from irc.egress(b, r)

  @check("T-4.1", rules=[*irc.FOOTING_DEPTH, "frost-depth"])
  def footings(b: Building, r: Rules) -> Iterator[Result]:
      """Footing depth and frost"""
      yield from irc.footing_depth(b, r, frost_rule="frost-depth")
  ```

## Two codes: the code in force and the latest code
`packs.conf` names the code in force (`code`) and, optionally, the latest code (`prefer`). `bldg check` runs every check twice: against the code in force (with the jurisdiction's values and local amendments) and against the latest code (with the jurisdiction's values; local amendments amend only the code in force). Both must pass. Latest-code results are marked "(latest code)".
- Where the two truly conflict, the code in force wins. The owner records a decision, and the designer adds a waiver to `model/checks/waivers.toml` (check id, decision, reason). The report shows the check as waived (`~`).
- A waiver never excuses the code in force; one that names a missing decision, or whose check now passes, fails the checks.
- Unverified latest-code values are noted but don't block a release: the permit is judged on the code in force.

## The failing-checks commit
1. Write the checks (and their edge tests) for the cases you were given, before the design.
2. `python -m bldg check` must fail **because the design is missing or wrong**, not because of a typo, an import error or a missing rule.
3. `CONST_FAILING_CHECKS=1 git commit -m "checks(phase-N): failing checks for T-N.x–T-N.y"`. Formatting, lint and types must still pass.
4. From then on the checks are locked: changing one needs the owner's agreement.

## Rule values
- Format: the top of `bldg/rules.py`. Numbers, units and section IDs only, never code text. Tables are lists of rows; `Rule.lookup("span", species_grade=..., size=..., spacing=...)` reads one cell, and fails on a missing row or a 0 cell.
- `value = 0` means not filled in yet. `verified = false` until the owner checks the value against their own copy of the code; the check report lists unverified rules, and a release refuses them.
- **Jurisdiction design values** (`frost-depth`, `ground-snow-load`, `ultimate-wind-speed`, ...) are `[[rule]]` entries in `jurisdiction/jurisdiction.toml`, loaded after the code pack's rules.
- Local amendments go in `rules/local/` with the same id and `amends = true`; the report marks them "(local amendment)".
- Never change a rule value to make a design pass. The owner corrects values; record why in `docs/decisions.md`.

## Drawings and takeoff
- `bldg build` makes a foundation plan (S-0), and per level a floor plan (A-n) and framing plan (S-n), as DXF (open in any CAD program, e.g. FreeCAD or LibreCAD) and PDF. Look at every sheet the phase changes.
- **Dimensions** are drawn from the model: footing centers chained both ways from the ledger (the house); for each joist run, its outermost joist between supports (spans and cantilevers); each beam, ledger and header between its posts and ends; overall wall dimensions on floor plans. Check that every dimension the jurisdiction's submittal list asks for is there; add any other as a note.
- The PDFs are fitted to the page, not to scale: the dimensions are what count.
- The takeoff is net: no waste. The work-planner adds waste and says how much.

## Releases
`tools/release.sh <permit|ifc> <rev>` refuses unless: everything is committed, every check passes, and every rule a check uses is verified. It writes `model/releases/<kind>-<rev>/` (sheets stamped with the set, revision, date and commit; takeoff; check report; `MANIFEST.txt` with the commit and a SHA-256 of every file). Commit it; the owner merges and tags it (`git tag permit-A main`). A release is never changed: fix things in a new revision.

## Test quality (for the check-critic)
- Coverage: `.venv/bin/pytest --cov` isn't installed by default; judge by reading which elements each check visits.
- Seeded defects: for each main rule, make the one-line change to `project.py` that should fail it (e.g. riser 7.75 → 7.8), run `bldg check`, confirm the failure names the right element and section, then undo it. Report any defect that wasn't caught.
