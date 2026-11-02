"""Pass47 generic import: one world-space FBX, placed at the origin.

The job comes from ImportJob47.json beside this file:
  {"build": "<build report json>", "label": "<actor label>",
   "folder": "<outliner folder>", "collision": "none" | "block"}

Same flags as native38 / import_roof46: no scene conversion, units only.
Each material slot is matched by name to the project material of the same
name under /Game/Airport38/Materials. Re-runnable: replaces its own actor.
MUTATES AND SAVES the level.
"""
import unreal as u, json, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAP = '/Game/Airport38/L_Airport_Repair38'
MESH_DIR = '/Game/Airport38/Pass47Meshes'
MAT_DIR = '/Game/Airport38/Materials'
R = dict(status='RUNNING', notes=[])


def prop(o, **kw):
    for k, v in kw.items():
        o.set_editor_property(k, v)


def main():
    job = json.loads((HERE / 'ImportJob47.json').read_text(encoding='utf-8-sig'))
    R['job'] = job
    build = json.loads((HERE / job['build']).read_text(encoding='utf-8'))
    assert build['status'] == 'SUCCESS'
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
    assert mesh is not None, 'import failed'
    R['slots'] = []
    for i, sm in enumerate(mesh.static_materials):
        name = str(sm.material_slot_name)
        base = next((m for m in build['materials'] if name.startswith(m)), name)
        mat = u.load_asset(MAT_DIR + '/' + base)
        if mat:
            mesh.set_material(i, mat)
        else:
            R['notes'].append('no project material for %r' % name)
        R['slots'].append([i, name, mat.get_name() if mat else None])
    u.EditorAssetLibrary.save_loaded_asset(mesh)

    assert u.EditorLoadingAndSavingUtils.load_map(MAP)
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    EA = u.get_editor_subsystem(u.EditorActorSubsystem)
    for a in EA.get_all_level_actors():
        try:
            if a.get_actor_label() == job['label']:
                EA.destroy_actor(a)
        except Exception:
            pass
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
    R['bounds_m'] = dict(x=[round(b.min.x / 100, 2), round(b.max.x / 100, 2)],
                         y_source=[round(-b.max.y / 100, 2), round(-b.min.y / 100, 2)],
                         z=[round(b.min.z / 100, 2), round(b.max.z / 100, 2)])
    assert u.EditorLoadingAndSavingUtils.save_map(world, MAP), 'save_map failed'
    R['status'] = 'SUCCESS'


try:
    main()
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'ImportMesh47.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
print('IMPORTMESH47', R['status'])
