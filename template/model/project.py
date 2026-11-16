"""{{PROJECT}}: the building, as code.

The designer builds this up phase by phase, from the approved specs. Rules for writing it are in
.claude/skills/model-practice/SKILL.md: every dimension is a named constant, in inches, with
its source.
"""

from bldg.elements import Building

NAME = "{{PROJECT}}"
ADDRESS = ""  # from docs/existing.md


def building() -> Building:
    return Building(name=NAME, address=ADDRESS)
