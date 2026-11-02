"""Pass56: the sun's shadows on the building come from the bake (soft, 5 degree
source) instead of being drawn live as razor-sharp cascades (-run=pythonscript).
MUTATES AND SAVES the level. Only the directional light's dynamic shadow
distance changes (to 0); people and moving things still get live per-object
shadows. The previous value is in Bake55.orig.json ('sun')."""
import unreal as u, json, traceback
from pathlib import Path
HERE = Path(__file__).resolve().parent
R = dict(status='RUNNING')
try:
    assert u.EditorLoadingAndSavingUtils.load_map('/Game/Airport38/L_Airport_Repair38')
    for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
        if isinstance(a, u.DirectionalLight):
            c = a.get_component_by_class(u.LightComponent)
            R['before'] = c.get_editor_property('dynamic_shadow_distance_stationary_light')
            c.set_editor_property('dynamic_shadow_distance_stationary_light', 0.0)
            R['sun'] = a.get_actor_label()
    assert u.EditorLoadingAndSavingUtils.save_current_level()
    R['status'] = 'SUCCESS'
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'SunSoft56.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
print('SUNSOFT56', R['status'])
