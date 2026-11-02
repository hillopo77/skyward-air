# Skyward Air â€” airport and aircraft visual repair

This is the editable local Unreal game and its modeled Blender source. Double-click `Play-Airport.cmd` to play. Run `Open-Airport38.ps1 -Editor` to edit the Unreal level. The preserved37 source and level remain available.

## Current work

The airport has a sectioned entrance, check-in and real baggage transfer, preparation and screening, repacking, concourse, cafÃ©/gallery, washrooms, two gate areas and an enclosed articulated jetbridge connected to the aircraft. The aircraft retains economy, private business suites, service areas, lavatories, cockpit and lower hold.

The latest whole-scene review repairs malformed chair armrests, models supported baggage portals, adds fitted wall panels and quiet floor finishes, and distinguishes lounge carpet from circulation floors. It also replaces pointed window returns, fixes a folded cockpit panel, seats luggage handles and zippers on their bags, and moves suite belts below passengers' hands. Character cuffs, elbow contacts and blouse edges have been rebuilt; adjacent waiting passengers now vary. Local shadow resolution fixes the angular hand-shadow artifacts without removing shadows. Appended window-material aliases now resolve to the same clear, softly tinted glass on both sides.

Character39 supplies original modeled colorful crew/player bodies, four human passenger models and security staff, a shared42-bone rig, seven actions and editable facial/seated shape keys. Airport benches and cafÃ© chairs have been remodeled to fit their proportions. The original first-person hand geometry remains, with matching new player colors.

Flight39 connects the modeled cockpit fittings to a cold-start procedure, engine spooling, braking and steering, real moving flight surfaces and gear, gauge needles and a live panel readout. One moving parent carries the aircraft, fittings, passengers, lights and collision. The airfield has coherent supporting pavement, a23m taxiway and45Ã—2600m runway. This is a game flight model; the runway length is a level-design choice.

## Controls

- Walk/look: WASD and mouse. Shift runs. E or click uses the aimed object. Space stands from a seat.
- Tab toggles free camera. V changes the aircraft view. F7 changes the player color.
- Pilot preparation: Home requests door closure; End requests jetbridge stow. M master power, N avionics, U fuel valves, J pumps, K start air, L beacon. Press1 and2 for engine start and wait for idle.
- C requests taxi/runway clearance. P releases/sets the parking brake. PageUp/PageDown selects idle, taxi or takeoff thrust. A/D steers on the ground; Ctrl brakes.
- Follow the yellow Alpha route. Stop before the hold-short markings, request clearance, enter runway36 and align with the white centerline. F selects takeoff flaps; X controls speedbrakes. At140kt, W raises the nose.
- In flight: W/S pitch, A/D bank, arrow keys yaw, G landing gear and F flaps. Cockpit switches and levers invoke the same control functions as these keys.

## Editable files

- `Airport_Repaired38.blend`: current airport, aircraft fittings and placed rigged character previews.
- `../../Characters/Revision39/Characters39.blend`: the separate editable character cast and pose library.
- Unreal project: `../../SkywardAir/UnrealProject/SkywardAir.uproject`.
- Unreal level: `/Game/Airport38/L_Airport_Repair38`.
- `Exports/airport_layout.json` and `airport_assets.json`: placements, interactions, current geometry/material signatures and aircraft contracts.
- `SourceAssets`, `Fixes` and the character handoff retain the construction, patch, import and verification scripts. `build_source38.py` includes the later39 modules; preserve the37 base library beside it.

## Evidence and limits

`ArtBible` records source geometry, native imports, physical probes, fresh passenger/scanner journeys, staged negative cases, flight checks and actual renderer settings. `Screenshots` contains genuine in-game captures. Character source renders are labeled separately; they are not gameplay screenshots. The final gallery must be regenerated after the final capture set so it does not show obsolete defects.

The frozen final build passed the full fresh entrance-to-airborne route: 174 checks, zero journey teleports and no direct baggage transform assignments. It includes actual queue service, checked-bag transfer, carried-bag screening, boarding, cold start, taxi, takeoff, flight controls, walking/reseating and release of the same carried bag in flight. Separate final sessions passed 27 assembly checks, 92 scanner checks and 28 safety checks. The final roof correction was checked inside and outside before release. All sessions exited cleanly.

At 1920 x 1080 and 100% resolution on the RTX 3060 Laptop GPU / Ryzen 6800H machine, seven airport views measured 58.9 to 59.4 FPS median. The cockpit and chase samples in flight measured 30.6 and 29.9 FPS median. Their 95th-percentile frame times were 40.2 and 41.2 ms, so flight still has slower frames. Airport 95th-percentile frame times were about 30.1 to 30.2 ms. Each airport view used 12 seconds of uncaptured, unprofiled timing; each airborne view used 30 seconds. Profiling was separate, with no concurrent construction/import job. Full method and individual views are in `ArtBible/Performance39.json` and `FlightPerformance39.json`. Screenshot timing is never used as a frame-rate measurement.

The gallery contains 98 selected, hash-checked current game images. Deliberately coarse forced-distance character views, rejected frames and temporal hold/move sequences remain separate technical evidence. `FlightDebug39.json` is explicitly a starting-aboard diagnostic, separate from the fresh route.

Remaining scope limits include flight performance, a simplified game flight model, local single-player moving-platform behavior, stylized costume seams, planar UVs for solid-color character materials and retained first-person hand geometry. The distant landscape/airfield is still simpler than the furnished passenger areas. Automated review used `-NoSound`; it does not establish an audible review. This is a runnable editable Unreal project, not a packaged standalone executable. No proprietary game assets were extracted and no paid generation credits were used.

The visual research uses the supplied screenshots plus the [official Dear Passengers Steam page](https://store.steampowered.com/app/4534960/Dear_Passengers/) and [FLEXUS page](https://flexus.games/). The [Boeing767 airport-planning document](https://www.boeing.com/content/dam/boeing/boeingdotcom/commercial/airports/acaps/767_REV_K.pdf) informed runway/taxiway width and turn scale. The embedded trailer was not playable through the text research reader; unseen frames are not claimed as studied evidence.
