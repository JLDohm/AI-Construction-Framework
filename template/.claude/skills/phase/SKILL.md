---
name: phase
description: Runs one phase end to end: brief, design (including coordination), permit or build. Covers choosing a phase whose dependencies are finished, branch, spec, owner approval, checks-first design or work planning, independent reviews, clean-copy verify, merge hand-off, and recording permits, inspections and field changes afterwards. Use when starting, resuming or finishing any phase in docs/build-plan.md, or when the owner reports a permit, an inspection result or a change made on site.
---

# Running a phase

You are the coordinator. You run the agents and keep the owner informed. You do not write the spec, the model, the checks, or the work documents yourself. You never order, book, pay for or submit anything.

## 0. Find where we are
- Read `docs/build-plan.md`, `docs/inspections.md`, and the spec of any phase `in progress`. Run `git status` and `git branch --show-current`.
- Work out which phases **can start**: every phase in its **Depends on** column (and phase 0) is finished. A brief or design phase is finished when `ready to merge` or `done`; a permit or build phase only when `done`. In a new project, that's only phase 0.
- Tell the owner, in a few lines: what's in progress, what's `waiting` (and on what: a permit, a sub, an inspection), and which phases can start. Recommend one: usually the one that unblocks the most others, or the one with the longest lead time (permits, long-lead materials).
- If the owner asks for a phase whose dependencies aren't finished, say which and why they matter. Go ahead only if the owner insists: record that as a decision, and commit with `ALLOW_PHASE_ORDER=1`.
- If the owner reports news from outside (a permit issued, plan-review comments, an inspection result, a change made on site), go to **Recording results** or **Field changes** below.
- Resume from whichever step below is unfinished.

## 1. Branch
- `git switch main && git switch -c phase-N-<short-name>`.
- Mark the phase `in progress` in `docs/build-plan.md`.

## 2. Spec
- Start the **spec-writer**. Tell it the phase number, name and type, the requirements it covers, and the source material to read.
- When it's done, start these reviewers on the draft, in parallel:

  | Type | Spec reviewers |
  |---|---|
  | brief | concision-reviewer, code-reviewer (jurisdiction data and permits), structural-reviewer (outline and engineering boundary), safety-reviewer (writes `docs/hazards.md`) |
  | design | concision-reviewer, check-critic (the check plan) |
  | permit | concision-reviewer |
  | build | concision-reviewer, check-critic (the verification table), constructability-reviewer (packages and sequence), safety-reviewer |

- The spec-writer and the concision-reviewer have no shell. Run `wc -w` on the spec yourself and give them the count.
- Have the spec-writer fold in the findings. Concision edits must not drop any number, tolerance, section ID, safety condition or check. If one would, keep the original.
- Pass on any "unclear or contradictory" items as open questions.
- **The spec-writer has no web access.** When the spec needs an outside source (the jurisdiction's adopted codes, its design-criteria table, its permit checklist, a product's data sheet or evaluation report), find the official page yourself if you can, give the spec-writer the URL, the date and what it says, and tell the owner where it came from. If you can't find an official source, it stays an open question for the owner.
- Show the owner a short summary, the open questions with your recommendations, and the path to the spec. Point out:
  - changes to the outline or the build plan (including dependencies);
  - new products;
  - every item marked **needs a licensed engineer or architect**;
  - any design value still "not filled in".

## 3. Approval: the owner's call
- Wait for the owner to say it's approved. Have the spec-writer record the owner's answers under **Answers (owner, date)** and fold them in, or record them in `docs/decisions.md`.
- A spec with an open **needs a licensed engineer or architect** item can be approved only if that item is out of this phase's scope, or the owner has the professional's documents to include.
- Set the Status line to `approved YYYY-MM-DD`, and commit on the branch: `docs(phase-N): approved spec`, with any outline and build-plan changes.
- Record each approved new product as a decision in `docs/decisions.md`.

## 4. Do the phase's work
**Brief (phase 0):** see the Phase 0 section below.

**Design:**
- Start the **designer** with the spec path. For a large check plan, give it one slice of cases at a time.
- Check its report: failing checks committed first (`checks(phase-N): …`), then the design that passes them (`design(phase-N): …`), then a clean `.githooks/pre-commit`.
- Show the owner the changed sheets (`model/out/`), in plain words: what was designed and why.

**Permit:** see the Permit phases section below.

**Build:**
- Start the **work-planner** with the spec path. It writes one work order per `sub` package and one owner instruction per `owner` package.
- Run `wc -w` on each document for the concision-reviewer.

## 5. Review
Start the reviewers for the phase's type in parallel. Give them only the spec path, the branch and the documents to review, not your own opinion, so their reviews stay independent.

| Type | Reviewers |
|---|---|
| design | check-critic, code-reviewer, constructability-reviewer; **structural-reviewer** if the phase adds or changes structure, foundations, or holes through structure (always in the coordination phase); **safety-reviewer** if it adds heights, stairs, excavation, electrical, gas or combustion equipment |
| permit | code-reviewer (the whole set, against the jurisdiction's checklist) |
| build | safety-reviewer, constructability-reviewer, concision-reviewer, code-reviewer (each work document) |

- Send any FAIL or must-fix findings to the designer or work-planner, then review again.
- After three rounds without a PASS, stop and ask the owner how to proceed.
- A round counts only if it sends the design, checks or work back. Check a wording-only fix yourself, without another round.
- Pass on to the owner every **needs a licensed engineer or architect** item, every **unverified rule** in use, and the reviewers' cost, schedule and site-check notes.

## 6. Verify
- Make sure everything is committed (`git status`), then run `.githooks/verify`.
- If it fails, send the problems back to the designer or work-planner, review the changes again, and verify again.
- If the dependency audit finds a known vulnerability in the model's tools: have the designer update it if a fix exists; otherwise explain the risk in plain words and record the owner's decision.

## 7. Hand-off
- Update the phase's status in `docs/build-plan.md` and commit it on the branch:
  - **brief or design:** `ready to merge`;
  - **permit or build:** `waiting`: the documents are ready, and the phase now waits on the world (the permit office, the subs, the work, the inspections).
- Give the owner a plain-language summary:
  - what was designed or planned, and how to look at it (sheets, documents);
  - what was deferred;
  - new decisions and products;
  - the verify result;
  - which phases this unblocks;
  - for permit and build phases: exactly what the owner does next, in order (see those sections below).
- Give them the merge commands; don't run them:
  ```
  git switch main
  git merge --no-ff phase-N-<short-name> -m "Merge phase N: <name>"
  git branch -d phase-N-<short-name>
  ```
- After the owner merges, mark a brief or design phase `done` in the build plan on the next phase's branch.

## Phase 0
Phase 0 (brief) designs nothing. Its spec is the plan for these documents, and the spec-writer drafts all of them:
- `docs/requirements.md`: R-1, R-2, … from the owner's goals, each testable, with its numbers;
- `docs/existing.md`: the site and existing building as found;
- `jurisdiction/`, if it's still the blank template: adopted codes, design values, amendments, permit rules, from official sources only;
- `docs/outline.md`: the one-page building outline;
- `docs/decisions.md`: choices made and still open, with reasons, including who does which work;
- `docs/build-plan.md`: the later phases with type, who, dependencies and requirements, including a **coordination** design phase before the building permit, and one permit phase per permit the owner applies for;
- `docs/hazards.md`, written by the safety-reviewer.

Ask the owner about anything missing: goals, sizes, budget, deadline, who uses the building, which work they want to do themselves and their experience, and what they've already measured or tested. Values that need a site visit or a call to the building department are open questions with exactly what to measure or ask.

The owner approves all of these documents with the spec. Run the spec's **Document checks** yourself (they are mechanical) in place of the designer and the review step. Then verify and hand off as usual.

## Permit phases
- **Assemble:** the spec lists what the jurisdiction asks for. The designer produces any missing sheets or reports from the model (design phases must already be finished; the hook checks this).
- **Release checks:** run them from the spec. Every rule value the set relies on must be `verified = true`; if not, list them for the owner, who checks each against their copy of the code and tells you the value and edition. Have the designer record it.
- **Release:** have the designer run `tools/release.sh permit <rev>` and commit the release folder. The code-reviewer reviews the released set.
- **Hand-off:** the owner merges, tags `permit-<rev>` (`git tag permit-<rev> main`), fills in the application, and submits it. Never submit anything yourself.
- **Plan-review comments** come back as entries in the spec's **Plan review** table, on a `phase-N-<name>-review` branch. Each comment becomes an amendment and, if the design changes, a new design phase or an amendment to the design phase. Then a new permit revision.
- **Issued:** see Recording results.

## Build phases
- **Before the work:** the owner, not you, sends work orders to subs, checks licenses and insurance, signs contracts, buys materials and books inspections. Tell the owner exactly which, in order, with the documents to use.
- **During the work:** when the owner asks for help on site, answer from the owner instruction, the drawings and the trade guide. If the question shows the plan is wrong or a stop condition was hit, say "stop" plainly, and follow Field changes.
- **After each inspection:** see Recording results.

## Recording results
Permits issued, plan-review comments, inspection results and field measurements are recorded on a short branch, `phase-N-<name>-record`, and merged by the owner like any phase.
- **Permit issued:** record the number, date and conditions in the permit spec, and the required inspections in `docs/inspections.md`. Set the permit phase `done`.
- **Inspection:** record the date, result and inspector's notes in `docs/inspections.md`, and the field measurements. Each failed item or correction notice becomes a follow-up (F-x) in the build plan, fixed before the work is covered.
- **Build phase done:** when every row of its **Verification** table has passed, set it `done`. Tell the owner which phases this unblocks.

## Field changes
Anything built differently from the drawings, for any reason, is a change:
1. If it touches structure, safety, egress, fire separation, or anything an inspector checks, **stop that part of the work** until the change is approved, and say so plainly.
2. The spec-writer adds an **Amendment** to the build phase (and to the design phase it changes), and the owner re-approves.
3. The designer updates the model so its checks still pass, or reports why they can't. A change that fails a check, or that goes beyond the prescriptive rules, needs the owner's decision and maybe a professional; it may also need a revised permit (ask the building department).
4. The drawings now match what was built. Record field measurements in `docs/inspections.md`.
