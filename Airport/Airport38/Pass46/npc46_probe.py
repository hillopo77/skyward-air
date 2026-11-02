"""Pass46 / P46-011: move the security greeter out of the walk lane.

The bag-carry failure (P45-008 / P46-011) is not random physics. In every run
that loses the bag, the held bag stops dead at (-47.31, -0.14, ~1.3) during the
walk [-47.7,6.1] -> [-47.7,-0.4] -> [-45.5,-0.4], and the passenger walks on
still "holding" it. That point lies inside `CH12COLL Security greeter`, the
hidden 0.7 x 0.7 x 1.8 m collision body of the greeter added in Pass39 at
(-47.0, -0.4) - on the authored walk line y = -0.4, which has existed since
Pass38. The pawn slides round her; the bag, hanging lower, swings into her
box and wedges. Whether it wedges depends on the swing, hence 3 outcomes in 4
runs.

She moves to (-43.6, -2.3): inside the controlled entry, beside the entering
passenger path rather than on it, more than 1 m from every walk leg of the
flight journey and about 1 m from the nearest fixture, facing the people
coming in. The visible character and its collision body move together,
keeping their existing offset.

Run standalone under -run=pythonscript. MUTATES AND SAVES the level.
"""
import unreal as u, json, time, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAP = '/Game/Airport38/L_Airport_Repair38'
ACTOR, PROXY = 'CH12 Security greeter', 'CH12COLL Security greeter'
OLD = (-47.0, -0.4)
NEW = (-43.6, -2.3)
ROT = 73.0          # layout rotation_degrees; actor yaw is its negative

S = dict(status='RUNNING', started=time.time(), moved=[])


def save(status=None, **extra):
    if status:
        S['status'] = status
    S.update(extra)
    (HERE / 'Npc46.json').write_text(json.dumps(S, indent=1), encoding='utf-8')


def src(vec):
    return [round(vec.x / 100.0, 3), round(-vec.y / 100.0, 3),
            round(vec.z / 100.0, 3)]


def main():
    assert u.EditorLoadingAndSavingUtils.load_map(MAP), 'could not load ' + MAP
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    EA = u.get_editor_subsystem(u.EditorActorSubsystem)
    actors = {a.get_actor_label(): a for a in EA.get_all_level_actors()}
    a, p = actors[ACTOR], actors[PROXY]
    al, pl = a.get_actor_location(), p.get_actor_location()
    assert abs(al.x / 100.0 - OLD[0]) < 0.05 and abs(-al.y / 100.0 - OLD[1]) < 0.05, \
        'greeter is not where the analysis found her: %s' % src(al)
    offset = pl - al
    target = u.Vector(NEW[0] * 100.0, -NEW[1] * 100.0, al.z)
    for actor, loc in ((a, target), (p, target + offset)):
        before = dict(location=src(actor.get_actor_location()),
                      yaw=round(actor.get_actor_rotation().yaw, 2))
        actor.set_actor_location(loc, False, True)
        actor.set_actor_rotation(u.Rotator(yaw=-ROT), False)
        S['moved'].append(dict(actor=actor.get_actor_label(), before=before,
                               after=dict(location=src(actor.get_actor_location()),
                                          yaw=round(actor.get_actor_rotation().yaw, 2))))
    save()
    assert u.EditorLoadingAndSavingUtils.save_map(world, MAP), 'save_map failed'
    save('SUCCESS', finished=time.time())
    print('NPC46 SUCCESS', flush=True)


try:
    main()
except Exception:
    S['error'] = traceback.format_exc()
    save('ERROR')
    raise
