# Skyward Air Terminal34

The airport-wide continuation of the approved Warm33 room. Run `Run Terminal34.cmd` to start at the forecourt. The main `Airport/Run Airport.cmd` also opens this version.

## Play

WASD and mouse move/look; Shift runs; E uses the crosshair target. Follow the HUD and gold check-in route. Join the queue at its marker, wait for Desk01, obtain the pass, pick up the blue suitcase and place it on the belt. Follow the screened route to A07, scan the pass and board across the bridge. A08 has distinct information screens and does not board this flight. Existing aircraft interactions remain available. Tab toggles spectator mode; Space/Ctrl change height there and Shift boosts movement. The normal entrance remains the default spawn.

`Open-Terminal34.ps1 -Checkin` opens the approved room directly. `-Editor` opens the native map for editing. `-Validate` runs the continuous route helper; `-Capture` runs the focused seating check and saves the native screenshot set, then exits.

## Editable outputs

- `Airport_Terminal34.blend`: complete editable terminal master; constructed profiles, hardware, fitted fixtures, source modifiers and asset collections are retained.
- `Exports/FBX`:40 new/adapted mesh families, alongside the preserved inherited project assets.
- `Exports/airport_layout.json`:17 zones, existing openings, placements and interactions.
- `Exports/Changes34.json`: affected placements, added assemblies and20 review camera definitions.
- `../../SkywardAir/UnrealProject/SkywardAir.uproject`: native project; map `/Game/Airport34/L_Airport_Terminal34`.
- `Review.html` and `Screenshots/`:20 genuine raw1920×1080 PNGs, with captions.
- `ArtBible/Delivery34.json`: source, native map, layout, screenshot and runtime hashes.

## Scope and verification

The approved entrance/check-in flow and geometry are preserved. Fifteen remaining zones receive coordinated material, wall, floor, coffer and lighting work, plus remodeled equipment and furniture. Gate desks, scanner panels, storage, café fixtures, charging, vanity, reclaim, the bridge and exterior have modeled construction details. Light remains predominantly associated with fixtures, with deliberate supporting ambient fill. The new exterior assemblies add airfield paint, apron joints/drainage, hangar frontage/roof seams and restrained landscape berms. The40-family count includes adapted source assets; it is not40 completely new designs.

`RouteProof34.json`:117 passing checks, one continuous actual pawn walk, zero route teleports. Covers arrivals/public return, check-in queue advancement, real suitcase pickup/belt acceptance, screening, gate/amenity detours, pass scan and boarding. The final sign and decorative exterior changes do not change passenger collisions or openings and were inspected through focused native captures. `FinalPhotos34.json`:6 passing viewport/display/seating checks and20 validated raw images. It uses one explicit setup teleport to an empty gate seat; sitting and standing then use real game functions. Its setup teleport is separate from the zero-teleport route proof.

The initial sign import had a section/print rendering problem. The final native solution uses mounted distance-field lettering on both manufactured sign faces, avoiding reliance on that face shader. The Blender master retains the matching editable printed sign surfaces. Text is attached to the board surface and is nonblocking.

## Remaining project limits

This is a local editable airport prototype. Character meshes/rigs, some character poses, the aircraft, inherited vehicles and the broad airfield footprint are reused. Distant terrain remains coarse beyond the detailed operational areas. General crowd navigation, all-airport prop interactivity, final character art, sustained FPS certification, multiplayer and standalone packaging are separate remaining project work. The current SA107 passenger journey is playable; the entire airport is not a completed commercial game. HTML source and image links are validated locally; browser rendering was not tested because local-file browser access was blocked earlier.

Earlier maps and source versions remain available. No paid generation, downloaded third-party models or external messaging was used for34.
