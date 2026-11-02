"""Pass70: install the new fire extinguishers, their stands and the A08 play plane (-run=pythonscript).
MUTATES AND SAVES the level and three meshes (built by props70_blender.py).

  stands       every 'Safety station N' takes SM_AP_P70ExtStand, backed against the wall that
               Pass48/ext70_probe.py found beside it and facing into the room (some old stands
               faced the wall); with no wall within 1.6 m it keeps its old heading
  extinguishers  every 'Usable extinguisher N' (the airport's spray pick-up, label unchanged so the
               interaction still finds it) takes SM_AP_P70Extinguisher, standing in its stand's tray
  play plane   'Airport70 play plane' on the A08 kids' mat, nose to the west; the Pass66 toy plane
               and balls move off the mat's centre so they do not start inside it
Meshes face -Y in Blender = +Y in Unreal: yaw = atan2(d.y, d.x) - 90 for a facing d (UE axes).
"""
import unreal as u, json, math, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAP = '/Game/Airport38/L_Airport_Repair38'
MESH_DIR = '/Game/Airport38/Pass48Meshes'
MAT_DIRS = ('/Game/Airport38/Finish43', '/Game/Airport38/Pass48/Materials', '/Game/Airport38/Materials')
BUILD = json.loads((HERE / 'Props70Build.json').read_text(encoding='utf-8'))
EXT = json.loads((HERE.parent / 'Pass48' / 'Ext70.json').read_text(encoding='utf-8'))
WALLS = json.loads((HERE / 'ExtWalls70.json').read_text(encoding='utf-8'))   # nearest layout wall (not a probe hit: those
                                                                           # caught benches and receiving stations)
PLANE_AT, PLANE_FACING = (-26.3, 32.85), (-1.0, 0.0)                    # source metres; nose west
MOVE = {'Airport66 toy plane 00': (-24.9, 33.3), 'Airport66 ball 00': (-28.1, 33.35), 'Airport66 ball teal 00': (-27.8, 32.35)}
R = dict(status='RUNNING', meshes=[], stations=[], notes=[])
_INDEX = {}


def material(name):
    for d in MAT_DIRS:
        if u.EditorAssetLibrary.does_asset_exist(d + '/' + name):
            return u.load_asset(d + '/' + name)
    if not _INDEX:
        for path in u.EditorAssetLibrary.list_assets('/Game', recursive=True, include_folder=False):
            _INDEX.setdefault(path.split('/')[-1].split('.')[0], path)
    return u.load_asset(_INDEX[name]) if name in _INDEX else None


def import_mesh(item, complex_collision):
    t = u.AssetImportTask()
    for k, v in dict(filename=item['fbx'], destination_path=MESH_DIR, destination_name=item['asset'], automated=True, save=True,
                     replace_existing=True).items():
        t.set_editor_property(k, v)
    o = u.FbxImportUI()
    for k, v in dict(import_mesh=True, import_as_skeletal=False, import_materials=False, import_textures=False,
                     automated_import_should_detect_type=False, mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH).items():
        o.set_editor_property(k, v)
    for k, v in dict(combine_meshes=True, auto_generate_collision=True, reorder_material_to_fbx_order=True, convert_scene=False,
                     convert_scene_unit=True, normal_import_method=u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS).items():
        o.static_mesh_import_data.set_editor_property(k, v)
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
    bs = mesh.get_editor_property('body_setup')
    if bs:
        bs.set_editor_property('collision_trace_flag', u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE if complex_collision
                               else u.CollisionTraceFlag.CTF_USE_DEFAULT)
    u.EditorAssetLibrary.save_loaded_asset(mesh)
    R['meshes'].append(item['asset'])
    return mesh


def ue(x, y, z):
    return u.Vector(x * 100, -y * 100, z * 100)


def yaw_for(dx, dy):
    """Facing (dx, dy) in source axes -> actor yaw for a mesh whose front is Unreal +Y."""
    return math.degrees(math.atan2(-dy, dx)) - 90.0


def setup(a, mesh, movable=True, collision=True):
    c = a.static_mesh_component
    c.set_static_mesh(mesh)
    if movable:
        c.set_mobility(u.ComponentMobility.MOVABLE)
    if collision:
        c.set_collision_enabled(u.CollisionEnabled.QUERY_AND_PHYSICS)


def main():
    meshes = {it['asset']: import_mesh(it, complex_collision=it['asset'] != 'SM_AP_P70Extinguisher') for it in BUILD['items']}
    assert u.EditorLoadingAndSavingUtils.load_map(MAP)
    EA = u.get_editor_subsystem(u.EditorActorSubsystem)
    acts = {a.get_actor_label(): a for a in EA.get_all_level_actors()}
    assert EXT.get('status') == 'SUCCESS', 'run ext70_probe.py first'
    for st in EXT['stations']:
        a = acts.get(st['station']); ext = acts.get(st['extinguisher'] or '')
        if a is None:
            continue
        cx, cy, fz = st['centre'][0], st['centre'][1], st['floor']
        w = WALLS.get(st['station'])
        hits = [w] if w else []
        if w:
            dx, dy = w['face']                                          # back to the wall, facing into the room
            k = float(w['wall'][2:])
            px, py = (k + dx * .27, cy) if w['wall'].startswith('x=') else (cx, k + dy * .27)
        else:
            r = math.radians(st['yaw'] + 90.0)                          # no wall: keep the old heading
            dx, dy = math.cos(r), -math.sin(r); px, py = cx, cy
        yaw = yaw_for(dx, dy)
        a.set_actor_location_and_rotation(ue(px, py, fz), u.Rotator(0, 0, yaw), False, True)
        a.set_actor_scale3d(u.Vector(1, 1, 1))
        setup(a, meshes['SM_AP_P70ExtStand'], movable=True)
        if ext:
            ext.set_actor_location_and_rotation(ue(px + dx * .01, py + dy * .01, fz + .045), u.Rotator(0, 0, yaw), False, True)
            ext.set_actor_scale3d(u.Vector(1, 1, 1))
            ext.static_mesh_component.set_static_mesh(meshes['SM_AP_P70Extinguisher'])
        R['stations'].append(dict(station=st['station'], at=[round(px, 3), round(py, 3), fz], facing=[dx, dy], yaw=round(yaw, 1),
                                  wall=bool(hits)))
    for a in EA.get_all_level_actors():
        if a.get_actor_label() == 'Airport70 play plane':
            EA.destroy_actor(a)
    p = EA.spawn_actor_from_class(u.StaticMeshActor, ue(PLANE_AT[0], PLANE_AT[1], 0.012), u.Rotator(0, 0, yaw_for(*PLANE_FACING)))
    p.set_actor_label('Airport70 play plane'); p.set_folder_path('Airport38/Pass70')
    setup(p, meshes['SM_AP_P70PlayPlane'], movable=True)
    p.static_mesh_component.set_collision_profile_name('BlockAll')
    for lab, (x, y) in MOVE.items():
        a = acts.get(lab)
        if a:
            z = a.get_actor_location().z
            a.set_actor_location(u.Vector(x * 100, -y * 100, z), False, True)
    assert u.EditorLoadingAndSavingUtils.save_current_level()
    R['status'] = 'SUCCESS'


try:
    main()
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'Props70.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
print('PROPS70', R['status'])
