# const-framework

A way to run a residential construction project with Claude Code, for an owner-builder working under the IRC (International Residential Code): remodels, additions, decks, ADUs, sheds and new homes. It works the way a careful software team does:

1. **Write down what to build before building it.** Each phase gets a short spec.
2. **You approve the spec before anything is designed or built.**
3. **Checks first.** The code-compliance and fit checks for a phase are written before the design, seen to fail, then the design is drawn until they pass.
4. **Someone other than the author reviews the work.** Independent reviewer agents check code compliance, structure, buildability and safety.
5. **Only you merge into `main`**, after the branch passes every check from a clean copy.

Plans are **code**: a Python model of the building generates the drawings (DXF and PDF), the material takeoff and the compliance report. The git hook runs the checks on every commit, each naming the code section it enforces (e.g. stair riser height, IRC R311.7.5.1).

The framework goes from the project brief, to plans, to code compliance, to a permit set, to the work itself: a **work order** for a subcontractor, or **step-by-step instructions** for you.

> **Status:** under construction. See [docs/design.md](docs/design.md) for how it fits together and the table below for progress.

| Step | What | Status |
|---|---|---|
| 1 | Scaffold: `new-project.sh`, git hooks, pack folders, self-test | done |
| 2 | Project docs and templates (CLAUDE.md, requirements, outline, phases, work orders) | done |
| 3 | Agents and the `phase` skill | done |
| 4 | The `bldg` building-model package (drawings, takeoff, check runner) | done |
| 5 | The `irc-2021` code pack | done |
| 6 | Jurisdiction packs (`TEMPLATE`, and support for your own packs kept in a separate folder), code packs sharing one set of check helpers, designing to the latest code | done |
| 7 | Trade packs: foundation, framing, electrical (plumbing, mechanical, envelope later) | done |
| 8 | Dimension lines, a first plumbing pack, and an example project end to end (a deck with an outdoor receptacle, light and hose bib) | in progress |
| 9 | Provisional assumptions: design goes on before site measurements and the inspection list are known, with results marked provisional and releases refused until they're replaced | in progress (this branch) |

## Limits

- It is **not** a licensed engineer, architect or inspector, and it never claims to stamp or certify anything. Work beyond the IRC's prescriptive rules is flagged "needs a licensed engineer or architect".
- Building codes are copyrighted. Rule files hold numbers and section IDs only. You confirm each value against your own copy of the code (`python -m bldg rules --todo` lists them with their sections) before a permit set can be released. Span tables start empty: you type in the rows your design uses.
- You only get instructions for work your jurisdiction lets a homeowner do under their own permit. Everything else becomes a work order for a licensed contractor.

## Start a project

```bash
path/to/const-framework/new-project.sh path/to/my-deck --name "Back Deck" \
    --jurisdiction TEMPLATE --trades foundation,framing
cd path/to/my-deck
claude                 # then say: start phase 0
```

- `--jurisdiction`: a jurisdiction pack. `TEMPLATE` is a blank one that phase 0 fills in from official sources; once filled in for a real place, keep it as your own pack (see **Your own packs**).
- `--code`: the code in force, a code pack (the framework has `irc-2021`). A jurisdiction pack names the code it enforces (its `CODE` file) and that's used automatically; otherwise the default is `irc-2021`.
- `--prefer`: the latest code, which the design also meets wherever that doesn't break the code in force. A jurisdiction pack can set it (its `PREFER` file). Every check runs against both codes; exceptions are owner decisions with a waiver in `model/checks/waivers.toml`.
- `--trades`: packs in `trades/`, comma-separated.
- The choices are recorded in the project's `packs.conf`. Run the script again to add a trade (`new-project.sh . --trades electrical`). It refuses to change the code edition or jurisdiction, because that changes every check: do that by hand, as a recorded decision.
- Existing files are never overwritten.

## What a project gets (so far)

```
CLAUDE.md                     how we work: roles, phase types, phase order, the phase cycle, rules
.claude/agents/
  spec-writer.md              writes the phase spec (and the phase 0 documents)
  designer.md                 writes failing compliance checks, then the model until they pass
  work-planner.md             writes work orders (subs) and owner instructions
  code-reviewer.md            code compliance, citing a section for every finding (read-only)
  structural-reviewer.md      load path, spans, connections, holes; flags engineer-required work (read-only)
  constructability-reviewer.md  buildable as drawn, sequence, trades, takeoff and cost (read-only)
  safety-reviewer.md          jobsite and occupant hazards; keeps docs/hazards.md
  check-critic.md             would the checks catch a bad design? (read-only)
  concision-reviewer.md       keeps specs and work documents short without losing anything (read-only)
.claude/skills/phase/         the phase cycle for the coordinator, by phase type, plus recording results and field changes
.claude/skills/model-practice/  how the building model, its checks, rules, drawings and releases are written
model/project.py              the building, as code
model/checks/                 the project's compliance checks, named by check-plan ID (T-N.x), citing rules
model/rules/                  rule values from the code pack, local amendments in rules/local/
model/bldg_checks/irc.py      check helpers for IRC-based codes; the code pack supplies their values and sections
.claude/skills/<code>-practice/  the code pack's guide: verifying values, auto vs by-hand topics, engineering boundary
jurisdiction/                 the jurisdiction pack: adopted codes, design values (as rules), amendments, permits
model/bldg/                   the library: elements, units, check runner, drawings (DXF + PDF), takeoff
model/requirements.lock       exact versions of the model's tools (ezdxf, matplotlib, pytest, ruff, mypy, pip-audit)
tools/release.sh              freezes a checked permit or construction set in model/releases/
packs.conf                    the code edition, jurisdiction and trades chosen
docs/requirements.md          R-1, R-2, … the owner's goals, with a Limits index
docs/existing.md              the site and existing building as found
docs/outline.md               one-page building outline: site, spaces, design criteria, load path, systems
docs/decisions.md             D-1, D-2, … choices and why
docs/build-plan.md            the phases: type (brief, design, permit, build), who, dependencies, status; follow-ups
docs/hazards.md               jobsite and occupant hazards, stop-work conditions
docs/inspections.md           required inspections and their results; field measurements
docs/budget.md                estimate from the takeoff and quotes; actual spending
docs/phases/TEMPLATE-*.md     spec layouts: brief (phase 0), design, permit, build
docs/work/TEMPLATE-*.md       work order (for a sub) and owner instructions
.githooks/pre-commit          blocks commits on main and phases whose dependencies aren't finished; runs every check in checks.d/
.githooks/checks.d/model.sh   ruff, mypy, the model's compliance checks, pytest (model/.venv)
.githooks/format              fixes formatting (format.d/)
.githooks/verify              before merge: all checks + long-run tests on a clean copy, then dependency audit
.gitattributes, .gitignore
```

Steps 6–7 add the jurisdiction and trade packs.

After setting up a project, install the model's tools once: `cd model && python3 -m venv .venv && .venv/bin/pip install -r requirements.lock`.

## Day to day

- A new project starts with **phase 0**, the brief: say **"start phase 0"**. It writes the requirements, existing conditions, outline, decisions, hazards and the build plan, and fills in the jurisdiction from official sources. No other phase starts until phase 0 is merged.
- After that, say **"start the next phase"**. Phases are one of:
  - **design:** checks first, then the building model until they pass, then review;
  - **permit:** one permit's application set, released and tagged `permit-<rev>`. You submit it;
  - **build:** work orders for subs and step-by-step instructions for you. The phase is done when its inspections pass.
- Claude stops and asks you at the approvals (spec, outline changes, new products) and at merging. It never orders, books, pays or submits anything.
- Tell Claude when something happens outside: "the permit was issued", "the footing inspection passed", "we moved the post 6 inches". It records the result on a short `phase-N-…-record` branch, or handles it as a field change (amend the spec, update the model, stop the work first if it touches structure or safety).
- Design needn't wait for every site measurement or for the department's inspection list. A spec can adopt a stated, conservative **provisional assumption** instead. Until it's replaced, Claude tells you the results are provisional, the check report and drawings say so, and no permit set is released and no work starts.
- Design, permits and work overlap, as on a real job. Each phase lists the phases it **depends on**, and the pre-commit hook blocks a `phase-N-…` commit until they're finished: a design phase when it's ready to merge, a permit phase when the permit is issued, a build phase when its inspections pass. A **coordination** design phase before the building permit roughs in every trade's layout (under-slab lines, holes through the structure, chases), so trades can be detailed and permitted later without rework.

## Packs

| Kind | Folder | Adds to a project |
|---|---|---|
| Code | `codes/<edition>/` | rule values with section IDs for the shared check helpers, and a practice skill for the reviewers |
| Jurisdiction | `jurisdictions/<name>/` | adopted editions, local design values (snow, wind, seismic, frost depth, climate zone), amendments, permit and inspection rules, what a homeowner may do |
| Trade | `trades/<trade>/` | a practice skill, work-order hints, and that trade's checks: `foundation` (posts on footings), `framing` (joists on two supports), `electrical` (guide and hints; alarms are checked by the code helpers), `plumbing` (guide and hints; pipe holes are checked by the code helpers) |

Each pack is a folder laid out like a project. Its files are copied into the project, except `PACK.md`, which describes the pack, and a jurisdiction's `CODE` and `PREFER`, which name the code in force and the latest code to design to. To add a pack, add a folder with a `PACK.md` and the files it gives a project.

## Your own packs

Packs for a particular place (your jurisdiction, your state's version of the code) can live in a separate folder, laid out like this repository (`codes/`, `jurisdictions/`, `trades/`), for example a private repository. Point `new-project.sh` at it with `--packs DIR` (repeatable) or `CONST_PACKS=DIR1:DIR2`. Pack folders are searched before the framework, and each project records them in its `packs.conf`, so later runs (adding a trade) find the same packs.

A pack folder can also hold an **owner profile**: `owner/`, laid out like a project (usually just `owner/docs/owner.md` with your name, contact and address). `new-project.sh` copies the first one it finds into each new project, and phase 0 uses it instead of asking again. Keep it in a private folder only.

A state code based on the IRC is a code pack with just rule files and a guide: the check helpers are shared, and its rule files give the same rule ids their values and sections (copy `codes/irc-2021/` and change the values, `code` and `section` fields).

## Changing the framework

Edit the files in `template/` (shared by all projects), `codes/`, `jurisdictions/` or `trades/`. Projects already set up keep their own copies, so copy any improvements into them by hand.

Test a change with `tools/selftest.sh`. It runs shfmt and ShellCheck on every script, sets up a scratch project, runs its hooks, and drives the model through a seeded defect and a release. It keeps the model's tools in `~/.cache/const-framework/` (rebuilt when `requirements.lock` changes; `CONST_SELFTEST_VENV` overrides the location).
