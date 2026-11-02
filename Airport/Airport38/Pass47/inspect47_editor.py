"""Pass47 read-only editor inspection (-run=pythonscript). Nothing is saved.

  instances  Every InstancedStaticMeshComponent in the level: mesh, instance
             count, and each instance west of x=-49 (the forecourt), because
             Inventory46 listed actors, not the instances inside them - so a
             forecourt "with four actors" may still hold instanced scenery.
  materials  Parent and parameters of the ceiling and wall finish materials.
  lights     The "Ceiling bounce approximation" lights: type, intensity,
             direction, size - the existing attempt at lighting ceilings.
"""
import unreal as u, json, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAP = '/Game/Airport38/L_Airport_Repair38'
R = dict(status='RUNNING', instances=[], materials={}, lights=[])


def src(v):
    return [round(v.x / 100, 2), round(-v.y / 100, 2), round(v.z / 100, 2)]


def main():
    assert u.EditorLoadingAndSavingUtils.load_map(MAP)
    EA = u.get_editor_subsystem(u.EditorActorSubsystem)
    for a in EA.get_all_level_actors():
        try:
            label = a.get_actor_label()
        except Exception:
            continue
        for c in a.get_components_by_class(u.InstancedStaticMeshComponent):
            m = c.get_editor_property('static_mesh')
            n = c.get_instance_count()
            west = []
            for i in range(n):
                t = c.get_instance_transform(i, True)
                p = src(t.translation)
                if p[0] < -49.0:
                    west.append(dict(i=i, at=p, yaw=round(t.rotation.rotator().yaw, 1)))
            R['instances'].append(dict(actor=label, component=c.get_name(),
                                       mesh=m.get_name() if m else None, count=n,
                                       forecourt=west))
        if isinstance(a, (u.RectLight, u.SpotLight, u.PointLight)) and 'eiling' in label:
            lc = a.get_component_by_class(u.LightComponent)
            row = dict(actor=label, cls=type(a).__name__, at=src(a.get_actor_location()),
                       pitch=round(a.get_actor_rotation().pitch, 1),
                       intensity=round(float(lc.get_editor_property('intensity')), 2))
            for k in ('source_width', 'source_height', 'attenuation_radius'):
                try:
                    row[k] = round(float(lc.get_editor_property(k)), 1)
                except Exception:
                    pass
            R['lights'].append(row)
    MEL = u.MaterialEditingLibrary
    for name in ('MI_AP_P43TCeiling', 'MI_AP_P43TPlaster', 'MI_AP_P38ACeiling'):
        mi = u.load_asset('/Game/Airport38/Materials/' + name)
        if mi is None:
            R['materials'][name] = 'missing'
            continue
        row = dict(parent=mi.get_editor_property('parent').get_name() if mi.get_editor_property('parent') else None)
        row['scalars'] = {str(p): round(MEL.get_material_instance_scalar_parameter_value(mi, p), 3)
                          for p in MEL.get_scalar_parameter_names(mi)}
        row['vectors'] = {str(p): [round(x, 3) for x in MEL.get_material_instance_vector_parameter_value(mi, p).to_tuple()]
                          for p in MEL.get_vector_parameter_names(mi)}
        row['textures'] = [str(p) for p in MEL.get_texture_parameter_names(mi)]
        R['materials'][name] = row
    R['status'] = 'SUCCESS'


try:
    main()
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'Inspect47.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
print('INSPECT47', R['status'])
