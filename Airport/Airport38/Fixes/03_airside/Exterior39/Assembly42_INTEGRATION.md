# B41 / Window42 / AircraftFinish42 targeted assembly

Nine new source kits, preserving the already integrated B40 and W41 files. No airport master, character source or native asset was modified by the child. Source/API evidence is separate from the parent's required native appearance/input review.

## Sequential source and native integration

1. Source entries, after existing B40/W41 and final chair updates:
   - `business_belt41.apply(ctx)` — two new worn belt kits. Updates existing B40 records, four worn overlays and four absolute retained-lid hinges. Existing base/stowed/lid meshes and control names stay.
   - `window42.apply(ctx)` — four new wall/frame kits. Replaces the 48 walls and 48 fixed shade frames; no fixture, shade or light transforms change.
   - `aircraft_finish42.apply(ctx)` — three new PSU/soft-luggage kits, binding the existing 70 instances by their original actor names.
2. Export the nine newly registered `ctx.a.ASSETS`; use the existing targeted exporter. Do not call any `build_units` function on the shared master.
3. Native entries after import, using the updated source D:
   - `business_belt41.apply_native(ctx)` — swaps four worn assemblies and places the four retained release lids at their new canonical worn baseline. Do not stage them in a released pose before configure.
   - `window42.apply_native(ctx)` — expected 96 fixed mesh actor swaps, no transforms.
   - `aircraft_finish42.apply_native(ctx)` — expected 70 existing actor swaps, no transforms/interactions.
   - Run the existing parent `glass39` hook after the window import to restore its approved glazing overrides.
4. Runtime data, after the existing airside/chair/Exterior39/Window40/Window41/Belt40 preparation and before configure/Flight39:
   - `business_belt41.prepare_plane(P,D)`
   - `window42.prepare_plane(P,D)`
   - `aircraft_finish42.prepare_plane(P,D)`
5. No new runtime installer is needed. Keep existing Flight39 → Window40 → Window41 → Belt40 installers. Existing four release controls still drive the actual worn/stowed assemblies; the new data only changes the canonical worn hinge and its correct released displacement.

## Exact nine families

- `SM_AP_B41LapWornCrew`
- `SM_AP_B41LapWornGeneric`
- `SM_AP_W42WindowWallL`
- `SM_AP_W42WindowWallR`
- `SM_AP_W42ShadeFrameL`
- `SM_AP_W42ShadeFrameR`
- `SM_AP_A42PSUCarrier`
- `SM_AP_A42ExpeditionDuffel`
- `SM_AP_A42Weekender`

## Actual visual causes and fixes

**Belt:** native `59_BusinessCharacter.png` proved that zero intersection counts were insufficient: the B40 radial fit used wrists/hands as outer lap surfaces and visibly formed cuffs. B41 fits only pelvis/spine/thigh/trouser triangles, explicitly excluding all upper-arm/forearm/hand/finger-weighted faces. The belt lies at the actual low hip/lap level z.600; buckle centreY−.430182 and hingeY−.441182,z.622. Original ±.325,+.15,.50 chassis anchors and supported stowed halves remain. The actual final character source silhouette shows the hands naturally above the lap belt. Against source177c, 68,252 complete band/buckle probes have zero penetration; minimum body gap4.43mm, minimum arm gap4.75mm. Final character surface updates require one final read-only reprobe, without rebuilding the frozen belt library.

**Windows:** native `85_WindowCornerClose.png` and source pixel ownership exposed long reverse-profile return facets and pointed triangular mechanism shields. The new collar has a monotone .690→.700 inner return, true2mm wall gauge and an actual swept shade-service recess. Old pointed shields are removed; a short rounded cassette feed cowl joins the retained housing. Dark captive wear channels remain real geometry; their lower stops now end behind the rounded side reveal instead of projecting below it. Rear capture clearance and the cassette back wall were corrected after the stronger whole-frame test exposed section4 contacts. The original48 shade curves, 8mm fit, 150mm complete fixture lift, source points and pressure aperture stay unchanged.

The new window test includes all fixed frame/cassette/guide/cowl surfaces as well as the collar: 7,020 full98–99% aperture rays clear, 210 actual moving-leaf pose pairs have zero triangle crossings, and no disjoint collar faces cross. The minimum evaluated pressure-skin clearance, including the perimeter guide rear flange, is2.00mm. The original .700×1.000m pressure aperture/glass is unchanged. The dark recess beside the glass is the actual shade-service channel, not a white ripped/tapered trim facet.

**PSUs:** the carrier gets warm satin grey broad faces while nozzles, key recesses and dark plenum remain distinct. A real modeling fault was found during verification: the original25mm bevel on a16mm plenum cover collapsed its edges into zero-area triangles. Safe manufactured rolls now stay below18% of part thickness. Source dimensions, pivots, nozzles and actual control actors remain unchanged; native defaults are reset during the new mesh binding.

**Soft cargo:** both duffel families' rigid high carry arches are replaced by webbing draped onto the actual compressed canvas surface. Strap ends still meet the existing leather patches; no bag body, shelf contact, label location or actor placement changes. Expedition maximum height drops .4788→.3753m and Weekender .3488→.24855m; both retain the exact ground minimum0. Handle underside canvas clearance is .35–.36mm at its closest; supported patch ends stay below8.5mm gap. Safe thin-label edge rolls also remove inherited collapsed label corners. The three finish kits contain94,064 evaluated triangles with zero degenerates.

## Evidence and remaining native check

- `Assembly42_SavedHooksVerification.json`: actual cold saved-library preflight and real Blender source apply/reapply with nine deliberate canonical-name collisions; all kits persisted and bind correctly through `.001` names.
- `Assembly42_AdapterVerification.json`: offline native/data repeat safety, 4 worn+4 lid updates, 96 window swaps, 70 finish swaps, correct released translation relative to the new absolute lid baseline.
- `BusinessBelt41_Verification.json`, `Window42_Verification.json`, `AircraftFinish42_Verification.json`: actual evaluated source/contact proofs.
- `BusinessBelt41_SourceSilhouette.png`, `Window42_SourcePreview_Standing.png`, `AircraftFinish42_DrapedHandles.png`, `AircraftFinish42_PSUFace.png`: genuine isolated source renders, not gameplay screenshots.

The parent must inspect native59/85 and overhead/cargo views after import, operate the four belt states and window/bin motions, and retain the existing full journey/Flight39 verification. Source/API passes do not constitute native visual approval.

## Final character and additional console checkpoint

`BusinessBelt41_FinalPoseVerification.json` now passes against final character SHA256 `eac73c0812391bc2f994d24cc9234c529be9a2d74175d41c1d58516c44703dff`:83,084 complete probes, zero penetration, minimum body4.433mm/arm4.749mm clearance and worn lid27.57–28.65mm clearance. The frozen belt bundle was read without any source or bundle writes.

The whole-aircraft ugly pass also identified the visibly folded centre console front in native39. This is a **tenth** asset, kept separate from the original frozen nine:

- Module `console_surface43.py`, kit `ConsoleSurface43_UnitKit.blend`, ID `SM_AP_C43DashboardFixed`.
- Run `console_surface43.apply(ctx)` **last**, after Flight39 extraction and the three source modules above. It replaces only the inherited hollow switch-tray casting while preserving365 other fixed dashboard objects byte-for-byte. It updates `D.flight39.dashboard_fixed_asset`; subsequent Flight native hooks must use that new field.
- Native: `console_surface43.apply_native(ctx)` replaces only the `Skyward:SM_Plane_AnalogDashboard` component mesh. All separate button/toggle/needle actors and their pivots remain untouched. Run the usual parent material hooks afterward.
- Data: `console_surface43.prepare_plane(P,D)` before configure; the existing Flight39 metadata mapping also sees the new ID. No installer.
- Source proof: exact original casting bounds, three real vent openings,4,716 evaluated triangles, positive volume, no degenerate/self-crossing/nonmanifold geometry. Broad front face corner normals align with+Y to at least.99999994. All365 other fixed parts and all needle/button/pivot metadata arrays are preserved. Cold saved-library apply with a deliberate canonical-name collision and repeat safety passes.
- `ConsoleSurface43_SourcePreview.png` is the actual fixed-kit source close-up showing the clean planar fascia. Existing moving caps/stems are separate actors and do not appear in this isolated fixed-kit render. Native39 must verify the combined assembly after import.
