# Cabin fit, interaction and cargo pass — revision13

The galley retains its constructed cabinets and appliance chambers. This pass closes specific fitting gaps, lowers the passenger service ceiling, changes the luggage-bin hinges, adds lavatory hardware and extends the existing lower hold. The accepted four-suite / forty-economy layout and rear preparation room remain.

## What changed

- Coffee dispensing heads have socketed feed risers, compression nuts and smoothly formed discharge tubes. The machine seats on its worktop; its reservoir access opens onto a cassette and pickup tube. Upper service closures have a continuous backing and ventilation fascia.
- Galley drawers have folded returns and approximately4mm designed reveals between fronts. Their trays, channels and dividers keep their dimensions.
- The unsupported crew and service checklists were removed. A solid utility enclosure and faceplate mount against the middle partition, with retained isolation knobs and surface-mounted legends.
- The inner acoustic ceiling peaks at2.40m. Centre service units, controls and reading lights come down34cm; side units and their bin assemblies come down25cm. The aircraft exterior keeps its dimensions. Lavatory crown fillers meet the lower liner.
- Both overhead bin leaves pivot at their upper hinges and lift toward the aisle by78degrees. Fixed and moving hinge knuckles meet at the same height. Saved-mesh checks inspect the open leaves against the new roof.
- Economy IFE adapters follow the actual curved chair shell, with117 measured support samples per adapter. The last row uses separate screen-free chair kits. There are36 seatback displays, four first-row bulkhead displays and four suite displays; all40 economy passengers retain a display ahead.
- The vacuum-toilet rear casings now end below the lid hinges, clearing the opened lids. Waste flaps return closed automatically after a push.
- Sliding lavatory doors have formed inset borders, recessed pulls, retained screws and guide hardware. Jamb modules show green VACANT or red OCCUPIED. Privacy locks operate from inside; separate inside release controls allow exit.
- Two rear extinguishers have shaped pressure vessels, retaining cradles, straps, connected hoses, gauges, pins and instruction bands. Their backplates seat into the lavatory aft partition.
- A small outlined crosshair stays at screen centre. Left click and E share the use action. Interaction rays test visible aircraft geometry; invisible standing-body proxies still stop walking but do not obscure controls. Physical walls block remote targets. Exposed grip points follow their controls as they move.
- Two cockpit light keys previously obscured by the yokes moved with their trim into supported aft side-console pods. Original apertures have retained blanking caps.
- The lower floor now spans cabinY1.30–34.65m, a33.35m compartment span inside the existing barrel. The aft extension is12.85m. The stair landing stays clear. Additional racks hold separate folded cartons, timber crates, sewn duffels and molded equipment cases, with different construction and silhouettes.
- Returning through the top stair portal restores the main-deck floor even after a missed stair sample. The correction keeps collision enabled and is limited to that portal.

## Verification

Native verification completed successfully on the final saved source. All 1,484 action/API checks were fresh; no earlier passes were carried forward. All 24 standing walking routes, 24 full-body clearance audits and six closed-door barriers with reopening passed. Both repeated cargo-stair returns ended at exactly1.62m standing eye height.

The final run saved 17 genuine current-source game screenshots. The earlier69-image revision13 run remains separately labelled as progress history before the final lavatory repairs. Independent saved-source inspection passed 76/76 checks; six floor-selection regressions passed. The native import and final delivery audit match the exact saved source and manifest. Reports are in `ArtBible/`; the final native run is archived under `ArtBible/ValidationRuns/13-full-4/`.

## Play and edit

`Run Plane.cmd` starts the local walkthrough. W/A/S/D moves; mouse aims; E or left click uses the fitting under the crosshair. Look away and use E to stand. V cycles the exterior review views. Stow the crew pans beside the hatch before using the lower stair.

`Edit Plane.cmd` opens the editable model. `Update Plane.cmd` exports saved edits and rebuilds Unreal without regenerating geometry. Deliberate revision13 regeneration starts from `Versions/Revision12_Before_Cabin13/Plane.blend` and uses `SourceAssets/Blender/rebuild_aircraft13.py`.

## Limits

This remains an uncooked local Unreal walkthrough. The utility, appliance and cockpit controls have authored visual states; they do not simulate electricity, plumbing, cooking or avionics. The fire equipment is mounted scenery, and cargo cannot yet be picked up or packed. The compartment extension is an authored fictional layout, without aircraft engineering or systems certification. Exterior polishing, production optimization, flight, turbulence, damage, characters, serving, multiplayer, audio and story remain separate unfinished work. Visual approval remains with the user. No paid generation was used.
