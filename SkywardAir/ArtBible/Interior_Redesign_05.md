# Interior redesign 05 — work in progress

The supplied README was read completely and remains unchanged in Original_Readme.md. The user's latest review rejected revision04 as insufficiently detailed and modern, and explicitly requested rebuilding beyond small refinements. This redesign is **not approved final art**.

The current passenger layout has eight 1–2–1 rows, 32 passenger seats, two cockpit seats, 4.74m trim-floor width, 1.15m row pitch and approximately 0.76m clear aisles. Side seat/window dimensions were retained while the cabin widened. Front cross circulation, service space and cockpit access are modeled. The previous 1–1 study and cargo ramp are preserved in Versions/Mechanical_03; the rejected complete-layout prototype is preserved in Versions/Interior_04_Working.

The service suite contains two lavatories, two forward galleys and one aft galley, two crew jumpseats, a cockpit door and two front passenger-door liners. Galley insert chassis, stacked convection ovens, insulated doors, control strips/displays, cooling vents, captive latches, carrier extrusions, coffee brewer, dispensing nozzles, grate, wet worktop/basin, faucet, carts, caster forks/axles, cart retainers, narrow drawers and access panels are separate source components. The lavatories have real toilet and basin interiors, contoured side shells/counter, an entrance-facing service panel, seated faucet components/aerator, illuminated mirror cabinet, dispenser, paper holder/shield, waste flap, call/flush controls, ventilation, detector, grab rail and placards.

The new flightdeck uses six original vector flight displays (PFD, navigation, engine and status artwork), a mode-control panel with mounted readouts/encoders/keys, warning switches, EFIS controls, twin yokes/pedals, radio stack, side consoles and modular overhead systems. The previous genuine throttle gates, independent lever hubs and supported pivot shaft remain. Screen values are static artwork. This is an authored contemporary game aircraft, not an exact operational 767 flightdeck.

The cabin retains the blue/neutral/navy/brown reference palette, open racks and tailored upholstery. Continuous wrap-around headrest upholstery, rear device ports, tray end fittings, gasper nozzles with actual center openings, reading optics and call-button fittings add functional detail. An earlier detached-wing experiment was rejected during inspection and replaced. New equipment legends use packed editable Arial Narrow in Blender and native distance-field text in Unreal. Materials distinguish slate, graphite, composite counter, satin polymer and restrained metal; procedural microtexture supports those surfaces.

## Inspection record

- Revision04's generic galley and pedestal basin were rejected and replaced.
- A floating work-bay placard was removed; crew labels received a structural mount.
- Deep outer window tunnels were reduced while preserving the interior window dimensions.
- Galley/vanity counter support geometry was corrected so it does not fill the basins. InteriorGeometryChecks.json records actual rays to the basin bottoms, retained throttle through-slots, layout and label checks.
- A placement error in the new mode controls was corrected and an assertion checks the saved carrier height.
- Exterior nose-cap triangles intruding across the flightdeck brow were identified by scene rays and removed from the overlapping interior region.
- Bulk conversion of many selected control components was too slow. The exporter now assembles evaluated mesh data directly, including source material IDs and custom corner normals. Evaluated material references must resolve to original datablocks before reuse.
- The headrest wrap is a single continuous quad surface. Overhead legends were rotated into the pilot's reading direction. Counter openings use uniformly sampled smooth contours. Seat footprint bounds prevent the fixed-height art-tour sphere from clearing chairs.
- Native reimport clears obsolete slot tables before rebuilding sections; export includes only materials actually assigned to faces. This prevents removed monitor slots or unused cutter materials from invalidating the source-to-engine mapping.
- Runtime labels use native distance-field text, driven by the Blender wording, colour, dimensions and surface basis. The source keeps packed editable Arial Narrow; the game uses its built-in distance-field font fitted to those bounds. Thin static glyph triangles did not remain legible at gameplay size, so they are excluded from the current runtime mesh export. The first runtime lighting/collision check is archived under Versions/Interior_05_First_Runtime.

## Limits and remaining gaps

Visual approval remains pending. There is no claim of perfection or a measured 1:1 replica. Detailed service equipment is static art: no door/latch/control animations, running water, systems logic or flight simulation. Fixtures and services need eventual interaction/collision simplification, production UV/lightmap/tangent cleanup, LODs and performance measurements. The exterior is adapted to the wider passenger interior and still needs a dedicated silhouette, tail and door-skin pass. The existing airport and historical layout studies are retained without receiving this interior redesign.

Latest native-build, material-binding and navigation evidence is in UnrealBuildReport.json and EngineValidation.json; inspect their revision/status rather than treating historical screenshots as current validation. Blender and actual Unreal images are separated in Screenshots.html, including the rejected/intermediate images.

General service zoning was cross-checked against Boeing's published 767 airport-planning interior arrangements; the compact 1–2–1 game layout is authored rather than copied from that plan: https://www.boeing.com/content/dam/boeing/boeingdotcom/commercial/airports/acaps/767_REV_K.pdf
