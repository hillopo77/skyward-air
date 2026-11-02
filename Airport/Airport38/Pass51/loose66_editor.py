"""Pass66: import and place the loose sandbox props from loose66_blender.py (-run=pythonscript).
MUTATES AND SAVES the meshes in /Game/Airport38/Pass48Meshes and the level.

Each prop mesh gets one simple collision shape (a sphere for balls, a box
otherwise) so it can simulate. Each placement becomes a StaticMeshActor
'Airport66 <prop> NN': MOVABLE, BlockAll, simulating physics with a believable
mass (Loose66Build.json 'kg'), spawned 4 cm above its surface so it settles
onto whatever is really there when play starts. Re-runnable: earlier
'Airport66 ' actors are replaced.
"""
import unreal as u, json, re, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAP = '/Game/Airport38/L_Airport_Repair38'
MESH_DIR = '/Game/Airport38/Pass48Meshes'
MAT_DIRS = ('/Game/Airport38/Finish43', '/Game/Airport38/Pass48/Materials', '/Game/Airport38/Materials')
R = dict(status='RUNNING', meshes=[], placed=0, notes=[])
_INDEX = {}


def prop(o, **kw):
    for k, v in kw.items():
        o.set_editor_property(k, v)


def material(name):
    for d in MAT_DIRS:
        if u.EditorAssetLibrary.does_asset_exist(d + '/' + name):
            return u.load_asset(d + '/' + name)
    if not _INDEX:
        _INDEX['_'] = ''
        for path in u.EditorAssetLibrary.list_assets('/Game', recursive=True, include_folder=False):
            _INDEX.setdefault(path.split('/')[-1].split('.')[0], path)
    return u.load_asset(_INDEX[name]) if name in _INDEX else None


def import_mesh(item):
    t = u.AssetImportTask()
    prop(t, filename=item['fbx'], destination_path=MESH_DIR, destination_name=item['asset'], automated=True, save=True,
         replace_existing=True)
    o = u.FbxImportUI()
    prop(o, import_mesh=True, import_as_skeletal=False, import_materials=False, import_textures=False,
         automated_import_should_detect_type=False, mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH)
    prop(o.static_mesh_import_data, combine_meshes=True, auto_generate_collision=True, reorder_material_to_fbx_order=True,
         convert_scene=False, convert_scene_unit=True, normal_import_method=u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS)
    t.set_editor_property('options', o)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    mesh = u.load_asset(MESH_DIR + '/' + item['asset'])
    assert mesh is not None, 'import failed: ' + item['asset']
    for i, sm in enumerate(mesh.static_materials):
        name = str(sm.material_slot_name)
        base = next((m for m in item['materials'] if name.startswith(m)), None) or \
            (item['materials'][i] if i < len(item['materials']) else name)
        mat = material(base)
        if mat:
            mesh.set_material(i, mat)
        else:
            R['notes'].append('no material %r in %s' % (name, item['asset']))
    # one simple shape (box, sphere for balls); the import's auto collision stays if no library can replace it
    shape = u.ScriptCollisionShapeType.SPHERE if 'Ball' in item['asset'] else u.ScriptCollisionShapeType.BOX
    sub = None
    for get in (lambda: u.get_editor_subsystem(u.StaticMeshEditorSubsystem), lambda: u.EditorStaticMeshLibrary):
        try:
            sub = get()
        except Exception:
            sub = None
        if sub is not None:
            break
    if sub is not None:
        try:
            sub.remove_collisions(mesh); sub.add_simple_collisions(mesh, shape)
        except Exception as e:
            R['notes'].append('collision %s: %s' % (item['asset'], e))
    count = None
    try:
        count = sub.get_simple_collision_count(mesh) if sub is not None else None
    except Exception:
        pass
    bs = mesh.get_editor_property('body_setup')
    if bs:
        bs.set_editor_property('collision_trace_flag', u.CollisionTraceFlag.CTF_USE_DEFAULT)
    u.EditorAssetLibrary.save_loaded_asset(mesh)
    R['meshes'].append([item['asset'], count, str(sub)[:40] if sub is not None else 'auto'])
    return mesh


def short(asset):
    s = asset.replace('SM_AP_P66', '')
    return ' '.join(w.lower() for w in re.findall(r'[A-Z][a-z]*', s))


def main():
    rep = json.loads((HERE / 'Loose66Build.json').read_text(encoding='utf-8'))
    assert rep['status'] == 'SUCCESS'
    meshes = {it['asset']: (import_mesh(it), it['kg']) for it in rep['items']}
    assert u.EditorLoadingAndSavingUtils.load_map(MAP)
    EA = u.get_editor_subsystem(u.EditorActorSubsystem)
    for a in EA.get_all_level_actors():
        if a.get_actor_label().startswith('Airport66 '):
            EA.destroy_actor(a)
    count = {}
    for asset, x, y, z, yaw in rep['placements']:
        mesh, kg = meshes[asset]
        if asset == 'SM_AP_P66Mug' and u.EditorAssetLibrary.does_asset_exist(MESH_DIR + '/SM_AP_P66MugCream'):
            mesh = u.load_asset(MESH_DIR + '/SM_AP_P66MugCream')     # the plain mug imports without collision (mug66_editor.py)
        name = short(asset)
        k = count.get(name, 0); count[name] = k + 1
        a = EA.spawn_actor_from_class(u.StaticMeshActor, u.Vector(x * 100, -y * 100, (z + .04) * 100), u.Rotator(0, 0, -yaw))
        a.set_actor_label('Airport66 %s %02d' % (name, k))
        a.set_folder_path('Gameplay/Pass66 loose props')
        c = a.static_mesh_component
        c.set_static_mesh(mesh)
        c.set_mobility(u.ComponentMobility.MOVABLE)
        c.set_collision_profile_name('PhysicsActor')
        c.set_collision_enabled(u.CollisionEnabled.QUERY_AND_PHYSICS)
        c.set_collision_response_to_channel(u.CollisionChannel.ECC_VISIBILITY, u.CollisionResponseType.ECR_BLOCK)
        c.set_simulate_physics(True)
        try:
            c.set_mass_override_in_kg(u.Name('None'), float(kg), True)
        except Exception as e:
            R['notes'].append('mass: %s' % e)
        c.set_editor_property('cast_shadow', True)
        R['placed'] += 1
    assert u.EditorLoadingAndSavingUtils.save_current_level()
    R['status'] = 'SUCCESS'


try:
    main()
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'Loose66.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
print('LOOSE66', R['status'])
