"""Pass64: seat the waiting passengers on the new gate-lounge seating
(-run=pythonscript). MUTATES AND SAVES the level and Exports/airport_layout.json.

Lounge64Seats.json (lounges62_blender.py) gives, per passenger actor, the new
source position, height, layout rotation_degrees and seat label. For each one:
  the 'CH12 <name>' skeletal actor and its 'CH12COLL <name>' collision cube move
  to the new spot (cube keeps its height above the actor); the actor's yaw turns
  by the change in rotation (source and engine y are mirrored);
  airport_layout.json character_placements: location, rotation_degrees and
  chair_fit39 are updated, so talk points and the occupied-seat check follow.
The previous layout is Backup/airport_layout.before64.json; the level is backed
up by Check50.ps1 -Mutates.
"""
import unreal as u, json, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAP = '/Game/Airport38/L_Airport_Repair38'
LAYOUT = HERE.parent / 'Exports' / 'airport_layout.json'
SEATS = json.loads((HERE / 'Lounge64Seats.json').read_text(encoding='utf-8'))
R = dict(status='RUNNING', moved=[], missing=[])


def main():
    layout = json.loads(LAYOUT.read_text(encoding='utf-8'))
    by_actor = {q['actor']: q for q in layout['character_placements'] if q.get('actor')}
    assert u.EditorLoadingAndSavingUtils.load_map(MAP)
    EA = u.get_editor_subsystem(u.EditorActorSubsystem)
    actors = {a.get_actor_label(): a for a in EA.get_all_level_actors()}
    for actor, (x, y, z, rot, seat) in SEATS.items():
        q = by_actor.get(actor)
        a = actors.get(actor)
        if not q or not a:
            R['missing'].append(actor); continue
        old_loc, old_rot = list(q['location']), q.get('rotation_degrees', 0)
        a.modify(); a.root_component.modify()
        p = a.get_actor_location()
        dz_actor = p.z - old_loc[2] * 100                    # actor's own offset from the placement height
        a.set_actor_location(u.Vector(x * 100, -y * 100, z * 100 + dz_actor), False, False)
        r = a.get_actor_rotation()
        a.set_actor_rotation(u.Rotator(r.roll, r.pitch, r.yaw - (rot - old_rot)), False)
        coll = actors.get(actor.replace('CH12 ', 'CH12COLL ', 1))
        got = a.get_actor_location()
        R.setdefault('readback', []).append([actor, round(got.x / 100, 2), round(-got.y / 100, 2)])
        if coll:
            coll.modify(); coll.root_component.modify()
            cp = coll.get_actor_location()
            coll.set_actor_location(u.Vector(x * 100, -y * 100, cp.z - old_loc[2] * 100 + z * 100), False, False)
        q['location'] = [x, y, z]
        q['rotation_degrees'] = rot
        q['chair_fit39'] = seat
        R['moved'].append([actor, old_loc, [x, y, z], old_rot, rot, bool(coll)])
    assert u.EditorLoadingAndSavingUtils.save_current_level()
    R['dirty_saved'] = u.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    LAYOUT.write_text(json.dumps(layout, indent=1, ensure_ascii=False), encoding='utf-8')
    R['status'] = 'SUCCESS'


try:
    main()
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'Npc64.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
print('NPC64', R['status'])
