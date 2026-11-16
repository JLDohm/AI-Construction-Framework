# Jurisdiction pack: TEMPLATE

A blank jurisdiction, for projects whose jurisdiction has no pack yet. Phase 0 fills in the copied files from official sources (the building department's website and code list, its design-criteria table, the state's code adoption and licensing rules). Once filled in for a real place, consider adding it to the framework as its own pack.

Adds to a project:
- `jurisdiction/jurisdiction.toml`: the department, the codes it enforces, non-numeric design values (climate zone, seismic category), and numeric design values as rules (`frost-depth`, `ground-snow-load`, `ultimate-wind-speed`) that the checks read. A value of 0 means "not filled in" and is never guessed.
- `jurisdiction/amendments.md`: local changes to the model code.
- `jurisdiction/permits.md`: which permits, who may apply, what a homeowner may do, how to apply, inspections.

No `CODE` file: any code pack can be used with it.
