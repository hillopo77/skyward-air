"""Pass50: hand the lighting to Lumen (-run=pythonscript). MUTATES AND SAVES the level.

The project now asks for Lumen global illumination and reflections
(Config/DefaultEngine.ini, changed beside this script). Here the level is
made to follow it: no post-process volume may force another GI or reflection
method, and every light and sky light is reported (mobility, intensity,
cast shadows) so they can be retuned for bounce light. Lumen's own short-range
AO replaces most of what the Pass48 SSAO boost did, so SSAO is eased back to
Lumen50.json's value.
"""
import unreal as u, json, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAP = '/Game/Airport38/L_Airport_Repair38'
SPEC = json.loads((HERE / 'Lumen50.json').read_text(encoding='utf-8'))
R = dict(status='RUNNING', volumes=[], lights={}, skylights=[])


def main():
    assert u.EditorLoadingAndSavingUtils.load_map(MAP)
    actors = u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
    for a in actors:
        if isinstance(a, u.PostProcessVolume):
            s = a.get_editor_property('settings')
            before = dict(gi=bool(s.get_editor_property('override_dynamic_global_illumination_method')),
                          refl=bool(s.get_editor_property('override_reflection_method')),
                          ao=round(s.get_editor_property('ambient_occlusion_intensity'), 3))
            s.set_editor_property('override_dynamic_global_illumination_method', False)
            s.set_editor_property('override_reflection_method', False)
            if s.get_editor_property('override_ambient_occlusion_intensity'):
                s.set_editor_property('ambient_occlusion_intensity', SPEC['ssao_intensity'])
            for k, v in SPEC.get('volume', {}).items():
                s.set_editor_property('override_' + k, True)
                s.set_editor_property(k, v)
            a.set_editor_property('settings', s)
            R['volumes'].append(dict(label=a.get_actor_label(), unbound=bool(a.get_editor_property('unbound')), **before))
        elif isinstance(a, u.SkyLight):
            c = a.get_component_by_class(u.SkyLightComponent)
            R['skylights'].append(dict(label=a.get_actor_label(), mobility=str(c.get_editor_property('mobility')),
                                       intensity=c.get_editor_property('intensity'),
                                       real_time=bool(c.get_editor_property('real_time_capture'))))
        elif isinstance(a, u.Light):
            c = a.get_component_by_class(u.LightComponent)
            k = '%s/%s' % (type(a).__name__, str(c.get_editor_property('mobility')).split('.')[-1])
            e = R['lights'].setdefault(k, dict(count=0, intensity=[], shadows=0))
            e['count'] += 1; e['intensity'].append(round(c.get_editor_property('intensity'), 2))
            e['shadows'] += bool(c.get_editor_property('cast_shadows'))
    for e in R['lights'].values():
        e['intensity'] = sorted(set(e['intensity']))[:12]
    assert u.EditorLoadingAndSavingUtils.save_current_level()
    R['status'] = 'SUCCESS'


try:
    main()
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'Lumen50Report.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
print('LUMEN50', R['status'])
