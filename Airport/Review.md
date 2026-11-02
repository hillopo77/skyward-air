# Airport revision 11 and aircraft fittings 17

The previous open hall is divided into an entrance vestibule, check-in and screening rooms, a defined concourse, separate gate lounges, cafe/shop fronts and waiting rooms. Lower acoustic ceilings, fitted runners, visible portal headers and seating banks give each area a clear boundary. The stair now sits in the side atrium with a continuous structural body, stringers, supported landings and a clear route to the mezzanine.

The aircraft uses continuous seat-back carriers with retained screens, side-mounted USB/headphone hardware and literature pockets. Thirty-six separate tables fold and lift on captive guides. Both pilot stations and their associated yokes/hardware are closer to the central console; tested horizontal throttle reach is 0.58 m. Original Plane.blend and legacy crash assets remain separate.

Seven removable extinguishers have modeled pressure vessels, valves, handles, pin rings, gauges, retained hoses and native contact hulls. Hold left mouse to discharge a finite charge, E to drop, and R near its bracket to stow/refill. The smoke-like powder is a lightweight game visual effect; this does not add calibrated fire suppression.

## Evidence

29 of 29 native checks pass; 25 current unaltered 1600 × 1000 screenshots are fingerprinted in ArtBible/Revision11_Delivery.json. The walking test drives the actual pawn continuously through the entrance, check-in, security, gate and bridge, and separately traverses the relocated stairs and service ramp. Mechanism checks exercise native pickup/throw/conveyor/tow bodies, doors, folding trays, pilot reach and extinguisher pickup/discharge/stow.

The separate rendered idle sample at 1280 × 800 measured 45.4 FPS average, 29.8 ms p95 and 31.1 ms maximum across 273 frames. This is one idle viewpoint, not a whole-airport performance guarantee.

- All authored native physics bodies initialized — PASS
- Two native articulated tow couplings — PASS
- checkin action has line of sight — PASS
- boarding action has line of sight — PASS
- Continuous entrance to aircraft walk — PASS
- Security cleared by crossing portal — PASS
- Boarding gate opened after clearance — PASS
- Aircraft boarding event detected — PASS
- Sliding leaves occupy their modeled pockets — PASS
- Cubicle outside release visible — PASS
- Cubicle slides into modeled pocket — PASS
- Cubicle inside release remains accessible — PASS
- Cubicle closes from inside pocket enclosure — PASS
- Opaque wall blocks interaction — PASS
- Stairs and upper landing reach mezzanine — PASS
- Service ramp reaches apron continuously — PASS
- Suitcase settles on actual terminal floor — PASS
- Spring-force luggage pickup — PASS
- Luggage throw uses physical impulse — PASS
- Scanner conveyor moves supported physical luggage — PASS
- Powered tug pulls constrained baggage dollies — PASS
- Rendered idle performance sample — PASS
- Meal tray opens flat and lifts in captive guides — PASS
- Meal tray returns to fitted seat-back recess — PASS
- Pilot throttle is within seated horizontal reach — PASS
- Extinguisher has an unobstructed pickup target — PASS
- Extinguisher detaches as a physical held object — PASS
- Powder discharge consumes charge and renders a jet — PASS
- Extinguisher returns to its physical bracket — PASS

## Practical limits and remaining gaps

This is an editable single-player Unreal preview requiring the installed engine, not a packaged executable. There are no new passengers, multiplayer services, airport taxi/takeoff integration or general-purpose fire/fluid solver. The tug remains a single-body force/torque approximation. Walking retains the established authored floor system.

Some retail and service props remain scenic or inspection interactions; this pass does not make every airport prop usable. The unclear voice reference to an object merged with a door/pillow could not be identified specifically. The actual seat-back display, tray, pocket and connector assemblies were rebuilt and photographed.

The ten preceding maps and their gallery remain available in Screenshots10.html and Review10.md. Current map: /Game/Airport10/L_Airport_Revision11. Current aircraft source: ../SkywardAir/Revision17/Plane_Refined17.blend. The original accepted aircraft source is unchanged.
