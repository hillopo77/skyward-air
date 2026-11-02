"""Pass50: put the rebuilt shell meshes back into their own assets, lift the
hall lights and soften the hall's grade boundaries (-run=pythonscript).
MUTATES AND SAVES the assets and the level.

Each Rebuilt/<name>.fbx (hall50_blender.py) is re-imported over the asset it
came from (Current50.json), with native38's flags; then every slot gets its
recorded material back by slot name and the collision setup is restored, so
the actors placing these meshes are untouched.
Lights standing in a hall below 4.2 m (the old ceiling lights) move to
that hall's new ceiling (Hall50.json 'halls') with more output for the height.
The three room grades that now share one hall blend over 4 m instead of
switching at the old walls.
"""
import unreal as u, json, re, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAP = '/Game/Airport38/L_Airport_Repair38'
CUR = json.loads((HERE / 'Current50.json').read_text(encoding='utf-8'))
HALL = json.loads((HERE / 'Hall50.json').read_text(encoding='utf-8'))
R = dict(status='RUNNING', meshes={}, lights=[], volumes=[])


def prop(o, **kw):
    for k, v in kw.items():
        o.set_editor_property(k, v)


def base(n):
    return re.sub(r'\.\d{3}$', '', n)


def reimport(name, rec):
    path = rec['path'].split('.')[0]
    folder, asset = path.rsplit('/', 1)
    t = u.AssetImportTask()
    prop(t, filename=str(HERE / 'Rebuilt' / (name + '.fbx')), destination_path=folder, destination_name=asset,
         automated=True, save=True, replace_existing=True)
    o = u.FbxImportUI()
    prop(o, import_mesh=True, import_as_skeletal=False, import_materials=False, import_textures=False,
         automated_import_should_detect_type=False, mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH)
    prop(o.static_mesh_import_data, combine_meshes=True, auto_generate_collision=False,
         reorder_material_to_fbx_order=True, convert_scene=False, convert_scene_unit=True,
         normal_import_method=u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS)
    t.set_editor_property('options', o)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    sm = u.load_asset(path)
    want = {base(s['slot']): s['material'] for s in rec['slots']}
    by_mat = {base(s['material'].split('.')[-1]): s['material'] for s in rec['slots'] if s['material']}
    slots = []
    for i, s in enumerate(sm.get_editor_property('static_materials')):
        n = base(str(s.get_editor_property('material_slot_name')))
        m = want.get(n) or by_mat.get(n)
        if m:
            sm.set_material(i, u.load_asset(m))
        slots.append([n, m])
    bs = sm.get_editor_property('body_setup')
    if rec.get('trace_flag') and 'COMPLEX_AS_SIMPLE' in rec['trace_flag']:
        bs.set_editor_property('collision_trace_flag', u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    if rec.get('double_sided') is not None:
        bs.set_editor_property('double_sided_geometry', rec['double_sided'])
    assert u.EditorAssetLibrary.save_loaded_asset(sm)
    R['meshes'][name] = dict(slots=slots, unmatched=[n for n, m in slots if not m])


def main():
    for name in HALL['cuts']:
        reimport(name, CUR['meshes'][name])
    assert u.EditorLoadingAndSavingUtils.load_map(MAP)
    for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
        if isinstance(a, u.Light) and not isinstance(a, u.DirectionalLight):
            p = a.get_actor_location()
            sx, sy, sz = p.x / 100, -p.y / 100, p.z / 100
            H = next((h for h in HALL['halls'] if h['hall'][0] < sx < h['hall'][1] and h['hall'][2] < sy < h['hall'][3]), None)
            zc = H['ceiling'] - .169 if H else None
            if H and sz < 4.2:
                c = a.get_component_by_class(u.LightComponent)
                c.set_editor_property('intensity', c.get_editor_property('intensity') * HALL['light_gain'])
                if hasattr(c, 'attenuation_radius'):
                    c.set_editor_property('attenuation_radius', max(c.get_editor_property('attenuation_radius'), 1600.0))
                a.set_actor_location(u.Vector(p.x, p.y, zc * 100), False, False)
                R['lights'].append(dict(label=a.get_actor_label(), source=[round(sx, 3), round(sy, 3)], z=[round(sz, 3), zc]))
        elif isinstance(a, u.PostProcessVolume) and a.get_actor_label() in HALL['blend_volumes']:
            a.set_editor_property('blend_radius', 400.0)
            R['volumes'].append(a.get_actor_label())
    assert u.EditorLoadingAndSavingUtils.save_current_level()
    R['status'] = 'SUCCESS'


try:
    main()
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'Reimport50.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
print('REIMPORT50', R['status'])
