# const-framework (the framework itself)

This repository is the framework. It is not a construction project built with it. `new-project.sh` copies `template/` and the chosen packs into a project folder. `README.md` describes the workflow that projects follow. How the parts fit together is in `docs/design.md`; the build steps are tracked in the README's status table.

## Layout

- `template/`: files every project gets. `template/CLAUDE.md` (once written) is the CLAUDE.md for *projects*, not for this repo.
- `codes/<edition>/`, `jurisdictions/<name>/`, `trades/<trade>/`: packs. Each is laid out like a project, and its files are copied in. `PACK.md` at a pack's root describes it and is not copied; a jurisdiction's `CODE` file names the code pack it requires.
- IRC-based code packs share the check helpers in `template/model/bldg_checks/irc.py` and differ only in their rule files (same edition-neutral ids, their own values and section numbers). A new edition is a new folder of rule files plus a practice guide.
- Jurisdiction facts come from official sources only, cited with the date checked. Unconfirmed values stay 0 with a note on who to ask.
- **Nothing about a particular place or person in this repository.** Packs for a real jurisdiction or a state code belong in a separate pack folder (`--packs`, `CONST_PACKS`), not here; examples use made-up places.
- `new-project.sh`: sets up a project or adds trades to it. It never overwrites existing files, and it records the chosen packs in the project's `packs.conf`.
- `tools/selftest.sh`: the framework's test.

## Changing the framework

- Projects keep their own copies, so a change here does not reach existing projects. When a change matters to a project already set up, say so, because it has to be copied over by hand.
- Keep README.md in step with any change to the workflow, packs, agents or hooks, including its status table.
- Test a change with `tools/selftest.sh`, rather than only reading the scripts. Extend it when you add behavior.
- Work on a branch and leave the merge into `main` to the owner.
- Shell scripts: `set -euo pipefail`, quote everything, and they must pass `shfmt -i 2` and ShellCheck.

## Construction content

- **Never copy code text** (IRC, NEC, IECC or local codes) into the framework: they are copyrighted. Store numbers, units and section IDs, with the source and `verified = false` until the owner checks them.
- **Never guess a design value** (snow load, frost depth, span). A value of 0 means "not filled in yet". Cite the source and date for every value. The only stand-in is a project's stated **provisional assumption** for a site measurement or inspection list not known yet, which marks results provisional and blocks a release.
- **Stay prescriptive:** anything beyond the IRC's prescriptive rules is a "needs a licensed engineer or architect" item, never a design the framework produces.
- **Safety first** in anything addressed to the owner: stop conditions, PPE, 811 before digging, de-energize and test before electrical work, lead and asbestos in older homes.
