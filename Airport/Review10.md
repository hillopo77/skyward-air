# Ten development passes

Each pass has a saved native level, a build manifest and fingerprinted genuine Unreal captures. Pass ten includes the visual and collision corrections found in the full review.

01. Passenger circulation and connected boarding footprint — 4 native captures; 10 placed instances.
02. Modeled architecture, glazed elevations and mezzanine — 4 native captures; 7551 placed instances.
03. Check-in, bag drop and arrivals reclaim — 5 native captures; 7575 placed instances.
04. Security lanes, trays, operator equipment and barriers — 4 native captures; 7702 placed instances.
05. Passenger amenities, lounge, cafe and furnished gates — 6 native captures; 7810 placed instances.
06. Landside, apron, runway and ground service — 6 native captures; 8321 placed instances.
07. Physical luggage, pickups and mechanical interactions — 5 native captures; 8366 placed instances.
08. Original signs, information systems and boarding sequence — 5 native captures; 8379 placed instances.
09. Materials, illumination and performance review — 5 native captures; 8379 placed instances.
10. Scrutiny, route verification and final corrections — 16 native captures; 8706 placed instances.

## Native acceptance

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

A separate rendered 1280 × 800 idle sample measured 59.9 FPS average, 17.6 ms p95 and 20.8 ms maximum over 360 frames. Screenshot stalls are excluded from this separate sample; route movement statistics remain in AirportSession.json.

No claim of perfection: the airport remains a single-player engine preview, with a force/torque tug approximation, authored walking floors, no new NPCs and no airport flight integration.
