# {{PROJECT}}: decisions

Record choices someone would later ask "why did we do it this way?" about. Newest at the bottom. If a decision is replaced, don't delete it: add a new entry and mark the old one "replaced by D-x".

## D-1: Use const-framework for this project
- **Date:** {{DATE}}
- **Decision:** Plan and build in phases with an approved spec, compliance checks first, independent review, and the owner merging. Code edition {{CODE}}, jurisdiction {{JURISDICTION}} (see `packs.conf`).
- **Why:** It keeps each step small, checked and recorded, from plans to passed inspections.

## D-2: Design to the latest code where it also meets the code in force
- **Date:** {{DATE}}
- **Decision:** The design must meet the code in force (`code` in `packs.conf`). Where `packs.conf` also names a newer code (`prefer`), the design meets that too, wherever doing so doesn't break the code in force. Every exception is a decision here and a waiver in `model/checks/waivers.toml`.
- **Why:** Newer editions fix problems found in older ones, the code in force may be replaced during or soon after the project, and a building that meets both is safer and easier to sell or alter later.

## D-3: The building model's tools
- **Date:** {{DATE}}
- **Decision:** The building is Python code (`model/`, the `bldg` package from const-framework). Drawings use **ezdxf** (DXF files, MIT licence) and **matplotlib** (PDF output, PSF-based licence). Checks use **pytest**, **ruff**, **mypy** and **pip-audit**. Exact versions are in `model/requirements.lock`.
- **Why:** Plans as code can be checked automatically on every commit, reviewed line by line, and regenerated after any change. DXF opens in any CAD program; PDF is what building departments take. All are maintained, free, and run on Linux, macOS and Windows.
