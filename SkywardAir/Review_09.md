# Aircraft revision09 — review build

The latest request rejected the bulky exterior and the cabin's quality. This revision changes the large forms and replaces passenger finish components. Visual approval is pending.

| Dimension | Previous exterior08 | Current09 |
|---|---:|---:|
| Body width | 6.10m | 5.00m |
| Body height | 6.40m | 4.70m |
| Overall length | 32.95m | 39.992m |

The cabin is about 4.80m wide, with two approximately 0.75m economy aisles. Four grey window-side business seats keep the centre clear. Economy has 40 seats in ten 1–2–1 rows; four added rows fill the longer cabin. Passenger seat sizes are retained and side assemblies move inward 20cm. Main galley remains between classes, and both aft lavatories remain.

New work includes the continuous nose/glazing surface, fitted lower pressure section and tail, thinner window reveals, shaped luggage/service housings, sectional grey/blue upholstery, formed premium consoles, corrected engine supports and aligned carpet. Cushion end caps use closed quad grids to remove the earlier subdivision pinching. Inherited roof/partition/cove/support protrusions were fitted to the new body.

## Verified locally

- 49 source geometry checks passed, including basin interiors, real throttle gate openings, skin coverage and 15 closed quad cushion cages.
- 2,580 pressure-skin rays passed outside intended apertures.
- 1,645,480 evaluated interior vertices were checked against the constant main body envelope with 3mm tolerance; no outliers. This includes actual bevel/subdivision results and excludes intentional exterior assemblies and the tapered nose/tail.
- Native import and map reload succeeded. The final standalone run produced 15 genuine game screenshots, passed 21 interaction/API/view checks and 15 walking checks with 15 reposition checks.
- Portable and authoring Blender sources are synchronized. The original supplied README remains unchanged. No characters or paid generation were added.

## Review

Use `Review Exterior.cmd` for outside views or `Run Plane.cmd` for the cabin. V cycles review cameras and returns to walking; E operates the cockpit door and enters/exits pilot/business seats. `Plane.blend` is the editable source, and `Screenshots.html` contains the current views and genuine construction history.

This remains an uncooked editor-hosted walkthrough. Exterior gear wells/door mechanisms, finer aerodynamic transitions, material/type review, production UV/tangent cleanup and optimization remain unfinished. Curtains, recline, passenger door mechanisms, IFE content and flight systems remain static. It is not a packaged shipping game or an exact 767 reproduction.
