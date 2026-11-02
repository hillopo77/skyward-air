# Frozen secondary contact patch

Call `refine_contacts39.apply(ctx)` on the existing saved38 source. It registers exactly **11** targeted export families in `ctx.a.ASSETS`, updates source instances/data, and returns an audit report. It does not open or save a shared master itself.

Changed families:

- `SM_AP_P38B_A00`, `A01`, `A02`, `A03`.
- `SM_AP_P38B_B00`, `B01`, `B02`, `B03`, `B04`.
- `SM_AP_P38B_docking_cab`.
- `SM_AP_P38B_GearContact39` (new local copy of the preserved modeled gear).

Native import: keep source materials on all imported families. The copied gear deliberately retains its original seven `MI_Plane_*` materials, which the native material cache already resolves from the preserved map. After import and exact placement, call **`refine_contacts39.apply_gear_native(ctx)`**. The existing `airside38.apply_native(ctx)` also calls that hook automatically when `D.aircraft38.gear_contact39` exists. It resolves the real `Skyward:SM_Plane_LandingGear` actor, replaces only that actor's mesh and asserts tyre-bottom/apron contact within3mm. The original actor name, tag, world transform and fixed cabin floor remain unchanged.

Re-copy updated `airside_math38.py` and `airport_airside38.py` to Content/Python. The complete aircraft AABB now includes corrected landing gear down to z=-3.689. `BODY_AIRCRAFT_BOUNDS` separately records the airframe body, so a body clearance claim is never used as a substitute for gear contact. `collect_airport_obstacles` excludes aircraft-tagged meshes even when their replacement asset lives under `/Game/Airport38`.

Real defects found and repaired from actual38 source and genuine screenshots:

1. Seven cabin/business passengers remained at original x coordinates, visibly seated on the apron in screenshots30/32. The patch translates their placement/source objects +16 exactly once. Root's existing native character/proxy synchronization applies their new locations.
2. All nine bridge sleeves had a32.5mm unsupported floor-to-wall slot and a77.5mm carpet shortfall. Structural decks now extend beneath the lower wall; carpet enters the kick seal by19.5mm. No duplicate carpet overlay is added.
3. Two first-sleeve bearing blocks sat on the joint landing away from their trimmed sidewall supports, producing the loose-looking black floor nubs in screenshot28. They are moved to the real bearing/wall start.
4. The flat docking membrane stopped at x13.891, while evaluated preserved fuselage geometry at its upper seal lay near x14.000. Lower bellows sides penetrated the skin by~.33m. A contoured weather membrane, seven supported accordion ribs and physical aperture returns now follow measured skin intersections with a12mm compression allowance.
5. Thin trim/gasket bevels were wider than half the part thickness. Evaluating the actual saved assets produced collapsed/zero-area corners. The patch limits those fillets to20% of the smallest real dimension.
6. All ten modeled aircraft tyres bottomed at z=-4.20, while visible poured apron panels top out at-3.689. The copied gear compresses oleos/retained braces by.511m with a continuous deformation, preserving fixed upper mounts and full tyre/hub diameters. Each tyre contact is recorded in `D.aircraft38.ground_contact39` for the upcoming flight/ground controller.
7. Static ground-power wheels had a40mm actor-to-pad gap. Its base is lowered from-3.70 to-3.74 so its local+.04 wheel vertex meets the pad.
8. The final bridge truck used the underlying terrain height,91mm below the poured apron. Shared bridge pose math now follows the actual visible apron and authored parking pad; the corresponding source locations and hydraulic lengths are synchronized.

Validation performed:

- Appended actual bridge collections from `Airport_Repaired38.blend` without opening/saving the shared file. **4,390 evaluated floor/roof triangle probes found no missing interior coverage** before refinement.
- Measured canopy skin contacts against the real exterior, cabin finish, door bay, window walls, barrel and vestibule geometry, rather than relying on bounding boxes.
- `test_contacts39_blender.py` passes:11 exports,7 NPC relocations,94,250 evaluated faces with no zero-area faces, idempotence, preserved tyre diameters and all tyre bottoms at-3.689, corrected canopy contacts and refreshed complete stowed bounds.
- Eight real-manifest/geometry/interlock tests remain passing after the corrected support-height and full-envelope changes.

`ContactRefinement39_Test.json`, `ActualAssemblyScrutiny38.json` and `ActualGearContacts39.json` contain the measurements. No source/native master or shared editor was changed by this fixer. Root owns final import, gear-contact native assertion, screenshots and expanded flight/character work.
