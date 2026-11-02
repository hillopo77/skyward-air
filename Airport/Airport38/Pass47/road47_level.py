"""Pass47: carry the forecourt road on to the edge of the map (-run=pythonscript).

The access road (Asphalt12_1804, 6 m wide, y -37..33) stops in the grass at
both ends; from the overview and the flight camera it reads as a strip laid
on a lawn. Final47 traced the ground along its centreline every 10 m from
y -600 to +800: flat at z -0.08 the whole way, nothing in the way. So the same
asphalt continues south to y -600 and north to y +800 at exactly the existing
road's height and width - nothing more invented than the road itself.

MUTATES AND SAVES the level.
"""
import unreal as u, json, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAP = '/Game/Airport38/L_Airport_Repair38'
R = dict(status='RUNNING', placed=[])
RUNS = [('Access road south47', -600.0, -37.0), ('Access road north47', 33.0, 800.0)]


def main():
    assert u.EditorLoadingAndSavingUtils.load_map(MAP)
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    EA = u.get_editor_subsystem(u.EditorActorSubsystem)
    road = next(a for a in EA.get_all_level_actors() if a.get_actor_label() == 'Asphalt12_1804')
    rc = road.static_mesh_component
    loc, scale = road.get_actor_location(), road.get_actor_scale3d()
    R['source'] = dict(location_m=[loc.x / 100, -loc.y / 100, loc.z / 100],
                       scale=[scale.x, scale.y, scale.z], yaw=road.get_actor_rotation().yaw)
    for label, y0, y1 in RUNS:
        a = EA.spawn_actor_from_class(u.StaticMeshActor,
                                      u.Vector(loc.x, -(y0 + y1) / 2 * 100, loc.z),
                                      road.get_actor_rotation())
        a.set_actor_label(label)
        a.set_folder_path('Airport38/Pass47/Forecourt')
        # The mesh is a 1 m unit slab; the road's own scale carries width and
        # depth, so only the length changes.
        a.set_actor_scale3d(u.Vector(scale.x, (y1 - y0), scale.z))
        c = a.static_mesh_component
        c.set_static_mesh(rc.static_mesh)
        for i in range(rc.get_num_materials()):
            c.set_material(i, rc.get_material(i))
        c.set_mobility(u.ComponentMobility.STATIC)
        c.set_collision_enabled(u.CollisionEnabled.QUERY_AND_PHYSICS)
        c.set_collision_profile_name('BlockAll')
        o, e = a.get_actor_bounds(False)
        R['placed'].append(dict(actor=label, y=[y0, y1], bounds_y_m=[round(-(o.y + e.y) / 100, 1), round(-(o.y - e.y) / 100, 1)],
                                top_z_m=round((o.z + e.z) / 100, 3), width_m=round(2 * e.x / 100, 2)))
    assert u.EditorLoadingAndSavingUtils.save_map(world, MAP), 'save_map failed'
    R['status'] = 'SUCCESS'


try:
    main()
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'Road47.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
print('ROAD47', R['status'])
