"""Pass58: cabin light from visible fittings (-run=pythonscript). MUTATES AND SAVES the level.

The cabin was lit by 24 'Cabin broad practical' rect lights, 1.15 m squares
hanging in mid-air 15 cm below the bin tops, with no fitting. Like a real
airliner, each now sits on the aisle-side top edge of the overhead bins
(bin doors at x 14.5 / 17.5, top 2.46 m) as a 1.3 m x 6 cm strip, aimed down
and in across the seats and aisle, with a glowing strip fitting of the same
size (engine Cube, MI_AP_P58CabinPanel, no collision, no shadow). Light and
fitting keep / get the 'Skyward:' tag, so they fly with the aircraft.
Originals are kept in Plane58.orig.json; earlier 'P58 cabin' actors are replaced.
"""
import unreal as u, json, traceback
from pathlib import Path
HERE = Path(__file__).resolve().parent
ORIG = HERE / 'Plane58.orig.json'
EDGE = {15.0: (14.62, 1), 17.0: (17.38, -1)}       # light x -> (strip x, inward direction)
Z, LENGTH, THICK, PITCH = 2.47, 130.0, 6.0, -55.0
R = dict(status='RUNNING', strips=[])
try:
    assert u.EditorLoadingAndSavingUtils.load_map('/Game/Airport38/L_Airport_Repair38')
    EA = u.get_editor_subsystem(u.EditorActorSubsystem)
    orig = json.loads(ORIG.read_text(encoding='utf-8')) if ORIG.exists() else {}
    for a in EA.get_all_level_actors():
        if a.get_actor_label().startswith('P58 cabin'):
            EA.destroy_actor(a)
    cube = u.load_asset('/Engine/BasicShapes/Cube')
    mat = u.load_asset('/Game/Airport38/Pass48/Materials/MI_AP_P58CabinPanel')
    assert cube and mat
    for a in EA.get_all_level_actors():
        lab = a.get_actor_label()
        if not (isinstance(a, u.RectLight) and lab.startswith('Cabin broad practical')):
            continue
        c = a.get_component_by_class(u.RectLightComponent)
        p, r = a.get_actor_location(), a.get_actor_rotation()
        o = orig.setdefault(lab, dict(p=[p.x, p.y, p.z], rot=[r.roll, r.pitch, r.yaw],
                                      w=c.get_editor_property('source_width'), h=c.get_editor_property('source_height')))
        sx = round(o['p'][0] / 100, 1)
        if sx not in EDGE:
            R.setdefault('notes', []).append('skipped ' + lab); continue
        ex, inward = EDGE[sx]
        loc = u.Vector(ex * 100, o['p'][1], Z * 100)
        a.set_actor_location(loc, False, False)
        a.set_actor_rotation(u.Rotator(0, PITCH, 0 if inward > 0 else 180), False)
        c.set_editor_property('source_width', LENGTH)            # along the cabin
        c.set_editor_property('source_height', THICK)
        s = EA.spawn_actor_from_class(u.StaticMeshActor, u.Vector(loc.x - inward * 2.0, loc.y, loc.z + 1.0), u.Rotator(0, 0, 0))
        s.set_actor_label('P58 cabin strip ' + (lab.replace('Cabin broad practical', '').strip('. ') or '0'))
        s.set_folder_path('Lighting/Pass58')
        s.tags = [u.Name('Skyward:P58 cabin strip'), u.Name('Airport38PlaneShift16')]
        m = s.static_mesh_component
        m.set_static_mesh(cube); m.set_material(0, mat)
        m.set_mobility(u.ComponentMobility.MOVABLE)
        m.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
        m.set_editor_property('cast_shadow', False)
        s.set_actor_scale3d(u.Vector(.03, LENGTH / 100, .025))
        R['strips'].append([lab, ex, round(o['p'][1] / -100, 2)])
    ORIG.write_text(json.dumps(orig, indent=1), encoding='utf-8')
    assert u.EditorLoadingAndSavingUtils.save_current_level()
    R['status'] = 'SUCCESS'
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'Plane58.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
print('PLANE58', R['status'])
