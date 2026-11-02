# Quality revision 02 — 23 October 2026

The user's accepted broad proportions are retained. This pass improves the airplane interior using the uploaded README and cabin/dashboard screenshots. It does not add characters, story, flight or paid generated assets.

## Visible changes

- Upholstery: shaped lumbar and shoulder support, piping projected onto the smoothed fabric surface, separate headrest stitching and cushion boxing seams. Woven material replaces the smooth plastic response.
- Seat construction: inset molded arm access panels, recline buttons, captive fasteners, rail anchors, shell joins, tray hinge hardware and safety cards.
- Windows: one continuous rolled molding with denser corner sampling, deep reveal, rubber glazing seal, panel separation and shade pull. The accepted clear opening remains 0.79 × 0.965 m.
- Racks: air vents and pivots, separate service strip, diffuser optics, mounting fittings, load markings and row placards.
- Cockpit: distinct calibrated scales, numeric markings, a sky/ground attitude insert, radar targets, warning arcs, panel fasteners, throttle labels and an updated status monitor. Instrument covers have a separate low-reflection material.
- Materials: five original seamless families, each with colour, roughness, height and normal maps. Upholstery, carpet, walnut, molded polymer and vinyl have distinct responses. These were authored numerically; no screenshot pixels were used as textures.
- Unreal: softer cabin illumination, lower direct sun contribution, reduced reflection on instrument glass, temporal anti-aliasing and contact occlusion. The existing DX11/SM5 compatibility path remains in use.

## Import correction

The engine review found that reimport had retained some older material section names. This prevented new materials from reaching the intended surfaces. The importer now resets material conflicts to the current FBX data, orders sections from the source, and checks every current plane mesh's imported material names against the Blender export. `UnrealBuildReport.json` records these checks.

## Editable delivery and evidence

`Plane.blend` and `SourceAssets/Blender/SkywardAir.blend` contain the authored meshes and modifiers. `EDIT_Seat`, `EDIT_Dashboard` and `EDIT_Window` expose their shared source geometry. `Update Plane.cmd` exports saved edits without regenerating them. `polish_plane.py` reproduces the pass from `Versions/Accepted_Before_Quality/Live_Session.blend`.

The accepted source, six Blender views and five Unreal captures are preserved in `Versions/Accepted_Before_Quality`. `Screenshots.html` includes same-camera Blender before/after sliders and labels intermediate checks separately from current captures. Files 66–69 show the first quality check; files 70–73 show the corrected Blender finish. UE 10–21 are earlier lighting/material checks. Current authoritative engine views are UE 22–27, after the material binding and oblique camera direction corrections in revision 03. These are genuine project renders/captures, not generated concept images.

## Remaining gaps

The exterior/nose silhouette and cargo mechanisms have not received this interior finish pass. Engine lighting remains an approximation of the Blender preview on this machine's compatible renderer. Some small imported surfaces still report tangent warnings; further UV cleanup, simplified collision, production LODs and performance profiling are pending. Detailed dashboard collision is heavier than a production game should use. No frame-rate target or final art approval is claimed. The current walkthrough tests cover the aisle, cockpit doorway and sidewall boundary only.

No Higgsfield calls or credit spending were made.
