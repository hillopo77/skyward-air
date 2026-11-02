# Interaction ease update14

The existing aircraft is easier to use. Its modeled layout, furniture, materials and walking geometry retain revision13.

- Visible door, luggage-bin and seat surfaces can select their action across the object, rather than only at one small marker.
- Small buttons, knobs and grips have wider aim tolerance and a little more reach. Directly aiming at a particular control still wins over nearby assistance.
- An unfolded crew-seat pan selects sitting when aiming at its seating surface; its side folding lever remains available.
- Physical aircraft walls still block selection. Shared centre-seat meshes resolve by the chair under the crosshair.
- Left-clicking empty space keeps the player seated. Space stands up; E also stands when looking away from usable equipment. Use prompts now mention E and click.
- Distant fittings are filtered before querying their native transforms. The coarse range includes the conservative authored door/hatch movement bounds.

## Recorded checks

`ArtBible/InteractionEase14.json` compares both selectors in the actual game world. All 438 exposed exact targets retain selection. Of 120 off-centre small-control attempts, 102 selected the intended control, compared with 59 previously. Of 64 inspection attempts, 64 selected the intended object, compared with 50 previously. Tests include three- and six-degree errors; in crowded areas aiming at a neighbouring physical object can correctly change selection. These measurements do not promise that every missed aim chooses the intended object.

`ArtBible/ActionValidation14.json` records 1,484 fresh action/API checks across the controls, inspectable objects, seats, displays and storage, plus six actual closed-door barrier and reopening checks. Three genuine native viewport captures are included. The wall and empty-click protections pass. Both reports identify the current runtime and saved source hashes.

The prior 24 walking/body routes, 76 source fits and six floor regressions remain separate revision13 evidence for the byte-identical model and unchanged floor functions. They were not rerun or relabelled as fresh14 walking tests. The earlier full report remains `ArtBible/EngineValidation.json`; its runtime hash identifies the previous selector. Current delivery checks are in `ArtBible/Delivery_Audit.json`.

## Play

Open `Run Plane.cmd`. Walk with W/A/S/D, aim the centre crosshair at a fitting, and use E or left click. Use Space to stand. Physical obstruction still matters: open an intervening door or oven front before reaching something behind it.

This remains the editable local Unreal walkthrough. Flight, story, characters, multiplayer and luggage pickup are still unfinished. No paid generation was used.
