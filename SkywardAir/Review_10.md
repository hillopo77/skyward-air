# Revision10 — room layout and access rebuild

**Current revision10 verification: SUCCESS. Visual approval: pending.** The final run saved 23 genuine game captures and passed all 186 interaction/API checks and all 13 actual walking routes. Fourteen independent saved-source geometry checks passed, and native import/reload succeeded for 110 current exported assets. The first revision10 run is archived in `Versions/Revision10_FirstEngine`; earlier revision09 results remain historical.

The user rejected revision09's cramped front rows, lavatories, crew space, pilot access and unfinished rear/exterior. This pass changes the architecture and circulation rather than adding more seats.

- The main cabin is 35.1m long; the source body is approximately 52.3m long. Capacity stays at four window-side business seats plus forty economy seats in 1–2–1. The latest 2.7m extension enlarges only the aft preparation/crew room; the lavatories stay in place.
- Room order is cockpit → dedicated crew entry → wall → business → wall → main galley → wall → economy → aft service vestibule. The main galley now has a partition on both sides.
- Business row pitch grows to 2.40m and economy pitch to 1.35m. The front rows have separate crossaisle space. Actual walking routes test entry ahead of the seats.
- Both lavatories use approximately 1.50 × 2.60m rooms, 2.20m clear height and 1m entrances, with moving doors and retained full-size fixtures.
- Aft services now include a deeper preparation room, rear crew seats, preparation banks, counter, two retained cart bays, overhead lockers, service interphone and crossaisle alongside the lavatories.
- The cockpit restores analog gauges, green radar and bright red/green pushlights. Raised controls and wider pilot spacing support walking approaches into the footwells; E seating remains available separately. The door now opens inward to keep the crew-room stair landing clear.
- Overhead bins have separate moving lids. A forward floor hatch opens to a modeled stair, lower luggage racks, retained cases and a central walkway. The camera follows the stair and lower floor continuously while collision stays enabled.
- The exterior length, nose, afterbody, wing placement and lower body are adjusted around the larger interior. Latest source fitting corrects the jagged cockpit-roof transition and protruding partition stubs. Its visual finish remains unfinished.

Native validation uses the same E and V actions as play, plus collision-enabled standing walks to the first business/economy rows, both lavatories, galley portals, pilot footwells and lower hold. The final run also passed the aft preparation-room route and lower-hold ascent. Its 26 navigation records comprise 13 initial-placement checks and 13 actual walks; the walking paths do not teleport between waypoints. It records actual viewport screenshots after the view has settled. Planned captures are never substituted for saved images.

Exterior finish, gear bays/mechanisms, the flat grey business-carpet finish, small-label clarity, production UV/tangent cleanup, LODs and performance work remain open. Instruments, passenger doors, recline, service equipment and IFE content are static art; flight simulation and bag handling are not implemented. No characters, paid generation or story were added. Passing the recorded routes establishes tested access, not final visual quality or complete gameplay.

Use `Screenshots.html` for genuine progress images, `README.md` for controls and `ArtBible/EngineValidation.json` for the latest test status.
