# Equipment and props critical review

The equipment is not consistently assembled. Several recent visual upgrades sit on older malformed assemblies; route waypoint tests did not inspect those connections.

The issue is construction consistency, not simply an insufficient count of tiny decorative parts. A functioning boarding trigger does not validate that the desk is fitted, that a conveyor goes somewhere, or that a monitor is supported.

## EQ01 [P1] Checked baggage belts terminate in a solid decorative wall and have no onward system

Status: verified. Objects: Bag drop belt 01, Bag drop belt 02, SM_AP_CheckinRoom33.

- Native03_BagDrop01 visibly ends against the timber/solid service wall. Belts point+X, occupy x[-29.7,-26.1] at y-12/-16; check-in east boundary is x-26 and its service lining is near x-26.13/-26.31.
- Exports has only two finite bag-drop rectangles and no backstage continuation. airport_journey22.py:70–78 accepts the bag while supported anywhere on the entry belt; no end-of-belt removal/transfer occurs there.

Correction: Create proper guarded baggage hatches through ALL overlapping wall/lining layers and a visible short continuation into a supported backstage baggage area. Transfer/sleep bags only after they physically disappear through the guarded hatch. Add guidance distinguishing optional bag drop from security screening.

Acceptance:

- A physical suitcase travels from load point through a real opening without hitting or clipping wall, falling at the end or remaining against it.
- The outward transfer is observed over time, not inferred from the accepted flag.
- Both belts have consistent arrow direction and accessible stop controls.

## EQ02 [P1] The emergency stop is embedded in the scanner shoulder

Status: verified. Objects: SM_AP_Belt, SM_AP_Scanner34, Security belt 01, Security belt 02.

- Source inventory cap local bounds x[.583,.677],y[-.997,-.903],z[.935,1.005]; scanner shoulder extends x[.645,.795] through the same y/z region.
- 08_ScannerControl shows only a thin yellow fragment behind the body; the red mushroom is obscured.

Correction: Move the stop box to an accessible outboard/entry bracket clear of the scanner envelope, with a retained mounting foot and readable emergency-stop identification. Keep the cap circular and above its bezel.

Acceptance:

- The entire cap and guard are visible from the passenger/operator approach.
- There is no triangle-volume intersection with scanner body.
- The interaction ray reaches the cap/bracket rather than the equipment wall.

## EQ03 [P1] Right lane side monitor/shelf penetrates the security east partition

Status: verified. Objects: X-ray scanner 02.

- Native machine bounds maxX-35.845; the room east wall is x-36 with interior face near-36.09.
- Its side console protrudes about245mm past the interior face at y~2.3, where the wall is solid.

Correction: Reposition the entire second screening assembly within the room envelope, including detector, belt, scanner, tray station and targets; do not move only the protruding screen. Preserve both lane clearances and the exit route.

Acceptance:

- All equipment bounds and controls are inside the room with a deliberate service clearance.
- Both detectors are walkable and remain aligned with their floor guidance.
- Monitor and control interaction rays are unobstructed.

## EQ04 [P1] Scanner monitor contains a floating weighted foot and conflicting supports

Status: verified. Objects: SM_AP_Scanner34.

- Old monitor weighted foot bottom is z1.164, while the side work shelf top is1.075: an89mm air gap.
- The original articulated support and swivel stem are retained as well. 08_ScannerControl visibly shows a small base hovering above a large shelf.
- Terminal34 clones Scanner without excluding original monitor housing/stand; a new readout housing is added over the original enclosure.

Correction: Use one coherent support scheme. Prefer a wall/VESA arm with bolted mounting and remove the redundant weighted foot; alternatively seat the foot on the worktop and correctly shorten the stem. Replace overlapping old/new monitor enclosures with one fitted enclosure.

Acceptance:

- Every monitor support member has a continuous mechanical connection to the scanner or shelf.
- No horizontal foot floats in air.
- Close front/side/rear views show one enclosure and no duplicate protruding backing.

## EQ05 [P1] A07 desk intersects its room wall

Status: verified. Objects: Gate A07 boarding desk.

- Native bounds minY-3.055; south room wall is centred y-3 with inside face approximately-2.91.
- The desk therefore penetrates the room boundary by~145mm. 27_DeskClearance shows the desk/foot rail crowded against the corner.

Correction: Move the complete boarding workstation and its NPC, interaction point, screen/reader and collision proxies north into a planned service bay; preserve a usable staff clearance. Audit A08 and operations workstation similarly rather than applying the move blindly.

Acceptance:

- No desk geometry or support penetrates a wall or adjacent desk.
- The staff working area and public scanner approach are both accessible.
- The boarding action remains reachable from the public side.

## EQ06 [P1] A standalone potted plant was left floating when furniture moved

Status: verified. Objects: Small potted plant24.

- Native plant base is at[-35.25,.25,1.06], boundsY[.1576,.3424].
- The repacking bench now starts at y.533 and the charging table moved to x-32.75. Neither is beneath this plant.

Correction: Attach the plant to the new charging surface with its base seated at the actual top height, or relocate it to a real supported ledge. Group props with their supporting furniture so later moves carry them together.

Acceptance:

- Downward support trace from the planter bottom hits its intended furniture within a few millimetres.
- The prop does not float or intersect another fixture from any nearby viewpoint.

## EQ07 [P1] Service-desk carcass and curved front panels are not constructed as a fitted assembly

Status: verified. Objects: SM_AP_ServiceDesk30, SM_AP_Counter34.

- The closed carcass has a front face while separate curved doors cross that envelope. The upper outer portions of the door curve reach approximately y-.45 at z.91, behind the carcass front near-.455.
- 27_DeskClearance shows open dark side voids/strips around the door/end-cheek assembly. The same modeled source is reused at check-in, both gates and operations.
- There is no evidence here that the TWO CHECK-IN DESKS mutually intersect: their centres are4m apart and their2.11m widths do not overlap. The verified defects are desk-wall and within-model assembly intersections.

Correction: Model an open-front carcass/frame with real backing and shelves, inset doors with consistent reveals, properly joined end cheeks and seated trim. Remove unseen faces behind inset panels instead of layering closed solids. Keep a continuous attached front badge rather than a plaque spanning two functional doors.

Acceptance:

- No front panel crosses the carcass surface in section.
- Door reveals are narrow, consistent and backed; no bright/world-visible voids at the ends.
- All instances render cleanly at close range while moving.

## EQ08 [P2] Curtain gaps create an unnecessarily high-contrast high-frequency pattern

Status: verified_geometry; shimmering_cause_is_suspected. Objects: SM_AP_Scanner34.

- There are12 strips across each tunnel end, width.106m on.112m pitch:6mm bright open gaps.
- All curtain parts are static/non-simulating and have zero within-part duplicate faces in the source inventory. That does not prove that no inter-asset overlap exists.
- The user image and07_Curtain show the repeated bright lines between very dark strips.

Correction: Use a continuous dark interior liner and softly shaped strips/grooves, or realistically stagger the overlaps in depth. Do not widen coplanar front strips into one another, which would create z-fighting. Soften the visible manufactured edges and keep cavity darkness stable.

Acceptance:

- Fixed-camera and moving-camera frame sequences have stable curtain silhouettes and no bright intermittent slit pattern.
- Transform samples remain invariant while stationary.
- No overlapping coplanar faces are introduced.

## EQ09 [P2] Stock shelves are populated with identical blank cartons rather than recognizable supplies

Status: verified. Objects: SM_AP_Storage34, RetailShelf24_1814, RetailShelf24_1815, RetailShelf24_1832, RetailShelf24_1833, RetailShelf24_1834.

- Source inventory:20 identical.18×.17×.30m cartons plus20 plain white rectangular label solids per shelf.
- 11_StaffStorage confirms the repeated five colours and blank labels.

Correction: Create a small coherent supply set with recognizable silhouettes and readable role labels: folded blankets, first-aid packs, radio/headset cases, document binders and boxed service supplies. Vary arrangement according to staff storage versus gallery retail; retain a consistent smooth stylized finish.

Acceptance:

- At normal player distance each product family is identifiable without zoom.
- There are meaningful shape/material differences and labels, not only recolours.
- Every item rests on a shelf with no wall intersection.

## EQ10 [P2] Shelf price rails float in front of the shelves

Status: verified. Objects: SM_AP_Storage34.

- Shelf front y-.245; rail back y-.258, leaving13mm unsupported air.
- Four rails are simple6-face boxes with no clips/attachment geometry.

Correction: Seat the rails directly on the shelf edge or add actual retained clips. If used in staff storage, replace retail price rails with appropriate inventory tags.

Acceptance:

- The rail back contacts its support continuously or at modeled clips.
- Close oblique views show no floating horizontal strip.

## EQ11 [P2] Legacy recycling units have painted-on recesses instead of apertures

Status: verified. Objects: SM_AP_Recycling, Recycling24_1810, Recycling24_1830, Recycling24_1831.

- The source consists of a closed housing, door and dark solid rectangles named Open dark recess; there is no cut-out or open liner.
- Newer café Bins36 already use genuine openings, so the map contains inconsistent prop construction standards.

Correction: Replace the legacy units with a compact genuinely open version, including a liner, thickness and either a swing flap or an actual mouth. Keep a clear label appropriate to location.

Acceptance:

- A view into the aperture shows a supported dark cavity rather than the outside floor or a flat solid decal.
- No open shell backfaces or floating trim are visible.

## EQ12 [P2] Screening tray stacks remain on the floor rather than the preparation worktop

Status: verified. Objects: Tray24_1719, Tray24_1720, Tray24_1721, Tray24_1722, Tray24_1732, Tray24_1733, Tray24_1734, Tray24_1735.

- Both stacks are at scannerX,y.8, baseZ0,.12,.24,.36, whereas the supported preparation worktop is aroundz.94.
- They are nonblocking decorative instances, with no coherent tray-use journey.

Correction: Put the stack on a fitted waist-height input cart or the preparation bench and make the equipment layout communicate prepare→load→walk→collect. Add a receiving shelf at the output or bounded return arrangement.

Acceptance:

- All trays rest on a support, with a deliberate reachable input/collection position.
- The route cannot be mistaken for putting belongings on the floor.
- If trays are interactive, they can be picked up and placed without slipping through the surface.

## EQ13 [P1] The fitted café run has100mm open voids between cabinet bases

Status: verified. Objects: SM_AP_Espresso36, SM_AP_Bakery36, SM_AP_POS36, SM_AP_Tea36.

- Each base/plinth is1.90m wide while counters are placed2.0m apart; worktops are2.0m wide.
- 24_CafeService visibly exposes100mm vertical gaps between base units below the almost-continuous worktop. The units have separate backs, so the service void is not closed by a continuous rear panel.

Correction: Model scribed filler panels/pilasters and continuous plinth/backing at the three joints, or author the run as one fitted cabinet frame with separate functional doors. Retain honest narrow worktop joints.

Acceptance:

- Front and oblique views show a continuous backed run with no view through100mm gaps.
- Doors, pulls and plaques do not intersect the fillers.
- All four equipment stations remain accessible.

## Limits and corrections to broad claims

- No proof that the scanner itself physically moves; native scanner is static. Motion/temporal causes require frame/transform analysis.
- No proof of mutually overlapping check-in desks in current placements.
- AP COLL proxy component visible flags do not establish that actors render: actor hidden-in-game must also be checked.

No engine/source/runtime edits were made. Only this report and local analysis helpers were written.
