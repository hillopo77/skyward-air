# BusinessBelt40 — frozen final body fit

Final character authority is`Characters/Revision39/Characters39.blend`, SHA256`177c3ee1b7a0db92fd668ea205cafe97784a9a734a668018fb88dcc13929301c`. The private build reads its actual Crew/HoodieLuxurySeated mesh, including final hands, and the ergonomic chair. It does not modify character files, Window40, airport master or native assets.

The old fixed central-pan webbing/selvage/receiver/pin were owned by the chair mesh;8 source parts are removed from the derived chair. Each arm-mounted anchor has an actual retained D-loop and chassis plate. Released halves follow the actual outer cushion surfaces and park their separate receiver/tongue in supported side clips. Fastened halves follow the posed hip/lower-abdomen surfaces with actual thickness and stitches; the female receiver, male slotted tongue and transverse hinge/lid are modeled separately.

The semantic lap anchor was not a skin surface: the actual front atz.66 wasY≈−.337. Final hand scrutiny required the front band/buckle atz.705, centredY−.353435, with its actual hinge atY−.364435,z.727. Side anchors remainat±.325,+.15,.50. These values came from the final body/hand footprint rather than assuming that a centre-only fit was sufficient.

## Root's sequential integration

1. Apply the final character/luxury-chair source updates first.
2. Source: `business_belt40.apply(ctx)` appends the5 private kits from`BusinessBelt40_UnitKits.blend`, registers them and adds8 distinct overlay instances. It swaps the four source chairs to the belt-free ergonomic base and keeps all original seat/control names and routes.
3. Native: after final character/chair native hooks, call`business_belt40.apply_native(ctx)`. It binds4 chairs+4 retained lid/control actors+8 stowed/worn overlays (16 actors). Overlay actors get real aircraft tags for the existing flight carrier. No new physics, editor or game process is started by the module.
4. Data: after`chair_runtime39.prepare_plane` and the aircraft translation, call`business_belt40.prepare_plane(P,D)` before configure/Flight39 preparation. It sets absolute fitted lid positions; it does not add a second80mm chair drop.
5. Runtime: call`business_belt40.install(G)` after Flight39 and any window installers. The ordinary existing control targets then drive actual worn/stowed geometry and the retained lid pose.

The original controls remain`Business belt release 112/212/312/412`. They now fasten/release actual webbing assemblies rather than merely toggling a lid. The occupied Business02A NPC defaults fastened; the three empty suites default released/stowed. A player must sit in an empty suite to fasten it. Leaving the suite stows its belt after the existing stand operation succeeds. NPC belts remain operable. No airport route or flight controls are changed.

The source control actor is kept in its canonical worn closed pose so configure captures a valid transform basis. The runtime applies released side-park translation and155° lid opening from that basis. Do not stage/save the native control in its released pose before configure, or the baseline would be applied twice.

## Exact targeted families

- `SM_AP_B40LuxurySeatBase`
- `SM_AP_B40LapStowed`
- `SM_AP_B40LapWornCrew`
- `SM_AP_B40LapWornGeneric`
- `SM_AP_B40ReleaseLid`

`BusinessBelt40_Verification.json` proves six actual source/contact passes against177c:69,388 evaluated triangles with zero degenerates;68,252 worn vertex/edge/face-centre probes with no body/hand penetration; separate lid worn/released-pose checks; stowed cushion clearance1.6–4.4mm and maximumabsX.331 inside armwallabsX.335. The body-fit minimum signed clearances are positive (Crew.922mm, generic1.352mm). Source assembly data repeat is stable.

`BusinessBelt40_AdapterVerification.json` proves the offline16-actor/4-control contract, visibility targets, default occupied state, no double chair drop, seated fasten/release, auto-stow and repeat safety. Actual native visual and input verification remain root's final step; these source/API checks are not presented as game screenshots.

The first saved-library integration attempt exposed a Blender persistence fault: the unit scene did not use the base and separate lid collections, so they were omitted on save despite in-memory Python asset references. The corrected builder gives all five kits persistent library users and stable semantic asset properties. The actual saved file was reopened independently; all five Belt40 and all six Window41 collections are present. `BusinessBelt40_SavedLibraryVerification.json` proves real cold apply/reapply with five deliberate canonical-name collisions: appended `.001` collections bind by immutable requested IDs, all source instances use the correct collections, and reapply creates no extra collections or records. Geometry and final body fit remain unchanged; all six contact passes and offline adapter checks reran successfully. Corrected Belt40 bundle SHA256: `0efe19206ca412e2944e4725f3e24942bbbf5270ccd5caa093d95935535ba00f`.
