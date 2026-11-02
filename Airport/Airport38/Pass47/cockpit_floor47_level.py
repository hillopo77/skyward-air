"""Pass47: give the cockpit a floor that physics bodies can land on.

Floor47 mapped the parked aircraft with simple-collision down-traces on a
10 cm grid. Aft of y=0 the fitted carpet is a solid floor. Across the whole
cockpit (y -5.4..0) there is none: the only floor is SM_Plane_CockpitShell's
complex mesh 10 cm below walking level, and simulated bodies use simple
collision. A bag dropped there falls out of the aircraft - the Pass47 journey
failure ("Dropped bag lost moving-frame support"); earlier runs passed only
because their bag happened to land aft of y=0.

The fix follows the aircraft's own idiom: hidden COL_ cube proxies, which
flight39_frame.bind() attaches to the aircraft carrier by label prefix so they
fly with it. One more, top exactly at floor level, under the cockpit floor
only (x 14.05..17.95, y -5.0..0.05, z -0.10..0.00).

MUTATES AND SAVES the level.
"""
import unreal as u, json, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAP = '/Game/Airport38/L_Airport_Repair38'
BOX = dict(x=(14.05, 17.95), y=(-5.0, 0.05), z=(-0.10, 0.0))
LABEL = 'COL_CockpitFloor47'
R = dict(status='RUNNING')


def main():
    assert u.EditorLoadingAndSavingUtils.load_map(MAP)
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    EA = u.get_editor_subsystem(u.EditorActorSubsystem)
    acts = {a.get_actor_label(): a for a in EA.get_all_level_actors()}
    if LABEL in acts:
        EA.destroy_actor(acts[LABEL])
    tmpl = acts['COL_ObserverSeat']
    carrier = acts['Flight39 Aircraft carrier']
    tc = tmpl.static_mesh_component
    mesh = tc.static_mesh
    mb = mesh.get_bounding_box()
    half = [(mb.max.x - mb.min.x) / 2, (mb.max.y - mb.min.y) / 2, (mb.max.z - mb.min.z) / 2]
    cx, cy, cz = [(BOX[k][0] + BOX[k][1]) / 2 for k in ('x', 'y', 'z')]
    sx, sy, sz = [(BOX[k][1] - BOX[k][0]) * 100 / 2 / h for k, h in zip(('x', 'y', 'z'), half)]
    a = EA.spawn_actor_from_class(u.StaticMeshActor, u.Vector(cx * 100, -cy * 100, cz * 100), u.Rotator(0, 0, 0))
    a.set_actor_label(LABEL)
    a.set_folder_path(str(tmpl.get_folder_path()))
    a.set_actor_scale3d(u.Vector(sx, sy, sz))
    c = a.static_mesh_component
    c.set_static_mesh(mesh)
    c.set_mobility(u.ComponentMobility.MOVABLE)
    # A floor blocks everything. Copying the template's 'Custom' profile by
    # name would not carry its per-channel responses, so be explicit.
    c.set_collision_enabled(u.CollisionEnabled.QUERY_AND_PHYSICS)
    c.set_collision_profile_name('BlockAll')
    c.set_visibility(False, True)
    a.set_actor_hidden_in_game(True)
    a.attach_to_actor(carrier, u.Name(''), u.AttachmentRule.KEEP_WORLD, u.AttachmentRule.KEEP_WORLD,
                      u.AttachmentRule.KEEP_WORLD, False)
    o, e = a.get_actor_bounds(False)
    R.update(actor=LABEL, template='COL_ObserverSeat', mesh=mesh.get_name(),
             profile=str(c.get_collision_profile_name()), enabled=str(c.get_collision_enabled()),
             parent=a.get_attach_parent_actor().get_actor_label() if a.get_attach_parent_actor() else None,
             bounds_m=dict(x=[round((o.x - e.x) / 100, 3), round((o.x + e.x) / 100, 3)],
                           y=[round(-(o.y + e.y) / 100, 3), round(-(o.y - e.y) / 100, 3)],
                           z=[round((o.z - e.z) / 100, 3), round((o.z + e.z) / 100, 3)]))
    assert u.EditorLoadingAndSavingUtils.save_map(world, MAP), 'save_map failed'
    R['status'] = 'SUCCESS'


try:
    main()
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'CockpitFloor47.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
print('COCKPITFLOOR47', R['status'])
