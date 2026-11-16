# Hints: plumbing work

For the work-planner. Who does plumbing work follows the plumbing guide: owner instructions only where `jurisdiction/permits.md` allows a homeowner plumbing permit and the owner wants to do it; gas piping always goes to a licensed contractor.

## Work order (licensed plumber)
- **Code and permit:** the plumbing code in force (`jurisdiction/jurisdiction.toml`); the plumber pulls the plumbing permit and books its inspections (a hold point before work starts).
- **Scope as results:** each fixture, valve and outlet by location (sheets), pipe routes through framing as modeled (holes and notches within the checked limits), protection plates, insulation where freezing is possible, backflow protection.
- **Products:** fixtures and valves with model numbers; who supplies them.
- **Hold points:** pressure test and rough-in inspection before covering; final inspection.
- **Not included** (typical): opening and patching walls, finishes, electrical for appliances.
- **Acceptance:** inspections passed; pressure test held as the code requires, witnessed or documented; no leaks after 24 hours in use; every shutoff labeled and working.
- **The plumber must have:** the state plumbing contractor license and insurance the owner has checked.

## Owner instructions (homeowner plumbing permit)
General shape for supply work; the worked case below is a frost-free hose bib.
- **Before:** plumbing permit issued and posted; main shutoff located and tested; the supply pipe material identified (copper, PEX, CPVC; galvanized or lead: stop); materials listed for potable water; the route and wall penetration from the model.
- **Safety:** water off and drained before cutting; for sweated joints, the torch safety in the guide; eye protection when cutting pipe.
- **Steps with measurements:** every cut, fitting and support at the stated location; pipe supported at the spacing the code requires for its material; protection plates where the pipe is within the code's distance of the framing face.
- **Hold point:** pressure test, then the rough-in inspection before closing any wall or ceiling. Record both in `docs/inspections.md`.
- **Stop and call a plumber if:** the main shutoff doesn't fully close, the pipe is galvanized steel or lead, you find leaks or corrosion you didn't cause, a joint leaks twice, or the route needs a hole bigger than the model allows.

## Worked case: frost-free hose bib through a rim joist
- Sillcock: frost-free, with a built-in vacuum breaker, its length chosen so the valve seat ends inside the heated space with the stated margin; install pitched down toward the outside so it drains.
- Hole through the rim or band joist: modeled as a `Hole` (diameter and distance from the edges checked); sealed and flashed against water and air leaks; the sillcock flange fastened to solid backing.
- Supply: a branch from a cold line with its own shutoff valve inside, pipe size as specified.
- Test: pressure test before closing up; then, with the water on, check for drips at every joint for 24 hours.
- Winter: disconnect hoses in fall (a frost-free sillcock with a hose left on can still freeze and burst inside the wall).
