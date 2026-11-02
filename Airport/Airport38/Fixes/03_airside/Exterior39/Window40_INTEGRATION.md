# Window40 coherent window repair

Current-master source/native writes belong to root. This module and its private unit model do not save the airport master or overwrite shared manifests.

## Actual causes found in genuine native views58/60/61/78/79

1. The cabin liner top exceeded the pressure skin by61.194mm. Obsolete old cassette/grip geometry also remained alongside the working shade system. These caused pale exterior strips and ambiguous top borders.
2. Revision18 stretched the window aperture vertically but did not stretch the weather-seal path. The old black U crossed inside the lower opening by about125mm instead of following its edge.
3. The upper rack underbody obstructed normal seated-eye rays toward the window top. Actual ray hits occurred atabsX2.178,z1.849.
4. The cassette mouth and long separated guide posts interrupted the upper rounded reveal. Raising a cassette blindly would have moved its panels through the overhead bucket.
5. The old raised finger pull extended35.5mm inboard of the shade sheet and intersected the business-side shell by23.5mm. The fixed rocker housing also lacked a real connection to its guide.

The glass material itself is not blamed: the approved root blue-green glass palette is retained, and the broad dark wing coating is untouched.

## Modeled correction

- Preserve the full0.70×1.00m clear window,0.16m corner radius and48 mechanisms. Build a smooth continuous rolled reveal, one optical pane, matched pressure opening/gasket and a real folded aperture return.
- Remove old duplicate cassette/grip geometry. Fit liner/shoulder inside the true pressure envelope.
- Put the retained cassette feed atz2.045, topz2.325. Fit the rear service chase in the rack's unused outboard218mm. Retain the complete PSU attachment footprint throughabsX2.01, existing hinges, bin doors, luggage and their targets. The five molded bucket floor/crown/end parts are tapered together, giving a genuinely clear chase rather than moving panels through a floor.
- Retain a curved captive track. Lower sheets stay outboard of the business shell before moving inboard near the upper pocket. Nothing disappears or changes visibility.
- Model an actual4mm recessed finger pocket inside the12mm shade leaf. Keep the rocker face/switch target; its tapered rear now overlaps the real guide return.
- Include the special cargo-pressure bay: it contains the final two passenger windows. Its lower cargo opening and external door/hinge source geometry remain in their original locations.

## Integration order

1. Source: `window40.apply(ctx)` on the preserved current-master assembly. It creates/synchronizes the10 IDs below and registers them in`ctx.a.ASSETS`. Root saves and exports these assets in its normal targeted batch.
2. Native: `window40.apply_native(ctx)` swaps198 original tagged placements while preserving actor transforms. Then run root`glass39.apply_native(ctx)` to bind approved true-glass slots.
3. Runtime data: after`airport_airside38.prepare_plane(P,D)` and`exterior39.prepare_plane(P,D)`, call`window40.prepare_plane(P,D)` before Flight39 preparation/configure.
4. Runtime installation: after`airport_flight39.install(G)`, call`window40.install(G)`. This wraps the current carrier-aware mover for the48 curved tracks. It safely falls back to parked coordinates when a flight frame is absent. It must run after Flight39 because the flight frame otherwise installs its legacy straight roller mover over this adapter.

Actor names, switches, validation approaches, shade widths and interaction semantics remain. Closed sheet positions move about32mm outboard into the fitted guides; open stow height increases85mm. Existing source mechanisms stay visible and editable at every state.

## Targeted asset IDs

- `SM_AP_W40WindowWallL`
- `SM_AP_W40WindowWallR`
- `SM_AP_W40PressureWindows`
- `SM_AP_W40CargoBayWindows`
- `SM_AP_W40ShadeFrameL`
- `SM_AP_W40ShadeFrameR`
- `SM_AP_W40RackL`
- `SM_AP_W40RackR`
- `SM_AP_W40ShadeHandleL`
- `SM_AP_W40ShadeHandleR`

`Window40_UnitKits.blend` is the private editable unit source. `export_window40_units.py` exports just these10 families into`Window40Package/Exports`, without touching the user's master/exports.

## Evidence and limits

`Window40_Verification.json` contains actual evaluated geometry/contact checks: zero degenerate triangles;6,844,704 moving-leaf vertex samples over48×5×41 states; at least17mm inside the skin and6mm outside the business-side shell;66/66 corner/top sight rays clear;10,250 rack-triangle crossing probes without collisions; unchanged switches and repeat-safe source/data preparation.

These source measurements establish coherent construction and motion. Root still needs native closed/open interior and exterior close-ups, actual interaction checks and the final look under the game renderer. This unit build does not claim those screenshots were already taken.
