# Airport38 fix integration contract

Five read-only reviews precede five separate fix assignments. Each fixer owns only its numbered folder. Root alone assembles the saved master and imports/runs the shared Unreal project. Do not spawn further agents, edit existing baseline files, launch shared Unreal sessions or alter the live Blender scene. A small independent Blender test using factory-empty data in your own folder is allowed.

Each authored source module exposes `plan(ctx)` and/or `build(ctx)`. Root calls all plans first, then model builds with architecture last, in one Blender process. Use original coherent modeled geometry, rounded profiles, supported hardware and genuine apertures. Avoid merely putting a new cover over defective existing construction.

`ctx` has:

- `a`: existing airport_model helper module; MATS mapped to saved source materials, ASSETS holds only new exports. `a.asset(name, callback, collision='complex')`, box/pill/profile/loft/tube/cyl/ring/font are available. Assets have full IDs `SM_AP_`+name; shape data uses source metres. Materials registered with `a.mat(short_name, hex, roughness, metalness=0, emission=0, glass=False)`.
- `D`: mutable current airport_layout dictionary, initially copied from Clarity37. `before`: independent baseline dictionary. `scene`: saved complete Blender scene. `R`: Airport38 output root. `A`: Airport output parent. `P`: UnrealProject/Content/Python path.
- `ctx.replace(name, asset)`: change an existing instance's asset and source collection link, retaining pose.
- `ctx.move(name, location, rotation=None, scale=None)`: move an airport instance and rotate/move all associated interaction points and parent labels. Rotation is source degrees around Z.
- `ctx.remove(name)`: remove airport instance and attached airport interactions/labels/source instance. Do not remove unrelated furniture.
- `ctx.add(asset, name, location, rotation=0, scale=None, collision=True, **extra)`: add instance and source collection instance; asset may be existing or newly built. Stage defaults10.
- `ctx.new_collection(name, collision='complex')`: create and register new asset collection, make it a.ACTIVE; for copying carefully selected source parts use explicit copies with data copies, never mutate an inherited source asset.
- `ctx.require(name)` returns the mutable instance dictionary or fails.

Plans may change zones/portals/floors/conveyors and add service openings. Record important authored dimensions under D['repair38']; do not mutate shared baseline exports. Wall service apertures use `D['service_openings38']` entries `{axis:'y',k:-26,centre:-13,width:1.25,z0:.65,z1:1.65}`; axis follows existing wall segment convention. Architecture builds true cutouts from those final parameters.

Native hooks may expose `apply_native(ctx)` in a separate file. Native ctx includes `u`, `EA` (EditorActorSubsystem), `D`, `K` (new export manifest), `B='/Game/Airport38'`, `actors` keyed by native label, `material(name)`, `mesh(asset_id)`, `v(source_point)`, `R`. Root applies them after common import and actor placement. Fresh import paths avoid inherited FBX section/material ordering.

Runtime files stay in your own folder and expose `install(G)` unless another entry is expressly needed. Root copies them to Content/Python and wires the38-only entry; legacy modes stay unchanged. Airside may expose `prepare_plane(P,D)` called after plane18_runtime.install and before P.configure/P.start. Translate absolute P.DATA coordinates, not P.vector, because vector converts both points and deltas. Airport floors are appended AFTER plane data preparation.

Source and native coordinate convention: Blender +Y north, Unreal -Y north; `v([x,y,z])=(100*x,-100*y,100*z)`. Plane position offset is source +X16m, unless clearance evidence requires another value. Never apply translations to dimensions, motion deltas, axes, quaternions or basis vectors.

Ownership:

1. Architecture/wayfinding: all terminal shell/floors/ceilings/roof ownership, physical perimeter seams, coherent A08 entrance, mounted legible signs, planter clearances and room fixtures. Rebuild from final zone footprints, not inherited mismatched caps. Preserve the warm entrance/check-in direction while repairing actual faults.
2. Equipment/modeling: check-in/boarding counters and targets, scanners and belt chassis/controls, supported consoles, detailed storage/shelf contents, bin openings, floating plant, café cabinet gaps. Add properly mounted emergency controls if feasible; gameplay semantics coordinated with5.
3. Airside: articulated fully enclosed jetbridge/docking cab, aircraft parked offset with exact point/data/native/source coordination, legacy service ramp removal, forward swept clearance and departure/interlock contract. Airport desks belong2. Navigation base policy belongs5.
4. Rendering/stability: one final rendering authority, AA/lighting roles/fill/shadow consistency, accurate runtime status, temporal/coplanar validation. Do not hide structural defects with AA. Vehicle parking may be coordinated with3/5.
5. Journey/function: authoritative door permissions and WC locking, queue availability, real baggage transfer/storage continuation and scan state, honest A08 target/UI, bounded navigation floors and complete interaction verification. Coordinate geometry/holes with1/2, and translated aircraft crossing with3.

Deliver a concise implementation report mapping every assigned finding ID to code/assets and acceptance tests. Distinguish implemented work from work requiring root's native validation. Do not claim in-game success from Python compilation alone.
