"""Pass48 batch import: world-space FBX meshes placed at the origin, plus
actors to hide or show, in one editor session (-run=pythonscript).

ImportJobs48.json beside this file:
  {"jobs": [{"build": "<build report json>", "label": "<actor label>",
             "folder": "<outliner folder>", "collision": "none" | "block"}, ...],
   "hide": ["<actor label>", ...], "show": ["<actor label>", ...],
   "actors": [{"mesh": "<project mesh name>", "prefix": "<label prefix>", "folder": "...",
               "items": [[x, y, z, yaw_deg, scale], ...]}]}
"actors" places existing project meshes (trees) as static actors, replacing
any earlier actors with the same label prefix.

Same import flags as native38 / import_mesh47. Each material slot is matched
by name to a project material: the Finish43 instances first (the live
textured finishes), then Pass48, then /Game/Airport38/Materials. Re-runnable: each job replaces its own
actor. Hidden actors are hidden in game and in the editor and lose collision,
so a hide is reversed by listing the label under "show".
MUTATES AND SAVES the level.
"""
import unreal as u, json, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAP = '/Game/Airport38/L_Airport_Repair38'
MESH_DIR = '/Game/Airport38/Pass48Meshes'
MAT_DIRS = ('/Game/Airport38/Finish43', '/Game/Airport38/Pass48/Materials', '/Game/Airport38/Materials')
R = dict(status='RUNNING', jobs=[], hidden=[], shown=[], notes=[])


def prop(o, **kw):
    for k, v in kw.items():
        o.set_editor_property(k, v)


_INDEX = {}


def material(name):
    for d in MAT_DIRS:
        if u.EditorAssetLibrary.does_asset_exist(d + '/' + name):
            return u.load_asset(d + '/' + name)
    if not _INDEX:                            # anywhere else in the project, first match by asset name
        _INDEX['_'] = ''

        for path in u.EditorAssetLibrary.list_assets('/Game', recursive=True, include_folder=False):
            _INDEX.setdefault(path.split('/')[-1].split('.')[0], path)
    return u.load_asset(_INDEX[name]) if name in _INDEX else None


def import_mesh(job):
    build = json.loads((HERE / job['build']).read_text(encoding='utf-8'))
    assert build['status'] == 'SUCCESS', job['build']
    t = u.AssetImportTask()
    prop(t, filename=build['fbx'], destination_path=MESH_DIR, destination_name=build['asset'],
         automated=True, save=True, replace_existing=True)
    o = u.FbxImportUI()
    prop(o, import_mesh=True, import_as_skeletal=False, import_materials=False, import_textures=False,
         automated_import_should_detect_type=False, mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH)
    prop(o.static_mesh_import_data, combine_meshes=True, auto_generate_collision=False,
         reorder_material_to_fbx_order=True, convert_scene=False, convert_scene_unit=True,
         normal_import_method=u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS)
    t.set_editor_property('options', o)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    mesh = u.load_asset(MESH_DIR + '/' + build['asset'])
    assert mesh is not None, 'import failed: ' + build['asset']
    slots = []
    for i, sm in enumerate(mesh.static_materials):
        name = str(sm.material_slot_name)
        base = next((m for m in build['materials'] if name.startswith(m)), name)
        mat = material(base)
        if mat:
            mesh.set_material(i, mat)
        else:
            R['notes'].append('no project material for %r in %s' % (name, build['asset']))
        slots.append([i, name, mat.get_path_name() if mat else None])
    u.EditorAssetLibrary.save_loaded_asset(mesh)
    return mesh, slots


def main():
    spec = json.loads((HERE / 'ImportJobs48.json').read_text(encoding='utf-8-sig'))
    meshes = [(job,) + import_mesh(job) for job in spec.get('jobs', [])]
    assert u.EditorLoadingAndSavingUtils.load_map(MAP)
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    EA = u.get_editor_subsystem(u.EditorActorSubsystem)
    actors = EA.get_all_level_actors()
    labels = {job['label'] for job, _, _ in meshes}
    for a in actors:
        try:
            if a.get_actor_label() in labels:
                EA.destroy_actor(a)
        except Exception:
            pass
    for job, mesh, slots in meshes:
        a = EA.spawn_actor_from_class(u.StaticMeshActor, u.Vector(0, 0, 0), u.Rotator(0, 0, 0))
        a.set_actor_label(job['label'])
        a.set_folder_path(job['folder'])
        c = a.static_mesh_component
        c.set_static_mesh(mesh)
        c.set_mobility(u.ComponentMobility.STATIC)
        if job.get('collision') == 'block':
            c.set_collision_enabled(u.CollisionEnabled.QUERY_AND_PHYSICS)
            c.set_collision_profile_name('BlockAll')
        else:
            c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
            c.set_collision_profile_name('NoCollision')
        b = mesh.get_bounding_box()
        R['jobs'].append(dict(label=job['label'], asset=mesh.get_name(), slots=slots,
                              bounds_m=dict(x=[round(b.min.x / 100, 2), round(b.max.x / 100, 2)],
                                            y_source=[round(-b.max.y / 100, 2), round(-b.min.y / 100, 2)],
                                            z=[round(b.min.z / 100, 2), round(b.max.z / 100, 2)])))
    for group in spec.get('actors', []):
        for a in EA.get_all_level_actors():
            try:
                if a.get_actor_label().startswith(group['prefix'] + ' '):
                    EA.destroy_actor(a)
            except Exception:
                pass
        material('MI_AP_P43TOak')                       # fills the project index
        mesh = u.load_asset(_INDEX.get(group['mesh'], '')) if group['mesh'] in _INDEX else None
        assert mesh, 'no mesh ' + group['mesh']
        for k, (x, y, z, yaw, sc) in enumerate(group['items']):
            a = EA.spawn_actor_from_class(u.StaticMeshActor, u.Vector(x * 100, -y * 100, z * 100), u.Rotator(0, 0, -yaw))
            a.set_actor_label('%s %02d' % (group['prefix'], k))
            a.set_folder_path(group['folder'])
            a.set_actor_scale3d(u.Vector(sc, sc, sc))
            c = a.static_mesh_component
            c.set_static_mesh(mesh)
            c.set_mobility(u.ComponentMobility.STATIC)
            c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
        R.setdefault('placed', []).append([group['prefix'], len(group['items'])])
    by_label = {}
    for a in EA.get_all_level_actors():
        by_label.setdefault(a.get_actor_label(), []).append(a)
    for lab, hide in [(l, True) for l in spec.get('hide', [])] + [(l, False) for l in spec.get('show', [])]:
        found = by_label.get(lab, [])
        if not found:
            R['notes'].append('no actor %r to %s' % (lab, 'hide' if hide else 'show'))
        for a in found:
            a.set_actor_hidden_in_game(hide)
            a.set_is_temporarily_hidden_in_editor(hide)
            c = a.get_component_by_class(u.StaticMeshComponent)
            if c:
                c.set_visibility(not hide, True)
                if hide:
                    c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
            (R['hidden'] if hide else R['shown']).append(lab)
    assert u.EditorLoadingAndSavingUtils.save_map(world, MAP), 'save_map failed'
    R['status'] = 'SUCCESS'


try:
    main()
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'ImportMesh48.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
print('IMPORTMESH48', R['status'])
