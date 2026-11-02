"""Pass48: which material asset (path, parent, textures, scalars) each architecture slot really uses. Read-only."""
import unreal as u, json, traceback
from pathlib import Path
HERE = Path(__file__).resolve().parent
R = dict(status='RUNNING', slots=[])
WANT = ('Airport38 coherent', 'Airport38 complete', 'Airport43', 'Airport38 role-based', 'Airport38 exterior glazing',
        'Airport38 retained', 'Airport38 verified', 'Airport39', 'Airport38 mounted', 'Finished Grounds34', 'Slab12_1')
try:
    assert u.EditorLoadingAndSavingUtils.load_map('/Game/Airport38/L_Airport_Repair38')
    ML = u.MaterialEditingLibrary
    for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
        if not a.get_actor_label().startswith(WANT):
            continue
        c = a.get_component_by_class(u.StaticMeshComponent)
        for i in range(c.get_num_materials()):
            m = c.get_material(i)
            row = dict(actor=a.get_actor_label(), slot=i, path=m.get_path_name() if m else None)
            if isinstance(m, u.MaterialInstance):
                p = m.get_editor_property('parent'); row['parent'] = p.get_path_name() if p else None
                row['scalars'] = {str(n): ML.get_material_instance_scalar_parameter_value(m, n) for n in ML.get_scalar_parameter_names(m)}
                row['textures'] = {str(n): (lambda t: t.get_path_name() if t else None)(ML.get_material_instance_texture_parameter_value(m, n)) for n in ML.get_texture_parameter_names(m)}
                v = {}
                for n in ML.get_vector_parameter_names(m):
                    c4 = ML.get_material_instance_vector_parameter_value(m, n); v[str(n)] = [round(c4.r, 3), round(c4.g, 3), round(c4.b, 3)]
                row['vectors'] = v
            R['slots'].append(row)
    R['status'] = 'SUCCESS'
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'MatPaths48.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
