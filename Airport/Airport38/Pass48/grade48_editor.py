"""Pass48: atmosphere grade (-run=pythonscript).

The renderer has no global illumination (r.DynamicGlobalIlluminationMethod=0),
so rooms read flat: nothing darkens where surfaces meet. Screen-space ambient
occlusion is a post-process setting, not a renderer change; it is switched on
raised in the unbound daylight grade (with a soft bloom and a light vignette)
and in every room grade that overrides it with a weaker value. Reports every volume's relevant settings
before and after. With Grade48Mode.txt = 'read' it only reports.
MUTATES AND SAVES the level otherwise.
"""
import unreal as u, json, traceback
from pathlib import Path
HERE = Path(__file__).resolve().parent
MAP = '/Game/Airport38/L_Airport_Repair38'
KEYS = ['ambient_occlusion_intensity', 'ambient_occlusion_radius', 'ambient_occlusion_static_fraction', 'bloom_intensity',
        'vignette_intensity', 'auto_exposure_bias', 'color_saturation', 'color_contrast', 'scene_color_tint', 'white_temp']
SET = dict(ambient_occlusion_intensity=.55, ambient_occlusion_radius=110.0, ambient_occlusion_static_fraction=0.0,
           bloom_intensity=.3, vignette_intensity=.25)
R = dict(status='RUNNING', before={}, after={})


def report(v):
    s = v.get_editor_property('settings')
    out = dict(priority=v.get_editor_property('priority'), unbound=v.get_editor_property('unbound'))
    for k in KEYS:
        try:
            if s.get_editor_property('override_' + k):
                val = s.get_editor_property(k)
                out[k] = val if isinstance(val, (int, float, bool)) else str(val)
        except Exception:
            pass
    return out


try:
    mode = (HERE / 'Grade48Mode.txt').read_text().strip() if (HERE / 'Grade48Mode.txt').exists() else 'write'
    assert u.EditorLoadingAndSavingUtils.load_map(MAP)
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    vols = [a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors() if isinstance(a, u.PostProcessVolume)]
    for v in vols:
        R['before'][v.get_actor_label()] = report(v)
    if mode != 'read':
        for v in vols:
            s = v.get_editor_property('settings')
            lab = v.get_actor_label()
            if lab == 'Airport clean daylight grade':
                todo = SET
            elif s.get_editor_property('override_ambient_occlusion_intensity'):
                # room grades override AO with weaker values; lift them to the same depth
                todo = dict(ambient_occlusion_intensity=SET['ambient_occlusion_intensity'],
                            ambient_occlusion_radius=SET['ambient_occlusion_radius'])
            else:
                continue
            for k, val in todo.items():
                s.set_editor_property('override_' + k, True)
                s.set_editor_property(k, val)
            v.set_editor_property('settings', s)
            R['after'][lab] = report(v)
        assert u.EditorLoadingAndSavingUtils.save_map(world, MAP)
    R['status'] = 'SUCCESS'
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'Grade48.json').write_text(json.dumps(R, indent=1, default=str), encoding='utf-8')
