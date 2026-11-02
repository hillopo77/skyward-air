"""Pass47: Gate 08's waiting row, from shoulder to shoulder to how people sit.

Both west benches were filled seat by seat, six people in the same pose
facing the same way, which reads as a clone row. Strangers leave a gap seat.
  - 'Additional waiting passenger 2' (senior, middle of the second bench)
    takes the free slot 2 of the north bench, beside the two already there,
    same bench model and pose.
  - 'Waiting passenger 7' (crew, middle of the first bench) stands at the
    east glazing looking out at the apron, standing idle, >1 m from the
    nearest fixture.
The visible character and its hidden collision body move together; the
standing body gets the standing proxy's height. MUTATES AND SAVES the level.
"""
import unreal as u, json, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAP = '/Game/Airport38/L_Airport_Repair38'
MOVES = [
    dict(name='Additional waiting passenger 2', to=(-26.96, 32.2), rot=0.0, standing=False),
    dict(name='Waiting passenger 7', to=(-24.85, 18.6), rot=90.0, standing=True),
]
R = dict(status='RUNNING', moved=[])


def main():
    assert u.EditorLoadingAndSavingUtils.load_map(MAP)
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    EA = u.get_editor_subsystem(u.EditorActorSubsystem)
    acts = {a.get_actor_label(): a for a in EA.get_all_level_actors()}
    for m in MOVES:
        body, proxy = acts['CH12 ' + m['name']], acts['CH12COLL ' + m['name']]
        b0, p0 = body.get_actor_location(), proxy.get_actor_location()
        x, y = m['to']
        body.set_actor_location(u.Vector(x * 100, -y * 100, b0.z), False, True)
        body.set_actor_rotation(u.Rotator(0, 0, -m['rot']), False)
        pz = 90.0 if m['standing'] else (p0.z - b0.z)
        proxy.set_actor_location(u.Vector(x * 100, -y * 100, b0.z + pz), False, True)
        proxy.set_actor_rotation(u.Rotator(0, 0, -m['rot']), False)
        if m['standing']:
            s = proxy.get_actor_scale3d()
            proxy.set_actor_scale3d(u.Vector(s.x, s.y, s.z * 90.0 / 80.0))
        R['moved'].append(dict(name=m['name'], from_m=[round(b0.x / 100, 2), round(-b0.y / 100, 2)], to_m=[x, y],
                               yaw=-m['rot'], standing=m['standing']))
    assert u.EditorLoadingAndSavingUtils.save_map(world, MAP), 'save_map failed'
    R['status'] = 'SUCCESS'


try:
    main()
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'Gate08_47.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
print('GATE08_47', R['status'])
