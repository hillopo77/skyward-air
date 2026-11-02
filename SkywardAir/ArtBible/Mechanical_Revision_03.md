# Mechanical detail revision 03

The user specifically rejected rods disappearing into solid housings and loosely modeled buttons. This revision rebuilds the control interfaces as manufactured assemblies, keeping the accepted airplane layout and the README's visual direction.

## Rebuilt assemblies

- Four throttle arms pass through rounded, genuinely open slots in a curved metal gate cover. Each arm has a bored pivot hub and thrust washers on a transverse shaft, supported by bored bearing brackets and bronze bushings.
- Curved side cheeks and under-cover mounting flanges support the gate cover. Cover screws, recessed slot seals, graduations, retained brown grips and handle end fittings complete the visible assembly.
- The switch tray is hollow, with a separate removable lid, eight actual mounting bores and three through-cut ventilation slots. Toggle necks pass through the lid under washers and chamfered retaining nuts; rubber boots support the stems. Red button caps have guided necks, recessed bezels and separate collars.
- Rotary knobs have spindle collars, ridged bodies and index marks. The main selector has a bored mounting plate, retaining hardware, a hub and a keyed handle. Side pushbuttons have housing bores, guides and machined bezels.
- The yoke has a bolted floor flange, column boot, keyed axle, tilt housing and a front bearing connecting the column to the hand wheel. Hollow ergonomic sleeves follow its angled bow legs, preventing the black frame from protruding through straight grips.
- Weighted face normals preserve broad manufactured panel faces after cutting the bores. Export signatures include corner normals, so a shading-only edit is imported by Unreal too.

These are static modeled assemblies for the art scene. They are not yet animated controls, a flight simulation or a certified aircraft mechanism.

## Evidence and editing

`81_controls_seated_interfaces.png` shows the complete assembly. `82_throttle_gates_final.png` shows the actual lever openings. `83_pivot_bearings_exposed.png` is the same model with its covers and cover-mounted parts hidden for inspection; this diagnostic visibility state is not saved to the source. `84_cockpit_mechanical_final.png` shows the installed result. UE 22–27 are native engine captures of the saved revision, including dedicated control/gate close-ups.

`85_controls_surface_check.png` shows the subsequent panel shading cleanup. Current Unreal oblique camera directions are corrected to match Blender; prior archived engine angles were offset horizontally. The current gallery identifies earlier checks separately.

`MechanicalOpeningChecks.json` records ray tests through the four gate slots, switch/button mounting bores, tray vents and pivot bracket bores. Solid regions bordering the holes are tested too. This checks actual mesh openings rather than relying on dark surface patches.

Open `Plane.blend`, then choose `EDIT_Controls` to edit the real source parts. `model_control_mechanisms.py` reproduces this revision from `Versions/Quality_02/Plane.blend`. Saved edits can still be sent to Unreal with `Update Plane.cmd`; that command does not regenerate meshes. The previous broad model and quality revision remain preserved.

Remaining airplane work includes exterior/nose and cargo mechanism refinement, further material/lighting matching in the compatible Unreal renderer, production UV/tangent cleanup, collision simplification and LOD/performance work. No new characters or paid generations were added.
