---
name: electrical-practice
description: How electrical work is planned, checked, ordered and inspected in this project - which electrical code applies, who may do the work, smoke and CO alarms (modeled and checked, including hardwiring and interconnection), circuits, GFCI and AFCI protection, outdoor receptacles and lighting, panel capacity, and what an electrician's work order must say. Read before any spec, design, review or work document with wiring, alarms or lighting.
---

# Electrical

## Which code, and who does it
- The electrical code for one- and two-family dwellings is set by the jurisdiction (`jurisdiction/jurisdiction.toml`, `[codes] electrical`). It may be the residential code's electrical chapters or a separate state electrical code based on an NEC edition. If it's blank, ask the building department before designing.
- **Who:** a licensed electrician pulling the electrical permit, unless `jurisdiction/permits.md` says a homeowner may get an electrical permit for this dwelling **and** the owner wants to do the work. Then the owner pulls the homeowner electrical permit and does the work personally, meeting its conditions (owner-occupied, any exam or affidavit).
- **Service and utility side** (service entrance, meter, service drop or lateral, main panel replacement, service upgrades): always a licensed electrician and the utility.
- **In the panel** (adding a breaker for a new circuit): an electrician is recommended. The owner may do it only by an explicit decision in `docs/decisions.md`, and the owner instruction then turns off the main breaker, treats the service lugs as live regardless, and stops on any surprise.
- **Branch circuits, boxes, devices, fixtures and alarms:** owner work when the above allows it, following the owner-instruction hints.

## Smoke and CO alarms (modeled and checked)
The model has `Alarm` elements, drawn on the floor plans. The code pack's helpers check them:
- `irc.smoke_alarms`: one in each sleeping room, one outside each sleeping room in its immediate vicinity (`covers`), one on each story with rooms, none closer to a tub or shower bathroom's door than the code allows (R314.3).
- `irc.co_alarms`: outside each sleeping room where there's a fuel-burning appliance or an attached garage (`Building.fuel_burning_appliances`, `attached_garage`; R315).
- `irc.alarm_power`: hardwired with battery backup, and interconnected (R314.4, R314.6).
- By hand: alarms near cooking appliances (R314.3.3), CO alarms inside a bedroom with a fuel-burning appliance, and the **exceptions for existing buildings**: work on an existing house can trigger alarm upgrades in the whole house (R314.2.2, R315.2.2). The code-reviewer checks these for every addition or alteration.

## Circuits and devices (checked by hand, against the electrical code in force)
Topics the electrician's design and the code-reviewer cover; NEC references for orientation:
- Receptacle layout in habitable rooms, kitchens, baths, outdoors (outdoor and deck receptacles: NEC 210.52).
- GFCI protection (NEC 210.8): baths, kitchens, outdoors, garages, unfinished basements, near sinks.
- AFCI protection (NEC 210.12) for dwelling circuits, including when existing circuits are extended.
- Lighting outlets and switching at stairs and entrances; outdoor fixtures rated for wet locations.
- Panel capacity: a load calculation before adding major loads (heat pump, EV charger, kitchen).
- Wiring methods outdoors and underground: burial depth, conduit, boxes rated for the location.

## Drawings
Alarms appear on the floor plans. An electrical plan (devices, circuits, panel schedule) is the electrician's to produce or check; record their sheets under the phase's **Drawings**.

## Safety
Treat every wire as live until tested. De-energize at the panel, lock it out and tag it, and **test with a tester you've just checked on a known live circuit**. Never work in a panel. Stop and call an electrician on any surprise: aluminum branch wiring, cloth-insulated wiring, no ground, scorched or warm devices, a breaker that won't stay on.
