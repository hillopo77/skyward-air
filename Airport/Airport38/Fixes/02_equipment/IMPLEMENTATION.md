# Equipment38 implementation and handoff

`equipment38.py` exposes `plan(ctx)` and `build(ctx)` under the shared contract. It replaces equipment assemblies rather than covering malformed inherited construction. It does not edit the baseline or launch a shared editor. `native38_equipment.py` exposes the small post-import plant attachment hook.

The editable library and three images are isolated Blender reviews, not native airport screenshots. The final shared Unreal import, actual interaction rays, journey simulation and temporal comparisons belong to root's integration validation.

| Finding | Implemented source change | Acceptance evidence and remaining native check |
|---|---|---|
| EQ01 | New supported Belt38 input chassis and accessible controls. Belt01, its conveyor rectangle, load point and adjacent desk/crew/queue approach move together to y=-13 / desk y=-11.6. Belt02 remains y=-16. | Positions align with fix1's x=-26 service openings. Fix5 owns the continuation, transfer and end-of-belt acceptance. Native bags must visibly travel through both openings before accepted/stored. |
| EQ02 | Separate EmergencyStop38 has a captured side clamp, cantilever, sealed yellow base, black bezel and circular revolved mushroom. Its cap is ahead of the scanner shoulder. Green START is separately mounted at the input. | Source envelope check proves clearance. Four `equipment_toggle` targets name their actual conveyor. Root/fix5 must verify unobstructed rays and stop/restart force gating. |
| EQ03 | Whole lane02 moves 650 mm west: detector x=-40.4, scanner/belt x=-38.05. Arrow, trays, crossing rectangle, conveyor rectangle and targets follow. | Scanner envelope maxX=-36.64, giving550 mm inside wall face x=-36.09. Both lane crossing centres and detector/belt spacing are asserted. Root verifies walking and controls in final shell. |
| EQ04 | One monitor enclosure with dual display faces, one bolted side plate and continuous arm; shelf has triangular braces. No inherited foot, swivel stem or duplicate housing. | Genuine close source render reviewed. Root checks post-import support and screen section binding. |
| EQ05 | A07 complete desk moves to[-17.5,-1.15], crew to[-16.25,-1.15]. A08 is retained after clearance review. Operations desk moves to y14.2 with its staff chair north at y15.3 facing the desk. | A07 minimumY=-2.14 is770 mm inside wall face -2.91. Public reader targets are attached to each real desk. Root regenerates character proxies and checks service space. |
| EQ06 | Plant base sits at1.061 on ChargingTable24_1749's1.06 top; marks stowed and records support. Source is parented when scene objects exist. Native hook attaches KEEP_WORLD. | Position/support metadata checked. Root must run native support trace and call `apply_native(ctx)` after common placements. |
| EQ07 | Counter38 is an open-front carcass: formed cheeks, real closed back, shelves, stiles/rails, consistent narrow inset door reveals, retained pulls/hinges, continuous fixed fascia and rounded stone top. All five desks replaced. | Five replacements asserted; actual front/oblique source render reviewed. No old closed front face or curved panel crossing remains. Root checks final nearby walls/NPCs. |
| EQ08 | Real U-shaped scanner shell and dark interior liner. Separate visual hinged curtain has a continuous dark backing and depth-staggered overlapping flexible strips. No repeated bright open slit field; no coplanar roof overlay. | Projected strip coverage and stagger depths asserted, duplicate-face scan zero. A first-render seam was corrected with a single continuous shoulder/roof loft. Root/fix5 must animate visual curtains when baggage passes; fix4 validates moving/stationary native frame sequences. |
| EQ09 | StaffStorage38 contains modeled medical cases, folded blankets, charging radios, labeled binders and soft service kits. TravelStorage38 instead has travel publications, revolved bottles, shaped neck pillows and pouches. | Both editable prop families have recognizable silhouettes and actual shelf support heights. Source review image checked. Root checks visibility at player distance. |
| EQ10 | Four directly seated rails per shelf with retained clips; staff rails are inventory tag carriers. | Rail back overlaps shelf edge2.5 mm; no13 mm unsupported air. Both shelf variants asserted. |
| EQ11 | Recycling38 has genuine open outer shells, inward-facing liners, captured mouth rings, sealed internal bases, grounded feet and attached labels/pulls. | Top has no solid cap or fake black decal. Two liner/opening/base assemblies checked. Root must inspect a downward view after import. |
| EQ12 | Two waist-height tray stations at y=.55; tray stack bases .824 with36 mm nesting. Two grounded output roller stations continue y4.8→5.48. | Tray/cart heights asserted; conveyor bounds extend to the actual output. Root/fix5 verifies tray pickup/use and force support on Outfeed38. |
| EQ13 | Three full-depth scribed filler pilasters close the100 mm café cabinet joints, with matching toe pieces and backing closures; original functional doors remain clear. | Source filler bounds match the three exact joints. Root inspects front/oblique final café images. |

## Runtime contract for fix5

Read `D['repair38']['equipment']` after all builds. It supplies:

- `lane_centres`, `counter_reader_local`, `desk_positions`, `tray_stack_base`, `tray_nesting`.
- `belt_asset_ids=['SM_AP_Belt38','SM_AP_Outfeed38']`; include these and your continuation in the supported-on-conveyor mesh whitelist. Legacy code accepts only Belt/Carousel.
- Four `emergency_controls` and actual interaction records: `{kind:'equipment_toggle', actor:<label>, point:<cap>, conveyor:<exact D.conveyors name>}`. Stop/restart must gate real force transfer and retain state; no position-assigned baggage motion.
- Four separate `curtains`: actor label, hinge, local X axis, open angle, trigger rectangle and height range. They are visual-only, collision disabled; animate as baggage enters/leaves rather than blocking a physical bag with static collision.
- `output_stations` with the extended physical support rectangle and `.845` roller height.
- `scanner_open_tunnel`:1.28 m minimum width, belt top .845, inner ceiling1.984 and entrance header underside1.912.

Native screen material uses the existing `MI_AP_Screen` slot for runtime replacement. All other equipment materials are unique `MI_AP_P38E*`, avoiding name collisions with other fixers. Text is painted, not brightly emissive.

## Unit verification

Run the included `test_equipment38.py` with a separate factory-empty Blender process. `--geometry-only` skips renders. It writes `unit_geometry38.json`, `planned_equipment_layout38.json` and `Equipment38_Unit.blend` in this folder. It checks actual source bounds, open central scanner ray, single roof shell, grounded supports, cap clearance, strip coverage, shelf rail contact, true bin liners, coherent lane/queue placements, material names and all meshes for duplicate faces/nonfinite vertices.

The three `*_review.png` images are genuine renders of these source assemblies. They show equipment only; they must not be represented as the final playable map.

Final isolated run: **24 assertions passed,11 assets, zero within-part duplicate faces and zero nonfinite vertices**. All three source images were reviewed. Scanner shell seams and the small first-aid cross overlap found during review were corrected and rerendered. Python compilation passes for the source module, native hook and unit harness.
