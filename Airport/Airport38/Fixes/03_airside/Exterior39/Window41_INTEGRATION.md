# Window41 — full rounded opening and enclosed shade mechanics

This is a six-kit derived patch after the already applied Window40. It does not modify Window40, any shared master, the pressure aperture, the glass geometry, or the aircraft exterior/flight systems. The original .70 × 1.00 m pressure aperture with .16 m corner radii remains unshrunk.

The prior source preview exposed two real readability faults that the old 88% opening test missed: the extreme upper arc was masked by the bucket/actual PSU nozzles, and the steep narrow reveal return read as a pair of exposed rods. The new broad, rounded molded shoulder encloses the actual C guides; thin formed upper-corner shields remain open behind the moving leaves. No guide, shaft or fake mechanism is added to the viewing opening.

The complete fixed bucket/hinges, separate bin leaves, side PSU carriers/gaspers/buttons, lights and the PSU inspection camera move upward by 150 mm together. 120 mm still blocked 98 extreme-edge rays; 140 mm still blocked two gasper-tip corner rays. At 150 mm all 7,020 rays clear. The actual shoulder ceiling cove is raised locally, tapering to zero at the unchanged central-roof junction. All evaluated cove/rack/liner vertices remain within the actual pressure envelope, and actual cove/rack triangles do not cross. Central PSUs and the central roof stay fixed.

All 48 retained shade curves receive only an 8 mm parallel outboard fitting, preserving their exact motion deltas and stow travel. This keeps the formed guide lips clear while improving business-console clearance. Source geometry, source instances, native actors, data points and actual runtime poses use the same correction.

## Sequential parent integration

1. Source: after Window40, call `window41.apply(ctx)`. It appends the six frozen private collections from `Window41_UnitKits.blend`, registers them in `ctx.a.ASSETS`, swaps 126 existing window-wall/frame/rack instances, and applies the complete fixture translation exactly once. Do not call `build_units` on the shared master; that function is for the isolated verification build only.
2. Export the six registered collections using the existing targeted export helper. The other four Window40 families stay unchanged.
3. Native: call `window41.apply_native(ctx)` after importing those six assets. Expected counts: 126 mesh actor swaps; 171 complete fixture/light/camera actors lifted; 240 moving shade parts fitted outboard. Existing aircraft tags, movable names, rotations, pivots and interaction labels are retained. Actor-position snapshots prevent double translation through attachment inheritance. Run the parent's existing `glass39` material hook afterward.
4. Data: after airside +16 translation, Exterior39 and Window40 preparation, call `window41.prepare_plane(P,D)` before configure/Flight39. It uses the original-name list stored by source apply under `D.repair38.window41`; it does not reclassify central PSUs by shifted positions. Fixture points/lights/camera/parented labels move together; ground validation approaches and all motion vectors stay unchanged.
5. Runtime: call `window41.install(G)` after Flight39 and Window40 installers. The wrapper retains the existing curve and flight-carrier conversion, then applies the single 8 mm parallel fit. Repeat installation is safe. BusinessBelt40 can install afterward independently.

## Exact targeted families

- `SM_AP_W41WindowWallL`
- `SM_AP_W41WindowWallR`
- `SM_AP_W41ShadeFrameL`
- `SM_AP_W41ShadeFrameR`
- `SM_AP_W41RackL`
- `SM_AP_W41RackR`

`Window41_Verification.json` contains five source scrutiny passes: nondegenerate modeled geometry; 7,020/7,020 full 98–99% aperture rays across both sides and normal seated/standing eye positions including actual PSU hardware; complete fixture/point metadata repeat safety and maximum nearest seated-control reach 0.633 m; 3,505,824 shade geometry samples with minimum 9.076 mm pressure-skin, 3.076 mm glass and 14.000 mm business-console clearance; 210 actual mechanism/leaf pose pairs and two cove/rack pairs with zero triangle crossings.

`Window41_AdapterVerification.json` proves the offline 126/171/240 native contract, unchanged central PSUs, repeat safety, preserved relative pivots, and actual carrier-aware curved poses at closed/half/open. Actual native visual/input review remains the parent's final step.

`Window41_BinClearance.json` adds the requested actual raised separate-leaf proof: all 30 leaves sampled at 41 authored Y-axis poses from 0 to ±78°, plus all 120 attached side PSU parts. 1,689,680 evaluated vertex samples and 1,350 actual ceiling/cove triangle pairs have zero crossings; minimum pressure-skin clearance is 381.9 mm. All moving/attached vertices remain at absX ≥ 1.139726 m, leaving 39.7 mm lateral clearance to the unchanged central ceiling strip ending at absX 1.10 m. This read-only check made no geometry/module changes.

The two `Window41_SourcePreview_Standing.png` / `_Seated.png` images are genuine CPU renders of the isolated authored source geometry, using the parent's existing glass39 source preset. They are source-model previews, not Unreal gameplay screenshots. They include the actual raised PSU source parts. They do not substitute for the parent's assembled/native whole-cabin proof.
