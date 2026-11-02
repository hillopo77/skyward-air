# Flight39 integration and evidence

Read the complete uploaded `read me`. This deliverable uses the current modeled aircraft, original branding, warm readable game style and native gameplay. It does not alter tower/crash modes.

## Source order

1. After final38/39 scene/source contacts: `airfield39.plan(ctx)`, `airfield39.build(ctx)`.
2. `flight39_surfaces.build(ctx)` creates copied fixed airframe/dashboard plus13 real surfaces and7 gauge needles. Then `flight39_gear.build(ctx)` extracts seven moving corrected-gear/door assemblies and retained fixed upper mounts. These27 actors are **individual movable actors**, never an ISM. Fixed meshes keep the preserved inherited library independent.
3. Root `nose39.refine(ctx)` operates on the copied `SM_AP_F39AirframeFixed` only.
4. Final source character/contact fixes may follow. Export fresh asset paths and final D.flight39 metadata.

Root's targeted importer must remove D.flight39.retired_instances and rebuild affected grouped asset families, including old Airfield34/Asphalt/Marking instances. Do not stack the new runway over old coplanar surfaces.

## Native and runtime order

1. Import and place new source assets. Cache ctx.mesh against their actual destination paths. Place all D.flight39.moving_names individually.
2. `native_flight39.apply_native(ctx)` replaces the two original tagged plane mesh actors, creates one carrier, printed live cockpit readout, attached chase camera and budgeted exterior practicals. It gives the actual visible pavement its collision top. Then `native_flight39.import_audio(ctx)` imports original local PCM sounds. Root's final material/glass authority applies after mesh replacement.
3. Before plane.configure: plane18.install; airside38.prepare_plane(P,D); **airport_flight39.prepare_plane(P,D)**; append airport floors; configure as before.
4. After ext11/characters12/clarity26/airside38/journey38 install: **airport_flight39.install(G)**; final rendering authority last. Existing tower/legacy launch paths never call this module.
5. Core held spring exact change in airport_runtime.physics: replace `-c.get_physics_linear_velocity()*9` with `-(c.get_physics_linear_velocity()-S.get('carrier_velocity39',u.Vector()))*9`. Off-plane carrier_velocity39 is zero. This prevents the spring braking against the whole aircraft velocity.

The single carrier moves rigid aircraft rooms, fittings, collision proxies, lights, aboard character placements and their CH12COLL proxies.27 actuators update at10Hz; the carrier and bounded loose-prop correction skip unchanged parked frames. The frozen manifest reference is preserved; moving doors, sliders, shades, target selection, seats, floors and printed instruments follow that frame. Native loose cabin props form a small bounded separate set; relative velocity is retained rather than writing1300 actors every frame.

## Native QA

`qa_flight39.specification(P,D)` gives the continuation from the existing successful fresh airport journey. Walk back through the **right galley route**, open the flightdeck door, walk the real footwell and sit `SM_Plane_Seat.016` through physical nearest/use. `qa_flight39.native_negative(G)` checks cold engine start, stand takeoff thrust, ground gear retraction and unpowered radio.

`qa_flight39.start_driver(G,capture)` then operates the **same actual mapped control API** used by modeled cockpit fittings and keyboard shortcuts. It requests crew door closure and actual bridge retraction; waits for real states; asks native airside.can_depart; spools both engines; taxis the full route; stops at Alpha1; requests clearance; lines up; accelerates; rotates; climbs; retracts the actual seven gear/door assemblies; demonstrates right and left banking and pitch/yaw inputs. No aircraft position/speed injection, bridge fraction injection or journey flag grants exist in this driver.

Driver capture callback receives stage labels. End with `qa_flight39.verify(G)`. Native results go to ArtBible/FlightQA39.json; live state goes to FlightSession39.json. Record a separate uncaptured manual60second run for performance approval; capture pauses are not steady-state FPS.

## Manual procedure

Home crew closes four aircraft doors + lower hatch; End stows empty bridge. M master, N avionics, U fuel, J pumps, K start air, L beacon;1 and2 engine START, wait for both to reach idle. C taxi clearance, P parking brake release. PageUp selects taxi thrust; A/D steer and Ctrl brakes. Follow the yellow Alpha line, stop at Alpha1 and press C. Follow the broad turn onto runway36, align, F takeoff flaps5, ensure X speedbrake retracted; PageUp takeoff thrust. At140kt hold W to rotate. W/S pitch, A/D bank, arrow keys yaw; G gear, F flaps. V cockpit/exterior; Tab free camera with Shift fast. Space stands when parked/taxiing or airborne; finish the takeoff roll first. In-flight walking neutralizes held controls and the game model holds its current trim.

Realism scope: documented local game flight approximation, stable rigid carrier, supported full-scale pavement and normal control procedure. This is not certified767 aerodynamics, an engineering simulator or a multiplayer moving-platform implementation. The runway is2600×45m with7.5m shoulders and23m taxiway. Boeing airport planning supports the width/turn scale;2600m is this tested game level's length.

## Verification completed before native assembly

Nine bounded source/control suites pass, including five procedure passes and54 arbitrary orientation/reference round trips.44 actual control IDs, five external door IDs and both pilot-seat IDs match the current Revision18 manifest. Complete integrated driver reaches flight in199.55simulatedseconds, max taxi deviation0.416m. These tests are explicitly **not native visual, collision or performance proof**. Independent evaluated Blender geometry audit passes all33 asset families with zero degenerate triangles and no nonfinite vertices, recorded in SourceGeometryPass39.json. Native visual/collision/performance approval remains with the root runner. Actual native runs exposed missing root-component/2D-audio aliases and the closed flightdeck door despite a completed scalar. Code now uses the native aliases and explicit identity quaternions; door_open_actual checks the real actor pose. A subsequent native door crossing and complete flight remain required before approval.
