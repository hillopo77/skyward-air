# Terminal finish43

This is an isolated, repeatable source finish pass for the current `Airport_Repaired38.blend`. The shared master and native map are integrated by root. No inherited baseline assembler is rerun.

## Current visual criticism, ranked

Reviewed the actual native full-resolution files `01_Entrance`, `02_Checkin`, `03_BagDrop01`, `13_Concourse`, `17_A08Interior`, `19_WCLobby`, `23_Cafe`, `26_A07Desks`, `38_Forecourt`, and `55_SeatedCharacter` in Airport38/Screenshots. Read the complete user-supplied Downloads/read me production bible.

1. **TF43-01: Baggage service wall is an unfinished backdrop.** In 02 and especially 03, one broad brown surface meets bare rectangular holes. Its construction and service-bay identity disappear beside the detailed rollers. It needs a designed assembly, rather than another poster or a flat colour substitution.
2. **TF43-02: Public walls have no scale or fitted construction.** In 01,13,17,19 and55 the same cream field above the same teal dado continues for many metres. The lounges and passage feel like a generic hospital despite their useful room sectioning. Long wall fields need a quiet panel rhythm, real edge highlights, and occasional timber warmth.
3. **TF43-03: Circulation flooring and lounge carpet are visually boundless.** 02,13,17,23,26 and55 show enormous solid cream or mint areas. The flat response does not distinguish resilient stone/resin from brushed carpet. Add material scale and very low-contrast joints, while retaining navigable clear floors.
4. **TF43-04: The ceiling and upper plaster suppress the welcome.** 13/17/19 show a grey ceiling and uniform wall response; fixtures have structure, but the surrounding surface has no material identity. Give the ceiling a lighter matte finish and the walls low-frequency plaster response. Engine illumination still needs its own native check.
5. **TF43-05: Forecourt has the same flat surface vocabulary.** 38 has useful glazing/canopy framing, but its opaque faces read as colour blocks. This pass gives opaque exterior faces the same fitted broad-panel construction and a lighter material hierarchy while respecting the existing glazing and canopy.
6. **TF43-06: Other visual issues remain independent.** Repeated passenger outfits, chair hardware and aircraft window/seat finish require the parallel character/furniture and aircraft assignments. This module deliberately does not edit those sources.

## Implementation

`finish43.py:apply(ctx)` (also `build`) changes only the three current terminal structural families' material slots and adds two decorative families:

- `SM_AP_TerminalWallFinish43`: broad fitted plaster cassettes on solid public wall surfaces, at most 2.45m wide, 26.5mm thick, with real 18mm shadow joints, backing beds and supported top returns. Sparse broad timber panels warm the A08 wall. The public side is derived from final room occupancy, so windows and every circulation aperture stay clear.
- `SM_AP_BaggageBackdrop43`: quiet cream service-wall skin cut from authoritative opaque wall rectangles, two deep timber service portals, mounted service crowns, supported sills and three substantial service piers. Each crown carries a solid raised luggage pictogram and clearly sized `BAY 01`/`BAY 02` lettering on its actual front plane. The glyph and 6mm extruded lettering bear into their crown backing, with no coplanar print or hover gap. Each original 1.45m by 1.40m feed opening remains exactly clear; the metal sill stays below the existing opening.
- `SM_AP_Walls38`, `SM_AP_Floors38`, `SM_AP_Ceilings38`: scoped new finish materials and metre-projected source UVs; mesh vertices/faces and collision topology remain unchanged. Pale pearl circulation flooring has a 3mm low-contrast joint every2m; gate carpet is a muted blue-grey with broad pile variation. Plaster/ceiling patterns repeat over4m. No fine normal or noise pattern is used.

`make_textures43.py` is the editable deterministic source of the original seamless packed colour/roughness PNGs. These are math-authored surface maps, with no AI service, external artwork or scan. `Textures/*.png` are needed for source application and native import; the saved unit also packs them.

`native_finish43.py:apply_native(ctx)` imports those same PNGs, builds explicit editable Unreal material graphs, uses UV0 in source metres with1/tile scale, connects RGB to base colour and alpha to roughness, enables ordinary streamed mips, and binds by exact P43T material-slot name. It updates both saved mesh slots and actual component overrides. This avoids the existing common material path's base-colour-only fallback. Native validation is root's responsibility.

## Integration contract

1. Apply `Fixes/06_visual_finish43/finish43.py:apply` to the current Context after architecture flow39 has finished.
2. Fresh-export/import all five returned `asset_ids`; retain the original structural collision policies and keep the two finish actors `collision=False`.
3. Run `Fixes/06_visual_finish43/native_finish43.py:apply_native` after native placement. Save the root map normally.
4. Recapture gameplay 01,02,03,13,17,19,23,26,38 and55, then inspect moving views for texture shimmer, panel/attachment overlap and clear belt transfer. Source previews cannot approve Unreal appearance.

No changes to room dimensions, portals, interaction names/points, collision geometry, aircraft or characters are permitted by this pass. `repair38.terminal_finish43_v1` makes repeat application register/reuse its saved assets instead of duplicating instances or geometry.

## Evidence and status

`source_unit43.py` appends only the relevant current terminal collections into a private factory-empty process, uses fixed inspection lighting, and saves `TerminalFinish43_UnitKit.blend` before any after rendering. It checks source-master hash, unchanged zones/portals/service openings/interactions, repeat-safe part/instance counts, and no finish vertices inside either service aperture. Six baseline views were retained; final source comparison uses three key pairs (baggage, A08 and café). `Source43Report.json` records actual completed checks. Its pictures are genuine source renders, clearly not native gameplay.

Completed source verification is recorded in `Source43Report.json`: editable source kit saved and actually reopened; 298 broad cassettes/596 total finish parts across the entire public/exterior opaque-wall kit; both service openings clear in18 geometric ray probes through the actual evaluated shell+finish; all7 packed colour/roughness graphs present with physical scale; repeat application after reopen leaves geometry/actors unchanged. Original master SHA remains `80049b883f8bda5eea272b71eaa71bd16132dd51d4de0c17a10b872f1ba927a5`.

Viewed the genuine reopened baggage/A08/café source comparison images. Baggage now has fitted service bays, A08 has broad plaster/timber wall rhythm and blue-grey carpet, and café dado/floor/ceiling now share the quieter material hierarchy. These images precede the final, identity-only addition of the two luggage glyphs and bay numbers. The final kit is rebuilt and actually reopened without another image run; the added evaluated geometry is checked for physical bearing on the crown and full clearance above the feed openings. The existing glazed source environment looks darker than native gameplay in these inspection lights; these images are not engine lighting approval. The deliberately quiet3mm floor joint is subordinate at this camera distance.

Native material graph execution and gameplay images remain pending root integration; Python syntax checks and source renders do not establish in-game success.
