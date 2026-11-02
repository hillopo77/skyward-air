"""Pass47: turn the taxis and the shuttle to the kerb (-run=pythonscript).

With the road painted it shows: the three taxis and the shuttle all stand
broadside across the 6 m road (mesh length is local Y, instance yaw -90 lays
it along world X), noses east into the kerb, blocking both lanes; the 9 m
shuttle overhangs the grass. They are turned to UE yaw 180 (nose north,
source rotation_degrees 180), the kerb lane for northbound traffic on this
side, and pulled in so the east side stands 0.30 m inside the kerb edge
(x -62.0), keeping each y. Footprints come from each mesh's own bounds.
They are instances in 'Airport instanced architecture and fittings';
nothing else references them (layout records are updated alongside).
MUTATES AND SAVES the level.
"""
import unreal as u, json, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAP = '/Game/Airport38/L_Airport_Repair38'
KERB_X, CLEAR = -62.0, 0.30
YAW = 180.0
MESHES = ('SM_AP_TaxiCar', 'SM_AP_ShuttleBus')
R = dict(status='RUNNING', moved=[])


def main():
    assert u.EditorLoadingAndSavingUtils.load_map(MAP)
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    EA = u.get_editor_subsystem(u.EditorActorSubsystem)
    host = next(a for a in EA.get_all_level_actors()
                if a.get_actor_label() == 'Airport instanced architecture and fittings')
    for c in host.get_components_by_class(u.InstancedStaticMeshComponent):
        m = c.get_editor_property('static_mesh')
        if m is None or m.get_name() not in MESHES:
            continue
        box = m.get_bounding_box()
        for i in range(c.get_instance_count()):
            t = c.get_instance_transform(i, True)
            x0 = t.translation.x / 100
            if not -70 <= x0 <= -60:
                continue
            sc = t.scale3d
            rot = u.Rotator(0, 0, YAW)
            q = rot.quaternion()
            xs = [q.rotate_vector(u.Vector(px * sc.x, py * sc.y, 0)).x / 100
                  for px in (box.min.x, box.max.x) for py in (box.min.y, box.max.y)]
            ys = [q.rotate_vector(u.Vector(px * sc.x, py * sc.y, 0)).y / 100
                  for px in (box.min.x, box.max.x) for py in (box.min.y, box.max.y)]
            assert max(xs) - min(xs) < 3.2 and max(ys) - min(ys) > 4, ('footprint not along the road', xs, ys)
            nx = (KERB_X - CLEAR) - max(xs)
            t2 = u.Transform(u.Vector(nx * 100, t.translation.y, t.translation.z), rot, sc)
            assert c.update_instance_transform(i, t2, True, True, True)
            dx = nx - x0
            R['moved'].append(dict(mesh=m.get_name(), index=i, y=round(-t.translation.y / 100, 2),
                                   from_x=round(x0, 3), to_x=round(x0 + dx, 3),
                                   width_m=round(max(xs) - min(xs), 2), length_m=round(max(ys) - min(ys), 2),
                                   from_yaw=round(t.rotation.rotator().yaw, 1), to_yaw=YAW))
    assert len(R['moved']) == 4, R['moved']
    assert u.EditorLoadingAndSavingUtils.save_map(world, MAP), 'save_map failed'
    R['status'] = 'SUCCESS'


try:
    main()
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'Kerb47.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
print('KERB47', R['status'])
