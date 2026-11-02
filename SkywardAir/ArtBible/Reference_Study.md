# Plane reference study — 23 October 2026

The complete 25-section README in `Original_Readme.md` is the visual and production source. The uploaded images are visual references, not hidden production specifications. All dimensions below are authored estimates; the screenshots do not reveal original meshes or exact measurements.

## Current user direction

Focus on the airplane. No new characters or first-person hands in the current scene. Match the supplied cabin/cockpit views closely, with modeled surfaces and construction detail. Preserve the older 767 2–3–2 and roomy 1–2–1 studies. Do not use Higgsfield or spend its credits.

## Observed features and implementation

| Supplied reference | Visible evidence | Current modeled treatment |
|---|---|---|
| Undamaged cabin, seated passengers at right | Saturated blue seat, separate headrest, white arm housing, brown cap, dark lower band, H-shaped metal supports | Shaped subdivided upholstery control cages; separate shell, arm profiles, cast legs, belt and buckle |
| Same cabin view | Rounded, slightly tapered windows, thick pale trim, lower sill above seat cushion | 0.79 × 0.965 m estimated clear opening; bottom 0.8875 m; seven surface loops form padded wall, rolled trim and deep reveal |
| Rack underside visible in cabin and damage views | Dark navy shelf underside; groups of three white rectangular lights; open storage above | Extruded shelf section, rounded retaining lip, arched supports, recessed three-light modules and small carry-ons |
| Cabin roof and end arch | Curved pale crown; repeated separate arch ribs; navy floor with pale binding lines | Quad barrel sections, separate ribs, carpet modules and narrow grid bindings |
| Isolated dashboard | Broad curved black wings, raised center console, left green radar, analog gauge cluster to right, six-toggle tray, yoke, four throttle slots | Curved tessellated panel mesh, individual recessed instruments, raised bezels, tick geometry, needles, glass, toggle stems, yoke and curved throttle sectors |
| Cockpit wide view | Blue/white pilot seats, wraparound glass, hanging aircraft monitor | Connected flightdeck, two seats, real transparent panes and posts, modeled hanging monitor with a newly drawn schematic |
| Rear cargo opening | Rear arch, illuminated EXIT, open metal ramp | Open rear area, arched frame, ramp, hinges/edge details and raised tread |
| Exterior shots | Pale hull, blue lower band, narrow gold stripe, visible wing and landing gear | A new compact outer skin fitted around this cabin, airfoil wings and stabilizers, hollow nacelles/fans and modeled gear |

## README rules applied

- Credible environment construction and smooth silhouette rather than a faceted blockout.
- Neutral architecture, saturated blue seating, navy carpet, controlled warm accent lights.
- Distinct material roughness for paint, upholstery, carpet, metal, glass and controls.
- Separate source geometry and modifiers retained; evaluated copies exported to FBX.
- Shared modular parts, metre-to-centimetre conversion, explicit cameras and repeatable Unreal assembly.
- Blender previews and Unreal captures are labeled separately. Final art acceptance is not inferred from a successful import.

## Current limitations

The current scene is a reference-led **1–1 cabin study**, with eight rows plus two cockpit seats. The previously requested 1–2–1 and 767 layouts remain available as separate scenes; they have not yet received this full new detail pass. The exterior, hatch mechanisms, exact cockpit silhouette, surface detailing and reference lighting still need further visual refinement. No claim of a measured 1:1 reconstruction is made. There is no flight simulation, story, animated crew, service interaction, damage system or multiplayer implementation in this art revision. The Unreal walkthrough uses a fixed-height collision sphere and simple hidden wall bounds; it is not yet a full physical character controller.

## External asset

Sky only: [Kloofendal 48d Partly Cloudy (Pure Sky), Poly Haven](https://polyhaven.com/a/kloofendal_48d_partly_cloudy_puresky), Greg Zaal / Jarod Guest, CC0. The downloaded 2K HDR file is included in `SourceAssets/Textures`. Models and the fine weave normal were authored locally; no screenshot pixels are used as model textures. Higgsfield spend for this task: zero.
