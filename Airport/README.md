# Skyward International Airport

Run **Run Airport.cmd**. Start at the covered departures entrance, collect a boarding pass at a counter or kiosk, run bag drop if carrying luggage, cross a security portal, and board SA107 at Gate A07. Walk through the enclosed bridge into the aircraft with the separate revision 17 fittings. Boarding opens only after check-in and security.

**WASD** move; **mouse** look; **Shift** run. Aim with the crosshair and press **E** or click for the shown action. **E** picks up/drops luggage; **left click** throws held luggage. **Space** leaves a seat. **Tab** toggles free spectator movement; **Space/Ctrl** move vertically and **Shift** boosts. At the baggage tug, **E** enters/exits, **W/S** accelerates/reverses and **A/D** steers. Entrance doors open automatically. Gate leaves slide into visible pockets.

**Revision 11:** enclosed entrance, check-in and screening rooms; a separate concourse and gate lounges; lower ceilings and fitted floor runners; supported stairs in the side atrium. Aircraft seat-back screens, connector strips and literature pockets have retained supports. Thirty-six separate meal tables fold and lift on captive guides. Both pilot stations and yokes sit closer to the central controls.

**Fire extinguishers:** E picks one up; hold **left mouse** to spray; **E** drops it. Press **R** near its bracket to stow and refill it. The charge is finite. Economy tray tables work with **E** while seated or standing.

## Included environment

Six detailed check-in counters and six kiosks; four security lanes with open scanner tunnels and separate detector portals; actual conveyor surfaces, trays and varied physical suitcases; arrivals reclaim carousel and trolleys; three furnished gate areas and original flight information displays; aircraft boarding bridge; mezzanine lounge and returning stairs; cafe with separate espresso, bakery, checkout and hot-drink stations; travel retail, vending, charging tables, telephone, planted seating islands and furnished restrooms. Outside: covered forecourt, drop-off road, crossing, taxis and shuttle buses, curbs and street lights, graded grounds, supported terminal foundations, apron, service ramp, tug with two native articulated dollies, mobile stairs, ground-power cart, hangar, control tower, windsock, taxiway and a 1,500 m runway with threshold numbers, edge/hold markings and lamps.

The full uploaded README was read and preserved in ArtBible/Original_Readme.md. ArtBible/Research.md distinguishes details observed in official Dear Passengers media from original Skyward extensions. Reference images are research-only. Screenshots/ contains genuine Unreal frames, and Screenshots.html presents the final views and development history.

## Editable files

- **Airport.blend**: original editable source models, lofts, profiles, modifiers, materials, assembly and review cameras. **Edit Blender.cmd** opens it.
- **../SkywardAir/UnrealProject/SkywardAir.uproject**, map **/Game/Airport10/L_Airport_Revision11**. **Edit Airport.cmd** opens the native level.
- **Rebuild Airport.cmd** regenerates the current airport model exports and separate revision 11 level using the preserved Pass09 seed. This rebuilds generated airport content; keep manual variations in a separately named level.
- **SourceAssets/**: deterministic Blender modeling/layout/export scripts, original UI/audio generator and Unreal authoring script.
- **../SkywardAir/Revision17/Plane_Refined17.blend**: separate editable aircraft fittings source. Original Plane.blend is retained. **Revision17/Exports/** contains the matching FBX and scene manifest. **SourceAssets/Blender/refine_fittings17.py** regenerates it from the original source; save manual variants separately before regenerating.
- **Exports/**: FBX asset families, material manifest and complete placement/interaction/floor manifest.
- **../SkywardAir/UnrealProject/Content/Python/airport_runtime.py**: airport-only extension to the existing aircraft walkthrough. The separate aircraft revision 17 data is loaded in memory for this airport mode.
- **Test Airport.cmd** repeats the native route/physics acceptance run. **Capture Airport.cmd** repeats the final native screenshot sequence. Results appear in ArtBible/Revision11_QA.json and Revision11_Captures.json.

The prior ten cumulative native maps, Screenshots10.html, Review10.md and their build/capture reports are retained. The current revision uses its own map and evidence. Final corrections were made during the tenth scrutiny pass. Earlier dark/checkerboard captures are preserved as development evidence, not final-quality images. RecoveryMaps contains generated-level recovery copies. Original plane sources, maps and current crash launchers are separate.

## Physics and practical limits

Luggage, cups, security trays, tug, dolly loads and removable extinguishers use native rigid bodies. Pickup is a force-driven spring; throwing applies an impulse. Conveyors apply forces only while a body is supported on a conveyor. Ten authored convex hulls per suitcase follow its shell, wheels, handle posts, grip and tag. Two native articulated constraints connect the tow train. The tug uses a single-body force/torque vehicle approximation with a low-friction ground material; it does not simulate independent wheel suspension. Sliding doors are kinematic mechanisms. Restroom pocket doors have modeled release plates on both sides and occupancy lamps.

This is an editable single-player Unreal preview requiring the installed engine. It is not a packaged standalone executable. It includes no new passengers/NPCs, multiplayer backend or airport taxi/flight/takeoff integration; the existing separate aircraft crash preview is preserved. Walking uses the established pawn, collision and authored continuous floor system. The native acceptance report records tested routes and actual measured frame times; it is not a claim about every possible machine or viewpoint.
