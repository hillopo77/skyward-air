"""Pass71: mount the new extinguisher cabinets on real walls (-run=pythonscript). MUTATES AND SAVES.

Each 'Safety station N' becomes SM_AP_P71ExtCabinet with its back flush on the wall face that
Pass48/walls71_probe.py measured in the game (both 1.0 m and 2.6 m traces on one vertical face), its
front along that wall's normal; 'Usable extinguisher N' (the airport's spray pick-up; the interaction
follows the actor) becomes SM_AP_P71Extinguisher standing on the cabinet shelf. A station whose probe
found no wall is left where it is and reported, never guessed.
"""
import unreal as u, json, math, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAP = '/Game/Airport38/L_Airport_Repair38'
BUILD = json.loads((HERE / 'Props71Build.json').read_text(encoding='utf-8'))
WALLS = json.loads((HERE.parent / 'Pass48' / 'Walls71.json').read_text(encoding='utf-8'))
SHELF, DEPTH = .48, .26
R = dict(status='RUNNING', meshes=[], stations=[], skipped=[], notes=[])


def ue(x, y, z):
    return u.Vector(x * 100, -y * 100, z * 100)


def main():
    src = (HERE / 'props70_editor.py').read_text(encoding='utf-8')          # reuse its importer (material binding by name)
    g = dict(__name__='props70e', __file__=str(HERE / 'props70_editor.py'))
    exec(compile(src.split(chr(10) + 'def ue(')[0], 'props70e', 'exec'), g)
    g['R'] = R
    meshes = {it['asset']: g['import_mesh'](it, complex_collision=it['asset'] != 'SM_AP_P71Extinguisher') for it in BUILD['items']}
    assert u.EditorLoadingAndSavingUtils.load_map(MAP)
    EA = u.get_editor_subsystem(u.EditorActorSubsystem)
    acts = {a.get_actor_label(): a for a in EA.get_all_level_actors()}
    assert WALLS.get('status') == 'SUCCESS', 'run walls71_probe.py first'
    for st in WALLS['stations']:
        a, ext = acts.get(st['station']), acts.get(st.get('extinguisher') or '')
        if a is None:
            continue
        if 'wall_point' not in st:
            R['skipped'].append(st['station']); continue
        wx, wy = st['wall_point'][0], st['wall_point'][1]
        nx, ny = st['normal']                                               # into the room, source axes
        fz = st['floor']
        yaw = math.degrees(math.atan2(-ny, nx)) - 90.0                       # mesh front (+Y in Unreal) along the normal
        a.modify()                                                          # only existing actors change: mark the level dirty
        if ext:
            ext.modify()
        a.set_actor_location_and_rotation(ue(wx, wy, fz), u.Rotator(0, 0, yaw), False, True)
        a.set_actor_scale3d(u.Vector(1, 1, 1))
        c = a.static_mesh_component
        c.set_static_mesh(meshes['SM_AP_P71ExtCabinet']); c.set_mobility(u.ComponentMobility.MOVABLE)
        c.set_collision_enabled(u.CollisionEnabled.QUERY_AND_PHYSICS)
        if ext:
            ext.set_actor_location_and_rotation(ue(wx + nx * DEPTH / 2, wy + ny * DEPTH / 2, fz + SHELF + .006), u.Rotator(0, 0, yaw), False, True)
            ext.set_actor_scale3d(u.Vector(1, 1, 1))
            ext.static_mesh_component.set_static_mesh(meshes['SM_AP_P71Extinguisher'])
        R['stations'].append(dict(station=st['station'], wall=[round(wx, 3), round(wy, 3)], normal=[nx, ny], yaw=round(yaw, 1),
                                  moved=st.get('dist')))
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    assert u.EditorLoadingAndSavingUtils.save_map(world, MAP), 'save failed'     # save_current_level skips a level it thinks is clean
    R['status'] = 'SUCCESS'


try:
    main()
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'Props71.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
print('PROPS71', R['status'])
