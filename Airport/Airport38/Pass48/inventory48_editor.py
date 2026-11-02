"""Pass48: full read-only inventory of the level for the makeover (-run=pythonscript).

Every actor (label, class, folder, source-metre bounds, mesh, material slots),
every instanced component (mesh, count, every instance's position and yaw),
and the parameters of the master materials the architecture uses, so the
makeover is planned against what is really there.
"""
import unreal as u, json, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAP = '/Game/Airport38/L_Airport_Repair38'
R = dict(status='RUNNING', actors=[], ism=[], masters={})


def src_bounds(o, e):
    return [round((o.x - e.x) / 100, 3), round((o.x + e.x) / 100, 3),
            round(-(o.y + e.y) / 100, 3), round(-(o.y - e.y) / 100, 3),
            round((o.z - e.z) / 100, 3), round((o.z + e.z) / 100, 3)]


def main():
    assert u.EditorLoadingAndSavingUtils.load_map(MAP)
    EA = u.get_editor_subsystem(u.EditorActorSubsystem)
    masters = set()
    for a in EA.get_all_level_actors():
        try:
            o, e = a.get_actor_bounds(False)
            row = dict(label=a.get_actor_label(), cls=a.get_class().get_name(),
                       folder=str(a.get_folder_path()), b=src_bounds(o, e))
            smc = a.get_component_by_class(u.StaticMeshComponent)
            if smc and smc.static_mesh and not isinstance(smc, u.InstancedStaticMeshComponent):
                row['mesh'] = smc.static_mesh.get_name()
                mats = []
                for i in range(smc.get_num_materials()):
                    m = smc.get_material(i)
                    mats.append(m.get_name() if m else None)
                    if m and isinstance(m, u.MaterialInstance) and m.get_editor_property('parent'):
                        masters.add(m.get_editor_property('parent').get_path_name())
                row['mats'] = mats
                row['coll'] = str(smc.get_collision_enabled())
                row['vis'] = smc.is_visible()
            R['actors'].append(row)
            for c in a.get_components_by_class(u.InstancedStaticMeshComponent):
                m = c.get_editor_property('static_mesh')
                if m is None or c.get_instance_count() == 0:
                    continue
                inst = []
                for i in range(c.get_instance_count()):
                    t = c.get_instance_transform(i, True)
                    inst.append([round(t.translation.x / 100, 3), round(-t.translation.y / 100, 3),
                                 round(t.translation.z / 100, 3), round(t.rotation.rotator().yaw, 1),
                                 round(t.scale3d.x, 3), round(t.scale3d.y, 3), round(t.scale3d.z, 3)])
                bb = m.get_bounding_box()
                R['ism'].append(dict(actor=a.get_actor_label(), mesh=m.get_name(), count=len(inst),
                                     mesh_box_cm=[round(bb.min.x), round(bb.max.x), round(bb.min.y), round(bb.max.y),
                                                  round(bb.min.z), round(bb.max.z)],
                                     mats=[(c.get_material(i).get_name() if c.get_material(i) else None)
                                           for i in range(c.get_num_materials())],
                                     instances=inst))
        except Exception as exc:
            R.setdefault('errors', []).append(str(exc)[:200])
    ML = u.MaterialEditingLibrary
    for path in sorted(masters):
        m = u.load_asset(path)
        try:
            R['masters'][path] = dict(
                scalars=[str(n) for n in ML.get_scalar_parameter_names(m)],
                vectors=[str(n) for n in ML.get_vector_parameter_names(m)],
                textures=[str(n) for n in ML.get_texture_parameter_names(m)],
                switches=[str(n) for n in ML.get_static_switch_parameter_names(m)])
        except Exception as exc:
            R['masters'][path] = str(exc)[:200]
    R['status'] = 'SUCCESS'


try:
    main()
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'Inventory48.json').write_text(json.dumps(R), encoding='utf-8')
print('INVENTORY48', R['status'], len(R['actors']), len(R['ism']))
