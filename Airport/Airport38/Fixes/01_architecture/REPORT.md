# Architecture and wayfinding repairs

`architecture38.py` exposes `plan(ctx)` and `build(ctx)`. Root must call this plan with the other four plans, then build this module **last**, after the baggage module has supplied `D.service_openings38`. No shared editor or saved baseline was changed by this agent.

The implementation replaces the layered terminal shell rather than placing another cover over it. Its new collections are `SM_AP_Floors38`, `Ceilings38`, `Roofs38`, `Walls38`, `Glazing38`, `Wayfinding38`, `Fixtures38`, `Canopy38` and `RetainedCraft38`. All new materials use the separate `P38A` namespace.

| Finding | Implemented repair | Acceptance evidence |
|---|---|---|
| L01 | Remove Roof35, every Room37/Room34 decorative ceiling/floor generation, Ceiling24/Floor24, older Envelope27/Transitions27 and original indoor Roof12/Facade12/Pillar12 components. Rebuild one ceiling and one weather-roof union from final room cells; minimum ceiling-to-roof underside separation is 0.36 m. | Floor/ceiling/roof coverage assertions; native root must verify no surviving old actors or AP COLL proxies. |
| L02 | Generate the complete east WC exterior directly from the amenities boundary, including x=-14,y=-4.5..-3. | Independent physical source ray from [-15,-3.8,1] to [-12,-3.8,1] blocks. |
| L03 | Generate the complete west corridor/security perimeter rather than skipping legacy facade rows. | Physical source ray from [-48,-4.25,1] to [-50,-4.25,1] blocks. |
| L04 | Remove the sign spanning the staff doorway; place a small supported plaque beside it, outside the opening. | Door remains centered x=-46, width 1 m; plaque x bounds -47.57..-46.73. Root should inspect native doorway clearance. |
| L05 | WC identification mounts north of the actual doorway and faces west toward approaching passengers. | `D.repair38.marker_probes` records mounted center, facing normal, dimensions and text. |
| L06 | A08 has an integrated high header visible from the southern approach; both plants move away from its sign and the queue. | Marker at [-29,13.88,3.31], facing south. Plant positions [-31,17.4] and [-25,17.4] avoid benches/charging table. |
| L07 | Delete A08 foyer cell and its y18 wall, giving one lounge rectangle [-32,-24,14,34] and a 4.8 m entrance. | Source ray through y17..19 at x=-29 is clear. |
| L08 | Delete the freestanding four-band directory and obsolete floating Sign24 boards. Install mounted A07, cafe and WC cues, modeled arrows, and one final gold route. | Marker probes and route coordinates are available to root QA. Native text labels attached to removed actors are removed through ctx.remove. |
| L09 | Merge A07 arrival cell and lounge without an internal wall; preserve the cafe's intentional transition into a taller room. Warm timber/acoustic art and useful furniture are selectively copied, while their old structural skins and lamps are discarded. | Source ray across former A07 interior wall is clear. All 19 final footprint regions have one owner. |
| L10 | Add explicit authored coverage, route, critical camera points, perimeter rays and fixture roles. | `test_architecture38.py` and `test_result.json`; native integration/visual checks remain root-owned. |

The retained warm foyer/check-in art gets structural backing where the older inset lining had left small mounting gaps. Lights now have a visible downward opal lens, a housing physically touching its support, and explicit `role`, `temperature`, `casts_shadows`, `shadow_intent`, `direction` and lumens in `D.lights`. There is no index-based light-role assignment. The rendering agent retains final native lighting authority.

## Shared baggage/airside dimensions

- Baggage staff bay: [-26,-22,-18.5,-12]. Both x=-26 feed apertures come from the final `D.service_openings38`; there is no older check-in east skin behind them.
- Arrivals: main [-22,-14,-22,-12] and exit pocket [-25,-22,-22,-18.5], merged without a partition. The reclaim bounds supplied by root fit inside the main region.
- The old public-return rectangle overlapped the new service bay by 0.5 m². It is now main [-49,-26,-22,-18] plus connector [-26,-25,-22,-18.5], merged with no inner wall. The public exit portal is correctly assigned to `publicreturneast` at x=-25,y=-20.
- Staff bay door aperture: x=-22,y=-17.65,width1.15,height2.6. It is tagged staff-only; gameplay agent supplies/control the physical door leaf.
- Observation glazing: x=-22,y=-14.7,width2.4,z1.05..2.12. It is a real inset window with collision and a supported frame.
- A07 boarding aperture stays x=-14,y0.675,width2.7, preserving the airside agent's enclosed bridge dock.

## Verification performed

`test_architecture38.py` was run with ordinary Python and with a **factory-empty Blender 5.2.2** process. Both passed. The source test evaluates all created meshes, checks finite vertices and nonzero face areas, builds independent BVH collision trees, and physically repeats seven perimeter/passage/feed traces. It also samples 18 points through the two service apertures analytically.

The final footprint has **19 nonoverlapping regions, 118 owned cells, and 1696 m²**. Root's assembled Blender build must exercise the selective copying against the inherited source collections; the factory-empty test intentionally has none of those collections. Root must still validate native imports, material assignment, motion, door gameplay, retained furniture/sign sightlines, and screenshots. This report does not claim an in-game or final visual pass.

## Full-source overlap correction

Root's first assembled whole-source checker found same-facing coincident surfaces at the boxed wall corners and roof-edge risers, which the earlier ray/topology suite did not detect. The implementation now performs an **exact whole-shell rectilinear solid union** across floor, ceiling, weather roof and wall volumes. It emits only the union's exposed boundary, then assigns those faces back to the original structural asset owners. Buried intersections/contact faces are physically deleted; separate boxes have not merely been joined or renamed. The plenum infill is restricted to H+0.16..H+0.36, meeting the ceiling top and roof underside instead of repeating their depth intervals.

The six retained forecourt Roof12 modules had their own overlapping purlins/cassettes. They and their old columns are removed, replaced by one continuous supported `Canopy38` with six explicitly described down-facing practical lights. Threshold reveal bottoms extend 5 mm beneath the floor rather than repeating the wall's buried bottom plane.

The isolated suite now runs the rendering agent's **same** cross-part exact-polygon coplanarity checker in addition to the physical BVH ray probes. `coplanarity_test_result.json` is **PASS with zero candidates**, including the new canopy, wall, roof, ceiling, floor and wayfinding collections. All aperture/perimeter ray tests continue to pass. Root must rerun the checker on its reassembled complete source and validate the final native scene; this isolated result is not a claim of full-map visual success.
