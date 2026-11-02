# Genuine taxi exterior diagnosis

Reviewed `Screenshots/Flight39_taxi.png` against the exact current exported FBXs, original Revision18 FBXs, authored source and flight bindings. No Unreal process was launched and no native assets were changed. Source verification used one private Blender process, read the current master, and did not save it.

## Established

- The broad dark wing rectangles are the authored `Conformal upper-wing protective coating15`, not absent control surfaces. The intended material is `MI_Plane_AirCorroguard15`: linear RGB0.33245/0.37626/0.40198, roughness0.52, metallic0.28. All288 polygon normals point upward; all1,152 actual exported corner normals point upward (normal Z0.99234–0.99907). The panels are projected2mm above the actual wing. Native effective material/override checks are still required before attributing their very dark appearance to a colour defect.
- All13 neutral actuator exports reconstruct original evaluated exterior vertices; maximum error0.000000238m. No missing neutral geometry or export-origin offset was found.
- There was a real inner flap hinge defect: lower-skin gear aperture cuts duplicate geometric corners. The old raw vertex average made the left/right root flap axes differ1.827°, and the next pair's hinge heights differ69.255mm. Unique geometric leading-edge endpoint fitting restores symmetry. This does not explain the dark coating and has no neutral taxi offset.
- The upper-crown source contact scan read220 original cabin asset FBXs across770 placements and found no interior vertices outside the straight pressure crown above z2.65m. Source aerials/beacons are present at their authored positions. This does not rule out shoulder penetrations, animated shade state errors or native binding/aliasing artifacts; it is not a reason to remove useful aircraft fittings.

## Implemented authorized flap-only correction

`flight39_surfaces.py::_hinge` deduplicates geometric positions only for objects prefixed `Independent trailing flap`. Other hinges, evaluated neutral lofts and runtime files are untouched.

For an already-built current master, call `flap_hinge_patch39.apply(ctx)`. It recentres the following four source meshes and their actor origins together, updates D instance/pivot/axis metadata, and registers them for targeted export:

- `SM_AP_F39Surface_00`
- `SM_AP_F39Surface_01`
- `SM_AP_F39Surface_06`
- `SM_AP_F39Surface_07`

Root must export/import those four kits with the updated placements before flight installation. Do not update native metadata alone: that would move a mesh whose geometry still uses the old origin.

`FlapHinge39_Verification.json` proves original/current evaluated neutral vertex preservation within2µm, actual mirrored vertex agreement at0/5/15° deflection, builder/upgrade hinge agreement and metadata/geometry idempotence. No master or shared export was written by the test.

## Pending actual native attribution

Root calls `exterior_native_probe39.apply(G)` in the existing final parked review session. It writes `ArtBible/ExteriorNative39.json` without changing actors, materials, controls or assets. It records full effective and default material-slot interfaces/overrides/colour getters, all13 actual actuator carrier-relative pivots/rotations,24 wing/shoulder/crown hit owners, and the48 shade state/stroke settings.

Until that evidence is available, the tiny white edge blocks/shoulder speckles remain unconfirmed. Do not claim that a source inspection alone fixed their appearance.
