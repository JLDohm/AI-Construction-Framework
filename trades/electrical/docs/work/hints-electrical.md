# Hints: electrical work

For the work-planner. Who does electrical work follows the electrical guide: owner instructions only where `jurisdiction/permits.md` allows a homeowner electrical permit and the owner wants to do it; service and utility-side work always goes to an electrician.

## Work order (licensed electrician)
- **Code and permit:** the electrical code in force (`jurisdiction/jurisdiction.toml`); the electrician pulls the electrical permit and books its inspections (a hold point before work starts).
- **Scope as results:** each circuit, device and fixture by location (floor plan sheets), the alarm locations and types from the model (`Alarm` elements: smoke, CO or combination; hardwired with battery backup; interconnected), GFCI and AFCI protection as the code requires, any panel or service work, a load calculation if loads are added.
- **Products:** owner-supplied fixtures and devices, if any, with model numbers; alarm model (listed for the purpose; combination units listed for both).
- **Hold points:** rough-in inspection before insulation or covering; final inspection.
- **Not included** (typical): patching and painting walls, trenching (if the owner digs), fixtures the owner supplies but doesn't want installed.
- **Acceptance:** inspections passed; every GFCI and AFCI tested; every alarm tested and the interconnection proven (one sounds, all sound); panel directory labeled; the electrician's as-built notes of circuit routing.
- **The electrician must have:** the state electrical contractor license and insurance the owner has checked.

## Owner instructions (homeowner electrical permit)
- **Before:** the homeowner electrical permit issued and posted, its conditions met; the circuit plan agreed (each circuit's breaker size and type, wire size and type, GFCI or AFCI protection, devices and boxes, routes through framing as modeled `Hole`s); materials checked against it (wire gauge matching the breaker, boxes sized for the conductors, devices and alarms listed for the use, outdoor parts rated for wet locations).
- **Safety first, every time:** turn off the circuit (the main breaker for any panel work), lock and tag it, and **test for voltage with a tester you've just checked on a known live circuit**. Never touch the service lugs or the service conductors: they stay live with the main off. PPE: safety glasses; insulated tools for panel work.
- **Steps with measurements:** box locations and heights from the floor plan; holes in framing within the modeled limits (diameter and distance from edges); cable stapled within the distances the code requires and protected where it passes close to the framing face; conductors left long enough in each box; every connection tight, with no bare copper outside the terminal.
- **Hold point:** the rough-in inspection before insulation or covering. Record it in `docs/inspections.md`.
- **Finish and test:** devices and covers on; every GFCI and AFCI tested with its test button and a plug-in tester; alarms tested and the interconnection proven (one sounds, all sound); the panel directory labeled. Then the final inspection.
- **Stop and call an electrician if:** you find aluminum branch wiring, cloth-insulated or ungrounded wiring, scorched or warm devices or wires, a breaker that trips again or won't reset, a panel without room for the breaker, more conductors in a box than it's sized for, or anything you didn't expect. Never work live.
