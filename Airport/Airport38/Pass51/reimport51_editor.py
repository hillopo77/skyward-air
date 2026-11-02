"""Pass51: put the cut meshes (cut51_blender.py -> Rebuilt/) back into their
own assets (-run=pythonscript). MUTATES AND SAVES the assets.

Same as Pass50's reimport: native38 import flags, each slot gets its recorded
material back by slot name (Current51.json), collision set-up restored, so the
actors placing these meshes are untouched. Only meshes Cut51Report.json marks
'rebuilt' are re-imported.
"""
import unreal as u, json, re, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
CUR = json.loads((HERE / 'Current51.json').read_text(encoding='utf-8'))
CUT = json.loads((HERE / 'Cut51Report.json').read_text(encoding='utf-8'))
R = dict(status='RUNNING', meshes={})


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


try:
    for name, rep in CUT['meshes'].items():
        if rep.get('rebuilt'):
            reimport(name, CUR['meshes'][name])
    R['status'] = 'SUCCESS'
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'Reimport51.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
print('REIMPORT51', R['status'])
