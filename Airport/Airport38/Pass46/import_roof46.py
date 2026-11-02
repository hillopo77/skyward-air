"""Pass46 / P46-006: import the rooftop plant and place it.

Same import flags as native38.py and import_mounts46.py: Blender writes Z-up
metres with no axis conversion, so the scene is not converted, only units.
The mesh is authored in world source coordinates like the project's union
meshes, so the actor goes at the origin unrotated and the importer's Y flip
puts every unit where v() would.

Materials are assigned per slot by name: each Blender material is named after
the project material it stands for (MI_AP_P38BSteel and so on), so the slot
name is the package name. Collision stays off: nothing can reach the roof,
and a colliding mesh would enter the aircraft departure sweep for no reason.

Run standalone under -run=pythonscript. MUTATES AND SAVES the level, and
replaces the actor if a previous run placed one, so it is safe to re-run.
"""
import unreal as u, json, time, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAP = '/Game/Airport38/L_Airport_Repair38'
MESH_DIR = '/Game/Airport38/Pass46Meshes'
MAT_DIR = '/Game/Airport38/Materials'
LABEL = 'Airport46 rooftop plant'

report = dict(status='RUNNING', started=time.time(), notes=[])


def flush(status=None):
    if status:
        report['status'] = status
    (HERE / 'ImportRoof46.json').write_text(json.dumps(report, indent=1),
                                            encoding='utf-8')


def prop(obj, **kw):
    for k, v in kw.items():
        obj.set_editor_property(k, v)


def main():
    build = json.loads((HERE / 'Roof46Build.json').read_text(encoding='utf-8'))
    assert build['status'] == 'SUCCESS', 'Blender build did not succeed'
    assert u.EditorLoadingAndSavingUtils.load_map(MAP), 'could not load ' + MAP
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    EA = u.get_editor_subsystem(u.EditorActorSubsystem)
    AT = u.AssetToolsHelpers.get_asset_tools()

    t = u.AssetImportTask()
    prop(t, filename=build['fbx'], destination_path=MESH_DIR,
         destination_name=build['asset'], automated=True, save=True,
         replace_existing=True)
    o = u.FbxImportUI()
    prop(o, import_mesh=True, import_as_skeletal=False, import_materials=False,
         import_textures=False, automated_import_should_detect_type=False,
         mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH)
    prop(o.static_mesh_import_data, combine_meshes=True,
         auto_generate_collision=False, reorder_material_to_fbx_order=True,
         convert_scene=False, convert_scene_unit=True,
         normal_import_method=u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS)
    t.set_editor_property('options', o)
    AT.import_asset_tasks([t])

    pkg = MESH_DIR + '/' + build['asset']
    mesh = u.load_asset(pkg)
    assert mesh is not None, 'import failed: ' + pkg
    slots = []
    for i, sm in enumerate(mesh.static_materials):
        name = str(sm.material_slot_name)
        mat = u.load_asset(MAT_DIR + '/' + name)
        if mat is None:
            # FBX may suffix duplicate names; match on the known prefix.
            base = next((m for m in build['materials'] if name.startswith(m)), None)
            mat = u.load_asset(MAT_DIR + '/' + base) if base else None
        if mat is None:
            report['notes'].append('no project material for slot %d %r' % (i, name))
        else:
            mesh.set_material(i, mat)
        slots.append(dict(slot=i, name=name,
                          material=mat.get_name() if mat else None))
    report['slots'] = slots
    u.EditorAssetLibrary.save_loaded_asset(mesh)
    b = mesh.get_bounding_box()
    report['mesh_bounds_m'] = dict(
        x=[round(b.min.x / 100, 2), round(b.max.x / 100, 2)],
        y_source=[round(-b.max.y / 100, 2), round(-b.min.y / 100, 2)],
        z=[round(b.min.z / 100, 2), round(b.max.z / 100, 2)])

    for a in EA.get_all_level_actors():
        try:
            if a.get_actor_label() == LABEL:
                EA.destroy_actor(a)
                report['notes'].append('replaced previous ' + LABEL)
        except Exception:
            continue
    a = EA.spawn_actor_from_class(u.StaticMeshActor, u.Vector(0, 0, 0),
                                  u.Rotator(0, 0, 0))
    a.set_actor_label(LABEL)
    a.set_folder_path('Airport38/Pass46/Roof')
    c = a.static_mesh_component
    c.set_static_mesh(mesh)
    c.set_mobility(u.ComponentMobility.STATIC)
    c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
    c.set_collision_profile_name('NoCollision')
    origin, extent = a.get_actor_bounds(False)
    report['placed'] = dict(actor=LABEL, centre_m=[round(origin.x / 100, 2),
                                                   round(-origin.y / 100, 2),
                                                   round(origin.z / 100, 2)],
                            extent_m=[round(extent.x / 100, 2),
                                      round(extent.y / 100, 2),
                                      round(extent.z / 100, 2)])
    flush()
    assert u.EditorLoadingAndSavingUtils.save_map(world, MAP), 'save_map failed'
    flush('SUCCESS')
    print('IMPORTROOF46 SUCCESS', flush=True)


try:
    main()
except Exception:
    report['error'] = traceback.format_exc()
    flush('ERROR')
    raise
