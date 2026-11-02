"""Pass60 test: volumetric fog on the warm haze, sun scattering with volumetric
shadow. MUTATES AND SAVES the level (values recorded in FogTest60.json)."""
import unreal as u, json, traceback
from pathlib import Path
HERE = Path(__file__).resolve().parent
A = json.loads((HERE / 'FogTest60.args.json').read_text())
R = dict(status='RUNNING', args=A)
try:
    assert u.EditorLoadingAndSavingUtils.load_map('/Game/Airport38/L_Airport_Repair38')
    for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
        if a.get_actor_label() == 'P55 warm haze':
            c = a.get_component_by_class(u.ExponentialHeightFogComponent)
            for k, v in A['fog'].items():
                c.set_editor_property(k, v)
            R['fog'] = True
        elif isinstance(a, u.DirectionalLight):
            c = a.get_component_by_class(u.LightComponent)
            for k, v in A['sun'].items():
                c.set_editor_property(k, v)
            R['sun'] = True
    assert u.EditorLoadingAndSavingUtils.save_current_level()
    R['status'] = 'SUCCESS'
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'FogTest60.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
print('FOGTEST60', R['status'])
