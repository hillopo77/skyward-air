# Flow39 architectural construction and room-flow refinement

`flow39.apply(ctx)` operates on the current saved assembly. It does not open,
reset, save or export a shared project, launch an editor, or change aircraft,
equipment placement, interactions, room footprints or lighting authority.

The module is idempotent through `D.repair38.architecture_flow39_v1`. It reuses
the existing derived structural collection IDs and registers all changed source
kits in `a.ASSETS`. An optional evidence callback records every construction pass.

## Five completed source passes

1. **Structural reconstruction.** Rebuild the exact whole-shell solid union from
   CURRENT room cells, true portals and service openings. Include the 29 shared
   unequal-height roof steps previously misclassified as internal. Integrate the
   gallery soffit side into that union and remove the separate attachment plates.
   Merge pane intervals and build all 67 frame solids through a single global
   union, replacing duplicated corner/transom faces with one 420-face glazing kit.
2. **Natural opening proportions.** Preserve the sectioned airport and offset
   route. Widen foyer-to-check-in from 1.9m to 2.6m. Build real curved corner solids
   inside six apertures: broad symmetrical A07, wider asymmetric A08, asymmetric
   café turn, open recovery release and a quieter smaller WC threshold. Central
   headroom remains 2.8–3.4m, rather than lowering ceilings into the walking path.
3. **Modeled fit and construction detail.** Continuous U-section reveals follow
   the real aperture curves. Fit separate captured insets, protective luggage-base
   sockets and a supported café arrival ledge; remove obsolete posts. Warm oak,
   navy and restrained metal distinguish destinations without adding extra arches.
4. **Route hierarchy.** Replace crossing route-strip joins with one welded mitered
   gold inlay. Add one mounted A08 cue at the actual north decision point. Retitle
   the existing café plaque CLOUD NINE, retain its service subtitle and add a
   captured north-turn chevron. No central directory or repeated café boards.
5. **Independent assembly fit and scrutiny.** Repair 12 socket/masonry same-plane
   interfaces while preserving at least 1.786m clear WC width. Remove the obsolete
   floating café title and 18 orphan direct scene FONT objects absent from current
   D.labels. Fit 18 risers to the actual tread undersides; preserve rise/run/landing
   and navigation data. Seat gallery-table bases on carpet top 3.1655m. Fit the
   retained canopy soffit into the wall center and columns into real shoes. Bound
   older thin-plate bevels by actual thickness, weld collapsed capsule endpoints
   and remove zero-area geometry in retained craft/gallery kits.

## Finding mapping

| Finding | Actual repair | Verification |
|---|---|---|
| AT11 shared-boundary roof-step gaps | Infill included before global union/owner split | Original proof ray plus 29 independent step rays blocked |
| AT12 duplicated Glazing38 frame faces | Merge panes, globally union every frame solid | Original 25 candidates reduced to zero; glazing explicitly included |
| AT08 open gallery soffit | Fascias remodeled into shell union | Existing source closure retained without separate overlap surfaces |
| AT13 gallery same-plane stair contacts | Risers end 130mm below tread top, beneath actual tread body | Expanded all-part checker includes GalleryStair35 |
| Independent café text overlap | Delete obsolete retained title; reconcile 18 retired direct labels | Final café/concourse views; source FONT list recorded |
| Thin retained mesh defects | Fit bevel radii and weld zero-length capsule endpoints | Nondegenerate evaluated meshes across retained craft and gallery |
| Generic portal repetition | Six differentiated actual openings with fitted continuous reveals |12 physical aperture/head-corner probes and final source previews |

## Integration

Export these 11 registered families from the patched current master:

- SM_AP_Floors38
- SM_AP_Ceilings38
- SM_AP_Roofs38
- SM_AP_Walls38
- SM_AP_Glazing38
- SM_AP_Attachments38
- SM_AP_Wayfinding38
- SM_AP_RetainedCraft38
- SM_AP_GalleryStair35
- SM_AP_Transitions39
- SM_AP_RouteHierarchy39

The first 9 update existing families. Add the two new actors from final D.instances:
`Airport39 fitted room transitions` and `Airport39 restrained route hierarchy`.
Regenerate native FONT templates for changed/new kits. Remove obsolete collision
proxies for the replaced shell/glass families and use their actual mesh collision;
the fitted transition kit uses complex collision. Wayfinding/route and the retained
gallery kit remain collision-none, preserving the existing stair navigation floors.

No role-based fixture or native light/post-process settings are changed. The
new P39F material family avoids collisions with the other fix modules.

## Evidence and limits

`Validation39.json` is the machine-readable result. `Coplanarity39.json` checks
actual evaluated active instances across the rebuilt shell, glazing, transitions,
wayfinding, attachments, retained craft and gallery. Its zero-candidate result is
scoped to those architectural families; it is not a blanket claim about all
equipment, characters or aircraft geometry.

The validator checks 48 physical source probes, idempotence, finite/nonzero faces,
unchanged room footprints, unchanged interaction records and unchanged master SHA.
Eight PNGs are genuine Blender source renders: five pass views and three final
views. They are construction previews with local QA lighting, without runtime
characters/UI; they are not Unreal gameplay screenshots or final engine lighting
sign-off. Parent must import the target kits and inspect actual gameplay scale,
material/text clarity, collision and route continuity in Unreal.
