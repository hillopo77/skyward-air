# Critical review 1 — architecture, boundaries and wayfinding

The boundary and wayfinding failures are construction defects, not merely a lack of decorative detail. The exact A08 flicker cause is a retained roof cap sharing the ceiling plane; two exterior seams are physically unblocked; two identification systems are incorrectly placed or oriented.

## L01 [P1] A08 and cafe approach ceilings are coplanar with retained roof caps

Status: verified.

- SourceInventory38: SM_AP_Room37_gate08foyer Fitted acoustic room ceiling35.020 has bottom z3.4, XY[-31.99,-24.01]x[14.01,17.99].
- SourceInventory38: SM_AP_Roof35 Weather-sealed roof cap35.003 has bottom z3.4, XY[-32.075001,-23.924999]x[13.925,18.075001].
- The same exact coincidence exists for cafefoyer: Room37 ceiling bottom3.4, Roof35 cap35.002 bottom3.4.
- AuditInventory38: Crafted Roof35 is visible=true, hidden=false. model37 repositions ceilings from3.3 to3.4 but retains Roof35 built from height3.3.

Correction: Give room ceilings and weather roof caps one coherent owner. Rebuild cap heights from current zone heights with positive vertical separation; remove obsolete hidden underside faces where redundant. Do not add another ceiling cover on top.

Acceptance: Static-camera hold and walking capture through both approaches show no alternating ceiling pixels/edges; assert no coincident upward/downward planar face pair across visible ceiling footprint.

## L02 [P1] Amenities have a real east-envelope opening into the exterior

Status: verified.

- model37 skips all east-boundary x=-14 segments with y-high<=10, then only restores gate07 y=-3..10.
- Last legacy east facade centre y=-6.25, length3.5: it ends at y=-4.5. Restored east gate wall starts y=-3.0, leaving1.5m unsealed.
- BaselineCapture38 trace WC east breach returns blocking=false, mesh=null.

Correction: Build a continuous exterior envelope covering amenities and arrivals from current zone bounds and subtract only named doors/windows with deliberate collision. Seal the1.5m northeast amenities gap with a full-height constructed wall.

Acceptance: Ray and swept player capsule at (-15,-3.8,1.0) toward(-12,-3.8,1.0) are blocked; walk-test the whole WC perimeter and all adjacent envelope seams.

## L03 [P1] Security entry has an unsealed west facade-to-wall seam

Status: verified.

- Legacy west facade centre y=-6.25 spans -8..-4.5, while the security west wall begins at y=-4.
- model37 deliberately skips west-boundary segments with y-high<=-4 and relies on those remnants.
- BaselineCapture38 trace Security west breach returns blocking=false, mesh=null; 06_WestEntryGap shows the disconnected end condition.

Correction: Join the landside/security envelope as one continuous wall/glazing system; provide a proper jamb/cap at the glazing end and continuous collision.

Acceptance: Perimeter rays at several heights and capsule sweeps across x=-49,y=-4.5..-4 are blocked; there is no visual crack or walkable slot.

## L04 [P1] STAFF ONLY board is hung across the usable door aperture

Status: verified.

- Native Staff service leaf24 occupies x[-46.5,-45.5],y[9.852128,10.06],z[0,2.7].
- Native Sign24_1816 occupies x[-46.874,-45.126],y[9.751,9.949],z[2.0225,2.4775]. It crosses the opening rather than mounting above or beside it.
- BaselineScreenshots/10_StaffDoor.png clearly shows the wide sign spanning the doorway below its header.

Correction: Place a smaller staff plaque on the solid wall beside the door or above the clear header, with physical mounting. Keep the full doorway clear.

Acceptance: Door opening and sign bounds do not overlap at any door state. Standing/seated-eye photographs show an intentional attached plaque and unobstructed head clearance.

## L05 [P1] WC identification floats inside the opening and faces away from approaching players

Status: verified.

- Identity37 WC backing bounds x[-26.24,-26.120001],y[-3.325,-2.675],z[1.525,2.375]. The concourse->amenitylobby portal is centred(-26,-3), width1.8.
- WC and TOILETS fonts are at x=-26.105, rotation(pi/2,0,+pi/2), normal+X. Players approach from concourse x<-26, requiring normal-X. Text is behind the backing from that side.
- BaselineScreenshots/18_WCSign.png shows the plain blue back of a visibly unsupported board in the doorway.

Correction: Mount the sign to an actual solid wall beside the opening or make an attached, two-sided blade. Orient readable faces to the approach, place fonts on the correct outward face, and add a clear toilet pictogram.

Acceptance: From (-28.2,-2.2,1.62), identification is readable, properly backed and outside the opening. No part floats or obstructs the passage; verify both approach directions.

## L06 [P1] The A08 marker is hidden behind its own entrance landscaping

Status: verified.

- Marker centre(-31.1,17.8,2.04), front text plane y17.748. Plant1224_1773 at(-30.6,16.5,0) has native canopy bounds x[-31.027306,-30.182853],y[16.05311,16.857301],z[0,2.376484].
- BaselineScreenshots/14_A08Marker.png shows the plant obscuring the marker almost completely. The normal south approach crosses that canopy silhouette.

Correction: Move the identification above or clearly beside the opening at an approach-readable height and move both planters away from the sign/door sightlines.

Acceptance: From the concourse approach, both standing and moving views show the complete A08 identifier without foliage overlap; include a visibility trace to its sign face.

## L07 [P2] A08 threshold is a leftover pocket rather than a coherent entrance

Status: verified design problem.

- Concourse rect[-32,-26,-4,14] expands abruptly into gate08foyer rect[-32,-24,14,18]; the extra eastern2m strip becomes a blind side pocket instead of a useful destination.
- South portal centrex=-29,width4.4 (x[-31.2,-26.8]); north portal centrex=-28,width4.6 (x[-30.3,-25.7]). Two shifted openings and two planters frame a4m-deep intermediate box.
- Plant1224_1771 canopy reaches x=-23.982853 while the west face of the east wall is approximatelyx=-24.09, so foliage penetrates the wall by roughly0.11m.
- The decorative sage post/frame sits immediately in front of the structural jamb/header, adding a second competing entrance outline.

Correction: Redesign the A08 threshold as one purposeful pause/turn with a clearly dimensioned clear route and one integrated entrance construction. Reconcile the2m return with the main concourse rather than using an arbitrary dead pocket. Move planters inside safe perimeter positions.

Acceptance: A floor-plan overlay shows no unexplained dead cubby; no planter intersects wall bounds; the entrance has one deliberate jamb/header system and a visible A08 identity from the decision point.

## L08 [P2] The narrow stacked directory is a weak primary wayfinding device

Status: verified design problem.

- Identity37 directory body is only0.46m wide at(-31.25,9.8); individual labels use0.072m font size and cap-height about0.05m.
- It faces south while the key recovery approach moves east, so it is small and oblique from the main decision view.
- The literal >,<,^,v text provides weak directional hierarchy; the user explicitly rejected it. It competes with floor stripes and separate entrance identifiers instead of giving one clear decision.

Correction: Replace the free-standing stack with a properly mounted directory at the decision point, using larger primary destination names, recognizable pictograms and consistent arrows. Keep each entrance individually identifiable rather than restoring a row of identical banners.

Acceptance: At each decision viewpoint, the player can identify the gate/cafe/toilets without approaching to read tiny labels; arrows correspond to actual branch geometry, and no plant/prop occludes the primary information.

## L09 [P2] Long generic circulation spaces still read as repeated empty boxes

Status: verified design problem.

- The main concourse is6m x18m, recovery4m x10m, and both gate foyer/cafe foyer boxes use nearly identical cream/navy wall treatments with simple cut-out openings.
- Baseline 12_Repacking,13_Concourse and Clarity37 01_ExitSightline show extensive blank planes and repeated rectangular framing. Removing glass reduced layers but did not resolve spatial hierarchy.
- The A08 side pocket and the existing A07 dogleg are assembled from independent room rectangles rather than one coordinated circulation plan.

Correction: Resolve circulation as a connected architectural plan with purposeful transitions, wall returns, coherent ceiling ownership and a few readable landmarks. Do not fill empty floor with more random objects. Preserve usable room clearances.

Acceptance: A new walk-through shows clear choices and distinct destination thresholds without arbitrary unused pockets, repeated mini-rooms or walls that exist only to patch another rectangle.

## L10 [P1] Previous passing checks did not audit the whole map or its construction

Status: verified.

- Clarity37 QA starts after check-in with one setup teleport, walks a selected waypoint route, tests seating/boarding and only two sightline traces.
- It does not test every perimeter, door/sign bounds, the actual outward WC boundary, the security facade seam or multi-frame ceiling stability.
- The current baseline has both live perimeter traces false despite the earlier93 checks passing.

Correction: Add a defect-driven acceptance matrix and boundary sweeps for every zone and doorway, plus moving-camera evidence. Keep route success separate from visual/construction sign-off.

Acceptance: Every finding has a named before/after proof. Whole-map sign-off requires all envelope seams, door clearances, object attachments and moving-image stability checks, not a higher count of waypoint assertions.

## Whole-zone coverage

- **entrancefoyer**: Source/native inventory reviewed; preserve approved layout. West envelope seam at its downstream connection requires closure (L03).
- **checkin**: Boundary/portal plan reviewed; approved room layout retained. Equipment and baggage handling defects are referred to equipment reviewer rather than inferred here.
- **publicreturn**: Rectangular boundary/portal continuity reviewed. Existing southern facade/ceiling system is retained; wider envelope acceptance must include this route (L10).
- **landsidecorridor**: Source/native reviewed; old west glazing ends short of security wall (L03).
- **security**: Entry boundary omission and staff doorway sign obstruction verified (L03,L04).
- **recovery**: Generic transition/wayfinding hierarchy remains weak (L08,L09).
- **concourse**: Directory and WC identification defects verified (L05,L08); spatial hierarchy remains weak (L09).
- **gate07foyer**: Final ceiling footprint matches current zone; avoid diagnosing it as the remaining A08 flicker. A07 entrance remains a dogleg with explicit direction sign (L09).
- **gate07**: Room enclosure footprint reviewed; desks/bridge handled by other reviewers. Clear opening is3m.
- **gate08foyer**: Exact roof/ceiling coincidence, hidden marker and dead-pocket design verified (L01,L06,L07).
- **gate08**: Room footprint matches current zone; passage sign/threshold failures are at its approach, not the back lounge ceiling (L01,L06,L07).
- **cafefoyer**: Second exact roof/ceiling coincidence (L01).
- **cafe**: Existing room bounds and gallery access retained; visual equipment audit delegated. No broad current room-footprint mismatch found.
- **amenitylobby**: Floating/back-facing WC identifier at its entrance (L05).
- **amenities**: East envelope breach verified by source and live trace (L02).
- **arrivals**: East boundary relies on legacy facade modules; covered current modules aty-22..-12, but include in continuous-envelope repair/validation (L02,L10).
- **operations**: Access sign crosses the door opening (L04); storage detail handled by equipment reviewer.
