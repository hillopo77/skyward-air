"""Pass47 level fixes, part 2 (-run=pythonscript). MUTATES AND SAVES.

1. Ceilings. Every fixture points down and this renderer has no bounce light,
   so ceilings read mid-grey (0.42-0.56) under near-white walls. The ceiling
   material already has an Emission scalar; trialled live at 0 / 0.2 / 0.4 /
   0.7 / 5 / 15 / 40 (Look47), 15 brings ceilings up to about wall level
   (check-in 0.42 -> 0.56, concourse 0.46 -> 0.57, corridor 0.56 -> 0.64)
   without outshining the walls; 40 reads as a glowing panel. Set to 15.

2. Two Pass46 flight boards were hung backwards. At yaw 0 this board's screen
   faces south: right for the arrivals board on a north wall, wrong for the
   concourse and landside boards on south walls, which showed their dark backs
   to the room (the landside one reads as a dead black panel). Turned 180.
"""
import unreal as u, json, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAP = '/Game/Airport38/L_Airport_Repair38'
R = dict(status='RUNNING')


def main():
    mi = u.load_asset('/Game/Airport38/Materials/MI_AP_P43TCeiling')
    ML = u.MaterialEditingLibrary
    R['ceiling_emission_before'] = ML.get_material_instance_scalar_parameter_value(mi, 'Emission')
    ML.set_material_instance_scalar_parameter_value(mi, 'Emission', 15.0)
    u.EditorAssetLibrary.save_loaded_asset(mi)
    R['ceiling_emission_after'] = ML.get_material_instance_scalar_parameter_value(mi, 'Emission')

    assert u.EditorLoadingAndSavingUtils.load_map(MAP)
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    EA = u.get_editor_subsystem(u.EditorActorSubsystem)
    R['boards'] = []
    for a in EA.get_all_level_actors():
        try:
            n = a.get_actor_label()
        except Exception:
            continue
        if n in ('Concourse departures board46', 'Landside departures board46'):
            before = a.get_actor_rotation().yaw
            o0 = a.get_actor_location()
            a.set_actor_rotation(u.Rotator(0, 0, before + 180.0), False)
            a.set_actor_location(o0, False, True)
            R['boards'].append(dict(actor=n, yaw_before=round(before, 1),
                                    yaw_after=round(a.get_actor_rotation().yaw, 1)))
    assert len(R['boards']) == 2, R['boards']
    assert u.EditorLoadingAndSavingUtils.save_map(world, MAP), 'save_map failed'
    R['status'] = 'SUCCESS'


try:
    main()
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'Fix47b.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
print('FIX47B', R['status'])
