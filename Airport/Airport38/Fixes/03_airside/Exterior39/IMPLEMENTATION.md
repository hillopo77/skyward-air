# Exterior39 fitting refinement

Frozen scoped module: **`exterior39.py`, guide-fit version2**.

If the first version has already been applied, call **`finalize(ctx)`**. It safely upgrades the two already-derived frame channel sets, keeps their modeled pockets and all other fitting kits, and re-registers the same six export IDs. Lower guide shoes now remain at least14mm outboard of the business suite shell below its1.3565m top, with their manufactured knee above it at1.40m. A private test reproduces the real version1 starting geometry and confirms the idempotent upgrade.

- Source: **`apply(ctx)`** on the current master. It copies only the six listed linked fitting collections, registers derived assets in `a.ASSETS`, and binds all76 existing fitting instances to the copies. It never writes a shared file itself.
- Native: **`apply_native(ctx)`** after fresh import. It matches actual `Skyward:` actor tags, changes only the static mesh and correct material-slot bindings, and asserts unchanged actor transforms. Run root `glass39.apply_native(ctx)` afterwards so true glass gets the approved material while the repaired opaque seals remain opaque.
- Runtime: copy **`exterior39.py`** to Content/Python and call **`prepare_plane(P,D)` after `airport_airside38.prepare_plane(P,D)` and before Flight39 preparation / `P.configure`**. This changes only the48 shade mechanisms' stow displacement by120mm inboard. Original closed positions, interaction points, movement labels and control semantics remain unchanged. Plane18's existing shade animator and Flight39's reference-frame wrapper consume the new displacement normally.

Derived asset map:

| Preserved source | Derived fitting |
|---|---|
| SM_Plane_CockpitShell | SM_AP_E39CockpitShellClean |
| SM_Plane_WindowShadeFrame18_L | SM_AP_E39ShadeFrameL |
| SM_Plane_WindowShadeFrame18_R | SM_AP_E39ShadeFrameR |
| SM_Plane_OuterWindowBarrel | SM_AP_E39WeatherSeals |
| SM_Plane_PassengerDoor07_L | SM_AP_E39PassengerDoorL |
| SM_Plane_PassengerDoor07_R | SM_AP_E39PassengerDoorR |

The fixes address actual visible/source defects:

1. The cockpit had six complete added pearl tube outlines around its six real panes. Their diagonal runs produced the lines across the view. Only those tubes are removed. All1,253 actual glazing vertices and all pressure-shell apertures remain in place.
2. The retained upper shade pockets pierced the curved outer skin by130mm, creating the repeated white caps visible above exterior passenger windows. They now have modeled curved hollow shells, real feed apertures, fitted end returns, felt mouths and continuous open C guides. The modeled shells remain at least31mm inside the pressure envelope after modifiers.
3. The telescoping shade stack formerly remained outboard when stowed. The data hook moves it120mm inboard into the modeled pocket, retaining its original closed pose and player target. Across48 mechanisms,21 animation positions and290,304 sampled slat vertices, the closest point remains47mm inside the pressure envelope.
4. An earlier broad material replacement assigned transparent sky glass to the rubber weather seals. Those two strips are restored as opaque seals, and remodeled using a stable radial sweep after evaluated source inspection found collapsed faces at the old tube-frame flips.
5. Both bored pressure-door leaves receive a nondestructive4mm manufactured edge roll; their source aperture vertices and all hinge pivots remain unchanged. Thin inherited bevels are bounded below part thickness to prevent collapsed corners.

Five actual scrutiny/model/regression passes are recorded in **`Exterior39_FivePasses.json`**. The factory-empty test loaded the exact current linked source references, executed the real source patch, sampled evaluated geometry and full shade motion, and checked48,242 evaluated faces with zero zero-area faces. `test_exterior39_blender.py` reproduces this without opening or changing the shared master.

Root still needs to import, wire the data hook, inspect both shade end states and intermediate motion, inspect the wider cockpit view, and take genuine native exterior/window close-ups. No native visual approval or flight-performance result is claimed from source checks. F39AirframeFixed, root nose geometry, dashboard/control surfaces, gear retraction and glass materials were not edited.

Whole-map presentation finding sent to root: the contact sheet was stale relative to newer native photographs, retaining earlier floating passengers and the removed ramp track. Regenerate it from final captures before delivery.
