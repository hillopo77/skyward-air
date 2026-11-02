# Skyward Air — editable aircraft and airport prototype

**Revision16 is current.** Overhead bins are about5% deeper, 3.5cm farther inward and3cm lower. Revision15 added11 cargo families/118 supported placements and a modeled exterior pass. Use `Run Plane.cmd` to play, `Run Exterior.cmd` to review the airframe, `Plane.blend` to edit, and `Screenshots.html` for the complete current photo gallery.

The easier interaction controls remain: aim at a fitting and use E/left click; **Space stands up**. Focused bin checks replace a full walkthrough for revision16, as requested. See `Review_16.md` for changes, exact verification scope and remaining gaps. Previous reports and geometry are preserved in `Versions/`.

## Rooms and seating

The latest source layout has a 35.1m main cabin. The body is approximately 52.3m long and 5.0m wide; individual seats and service fittings retain their scale. The final 2.7m extension is used only for the aft preparation/crew room. This is a fictional airliner designed around the requested playable spaces, rather than an exact Boeing 767.

From the cockpit toward the tail:

| Area | Source cabin position | Contents |
|---|---|---|
| Crew entry | 0–3.8m | Cockpit door, two crew jumpseats, equipment and open standing space. Passenger seating begins beyond a full-height partition. |
| Business | 3.8–9.6m | Four window-side plum/cream/walnut suites, two rows at 2.40m pitch, sliding privacy doors, consoles, own screens and a clear centre aisle. |
| Main galley | 9.6–12.4m | Its own service room, with a wall on both the business and economy sides, open aisle portals and gathered curtains. |
| Economy | 12.4–27.0m | Forty seats in ten 1–2–1 rows at 1.35m pitch, seatback displays and a front crossaisle. |
| Aft services | 27.0–35.1m | Two larger lavatory rooms and crossaisle, followed by a deeper preparation room with crew seats, banks, counter, retained carts, lockers and interphone. |

Each lavatory retains its approximately 1.50 × 2.60m room and full-size fixtures. Its entrance now faces the central internal corridor, with a sliding pocket door and approximately 1m portal. It opens away from the exterior passenger-door crossaisle.

The public turn behind business suites has approximately 0.67m wall clearance. The front galley partition and its base trims moved 20cm aft after the first full walking test found a blocked approach; its corrected route starts in the centre aisle.

The suites have approximately 30-inch displays with original 1920 × 1080 welcome, flight-information and personal-suite pages. Economy has36 independently controlled seatback displays plus four first-row units mounted within the solid galley bulkheads. The last row uses screen-free rear shells; its passengers retain their forward displays. Each of the 40 economy seating positions explicitly maps to its own display ahead. Every display keeps its own page state. Cup wells, coffee service, connected controller leads, modeled USB sockets, storage, literature and headset stowage sit on supported surfaces. Sliding-door rollers, rail, stops, brushes and pockets remain visible; the open stop leaves the manual pull exposed.

The cockpit retains round gauges, green radar, a supported status screen, bright red/green pushlights and the mechanical throttle gates. Separate switch stems, pushcaps, rotaries and four quadrant levers now have usable visual or pose states. These controls do not simulate aircraft flight systems. Two connected headsets sit beside the pilot chairs. Split overhead banks sit lower, the outer instrument wings are lowered, and the nose has actual re-cut glazing apertures for the seated forward horizon. The latest print pass fits complete glyph footprints onto their physical faces and attaches the green pushlight legend to its moving cap. The secondary radar now has its own clear mounting strip, and four wing instruments have fitted rear adapter collars. Source checks found no intersections among the 13 instrument bezels and supported every tested rear rim.

Both complete pilot chairs and their connected headset assemblies move 26cm aft, creating 52.4cm between the actual cushion fronts and the rear of the yokes. The controls keep their modeled positions. A standing approach passes through this space before entering each chair. Saved-source checks confirm the poses, collision bounds and action points align, and both moved eye positions retain horizon/upward glazing views. Two cabin-light controls now sit on supported aft console pods, away from the yokes; exposed grip points follow their controls.

## Luggage and equipment

Overhead luggage enclosures have upper hinges and lift-up lids, with modeled cases inside. The forward floor aperture is widened to 1.45m with 1.20m-wide stair treads. The lower floor spans33.35m inside the existing barrel, from cabinY1.30 to34.65m. Its aft extension adds12.85m. Secured racks along both sides contain cartons, timber crates, sewn duffels and latched equipment cases, with a clear central walkway. Its floor remains 2.05m below the main cabin.

The lower-deck stair is a gameplay design choice for this fictional aircraft. The standing camera follows the authored floor continuously with collision enabled. The forward hold liner now has a real returned notch below the first tread, with collision proxies matching that shape. The landing route turns through the centre aisle before passing the next rack. Current validation retests descent, the extended walkway and return ascent with body-clearance probes, plus two repeated stair-return cycles. The top portal restores normal standing height after a missed stair sample.

The longer exterior repositions the wings, powerplants, gear and tail coherently, extends the nose and afterbody, and adds lower body volume for the luggage deck. The revision15 exterior and its current limitations are documented in `Review_16.md`. Passenger doors retain their viewports, pressure seals, arming housings and slide bustles, and now release outward before swinging. An evacuation slide deployment is not simulated.

## Play and edit

Open `Run Plane.cmd` to walk inside. Use **W/A/S/D** and the mouse. Aim the centre crosshair at nearby equipment and press **E** or **left click**. Physical aircraft walls block interaction rays. Invisible standing-body proxies keep their movement barriers but do not hide the visible fittings. Doors, storage fronts, overhead lids, the luggage hatch, oven fronts, lavatory fittings and crew pans have authored movement or control states. Fold a crew pan down before sitting. Stow the crew pans beside the floor hatch before using the cargo stairs. Pilot, business, economy and crew seating positions are available. Standing eye height is 1.62m above the active floor; pilot seated eye height is 1.60m. Close the window or press **Alt+F4** to exit.

Look directly at a display and press **E** to cycle its pages, including while seated. Small controls have aim assistance around their visible cap or grip; E or left click cycles their visible state, lighting or pose. Press **Space** to stand up, or look away from usable equipment and press **E**. An empty left click keeps you seated. Reading lights, call indicators and gasper positions operate separately for each passenger unit. Inspect a safety card, crew guide or interphone with **E**; press **E** again to return it and restore the previous view.

Open `Review Exterior.cmd` to start at an exterior camera. **V** cycles exterior, front, side and walking views. These are fixed review cameras; flight simulation is not implemented.

Open `Edit Plane.cmd` for Blender. `Plane.blend` and `SourceAssets/Blender/SkywardAir.blend` are synchronized editable sources. Save edits, then use `Update Plane.cmd` to export the saved model and rebuild Unreal without regenerating its geometry. Deliberate revision13 regeneration uses `SourceAssets/Blender/rebuild_aircraft13.py` and its helpers, from the preserved final revision12 archive.

This is an **uncooked Unreal editor-hosted walkthrough**, requiring the included local UE5.8 installation. Its interactions run through the project startup Python module. It is not a packaged shipping executable.

## Review and verification

`Screenshots.html` puts saved game captures of the latest source first, separate from genuine construction views and earlier versions. Missing or planned screenshots are not displayed. Some construction views precede final mounting and trim corrections; current native captures establish the delivered appearance.

`Review_16.md` describes the current work and its limits. `ArtBible/Revision13Layout.json` records the authored layout; `ArtBible/SourceFit13.json` records independent saved-mesh checks; `ArtBible/FloorRegression13.json` records the floor-selection regressions; `ArtBible/EngineValidation.json` records the latest standalone test run; `ArtBible/UnrealBuildReport.json` records native import/map reload; `ArtBible/Delivery_Audit.json` records the delivery audit. Source, material, jamb and geometry checks also live in `ArtBible/`. Check each report's revision and source hash before treating a passing result as evidence for the current model. Earlier successful or interrupted runs are preserved in `Versions/`.

## Remaining gaps

Exterior surfacing, wing/body transitions, gear bays and passenger-door mechanisms still need visual work. Small text and fine seams can lose clarity at gameplay distance. Some detailed static meshes still need UV/tangent cleanup, production LODs, batching, collision optimization and measured performance profiling. The new suites have static recline, trays and entertainment artwork; their privacy doors work.

Cockpit and appliance controls drive modeled states, lighting or movement; they do not simulate avionics, heat, water or electrical systems. Passenger exit leaves have an outward-release/swing animation, without evacuation-slide deployment or pressure simulation. Curtains, recline, most trays and some ancillary seat/table fittings remain static. Coffee pouring, taps and ovens have authored visual states. The mounted extinguishers are scenery; fire suppression is not simulated. Display page navigation has no film/music playback, touch input or live aircraft telemetry. Charging ports are modeled fittings without device simulation. Luggage lids and the hold hatch open; bag pickup/packing is not implemented. Interphones can be lifted and returned, but phone/radio audio is not implemented.

Flight physics, turbulence, damage, serving tasks, hands/characters, multiplayer, audio and story are not implemented. The airport prototype is preserved and was not revised in this aircraft pass. Boarding a moving aircraft is not implemented. Native tests establish only the routes and interactions actually exercised; they do not establish final art quality or complete gameplay.

No paid generation or Higgsfield credits were used.

## References

The source visual bible and supplied screenshots are in `ArtBible/`. Qatar's [official Qsuite reference](https://www.qatarairways.com/en/onboard/qsuite.html) informed sliding privacy doors, personal storage, side consoles and ambient lighting; these are original fictional suites without Qatar branding. Boeing door dimensions informed earlier door proportions: [D6-58328 Rev K, Â§2.7](https://www.boeing.com/content/dam/boeing/v2/airports/acaps/767_REV_K.pdf). The included sky is CC0 from Poly Haven.
