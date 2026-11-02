# Aircraft revision16 — bins, cargo and exterior

The overhead bins are approximately 4.8% deeper, extend 3.5cm farther inward and have a bottom lowered by3cm. Hinges remain at the top, their round geometry is preserved, and the leaves still lift upward. Attached passenger-service fittings move with the lower underbody. The central aisle and seating layout remain the same.

Revision15 introduced eleven individually constructed cargo families in118 placements: ribbed spinner cases, a checked case resting on four rear wear pads, tailored soft bags, folded cartons, a long mailer, a plywood freight chest and reinforced equipment cases. The read-only saved-mesh check measures their true support points, rack clearance and gaps. All118 touch their trays; no cargo was shrunk to fit. The cases laid flat bear on rear pads, with trolley grips clear of the tray.

| Cargo family | Actual dimensions, metres |
|---|---|
| CarrySpinner | 0.37 × 0.30 × 0.55 |
| CheckedSpinner | 0.51 × 0.39 × 0.78 |
| CheckedLaid | 0.51 × 0.78 × 0.39 |
| Weekender | 0.34 × 0.47 × 0.35 |
| ExpeditionDuffel | 0.43 × 0.88 × 0.48 |
| SmallParcel | 0.26 × 0.31 × 0.19 |
| MediumParcel | 0.44 × 0.61 × 0.43 |
| LongMailer | 0.28 × 1.04 × 0.17 |
| PlywoodCrate | 0.50 × 1.06 × 0.55 |
| InstrumentCase | 0.36 × 1.11 × 0.24 |
| CrewEquipment | 0.48 × 0.63 × 0.41 |

The exterior has a revised forebody, wrapped white/gold/navy paint, broader wings with separate control surfaces, original airline marks, two hollow engine intakes with36 modeled fan blades each, and ten detailed tires across the two main bogies and twin-wheel nose gear. All ten tires meet the apron. A separate exterior review scene provides a ground reference. This remains a fictional aircraft; the existing custom interior is preserved.

Open `Run Plane.cmd` to play or `Run Exterior.cmd` to review the airframe. E/left click uses nearby fittings; **Space stands up**. Open `Plane.blend` to edit. Both editable source copies match. `Screenshots.html` contains 35 aircraft views, plus a link to earlier history.

## Focused verification

The current source was imported and saved successfully. Three representative changed bins passed selection, full opening and full closure (9 focused checks), with seven fresh game photographs. Independent saved geometry confirms the small bin drop and inward extension. The user requested that complete walking/all-fitting loops be skipped for this change.

The prior revision15 run is preserved without relabeling it as a revision16 pass. It recorded1483/1484 action expectations,24 standing routes/body checks and six door barriers with reopening. One legacy expectation that E immediately stands from the forward crew jumpseat failed; E can select nearby fittings, and Space remains the explicit stand control. The source cargo/exterior checks passed. Reports state their own source hashes and scope.

## Remaining gaps

Luggage is currently static scenery; pickup, packing and turbulence restraint simulation remain future work. Flight simulation, characters, story, multiplayer and appliance/avionics simulations remain outside this asset pass. The aircraft exterior still needs artist review and production optimization; these checks establish fit and behavior, not final visual approval. The walkthrough requires the existing local Unreal installation and is not a packaged shipping game.

No paid generation was used. The supplied style bible is preserved unchanged in `ArtBible/Original_Readme.md`.
