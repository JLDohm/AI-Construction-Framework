# Code pack: irc-2021

The 2021 International Residential Code as rule values (numbers and section IDs, never code text) and check helpers.

Adds to a project:
- `model/rules/irc-2021/*.toml`: rule values for rooms, ceilings, emergency escape openings, stairs, handrails, guards, footing depth, holes and notches in sawn framing, smoke and CO alarms, and the continuous load path; plus two span tables (deck joists, Table R507.6; floor joists, Table R502.3.1(2)) that start empty for the owner to fill in from the code. Every value starts `verified = false`.
- Values for every rule id the shared helpers (`template/model/bldg_checks/irc.py`) use, with their 2021 IRC sections.
- `.claude/skills/irc-2021-practice/SKILL.md`: verifying rule values, which topics are checked automatically and which by hand, and the engineering boundary.

Not yet covered (checked by hand, listed in the guide): fire separation, footing sizes, deck footings, posts, beams, ledgers and lateral connections, headers, wall bracing, roofs, energy.
