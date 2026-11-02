"""Pass51: read-only dump of the landside hall lighting (-run=pythonscript).

Every light within 12 m of the hall (class, label, source-metre position,
rotation, intensity and units, colour, temperature, attenuation, size, shadows),
the sun, sky light, fog and every post-process volume's exposure, bloom,
grading and AO overrides. Writes Pass51/LightInspect51.json.
"""
import unreal as u, json, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAP = '/Game/Airport38/L_Airport_Repair38'
HALL = [-61, -14, -30, 8]
R = dict(status='RUNNING', lights=[], volumes=[], world=[])


def src(v):
    return [round(v.x / 100, 3), round(-v.y / 100, 3), round(v.z / 100, 3)]


def props(o, names):
    out = {}
    for n in names:
        try:
            v = o.get_editor_property(n)
            out[n] = v if isinstance(v, (int, float, bool, str)) else str(v)
        except Exception:
            pass
    return out


LP = ['intensity', 'intensity_units', 'light_color', 'temperature', 'use_temperature', 'attenuation_radius',
      'source_width', 'source_height', 'source_radius', 'soft_source_radius', 'source_length', 'barn_door_angle',
      'barn_door_length', 'inner_cone_angle', 'outer_cone_angle', 'cast_shadows', 'indirect_lighting_intensity',
      'volumetric_scattering_intensity', 'mobility', 'specular_scale', 'use_inverse_squared_falloff']
PP = ['auto_exposure_method', 'auto_exposure_bias', 'auto_exposure_min_brightness', 'auto_exposure_max_brightness',
      'auto_exposure_apply_physical_camera_exposure', 'bloom_intensity', 'bloom_threshold', 'color_saturation',
      'color_contrast', 'color_gamma', 'color_gain', 'color_offset', 'white_temp', 'white_tint', 'vignette_intensity',
      'ambient_occlusion_intensity', 'ambient_occlusion_radius', 'film_slope', 'film_toe', 'film_shoulder',
      'film_black_clip', 'film_white_clip', 'indirect_lighting_intensity', 'dynamic_global_illumination_method',
      'reflection_method', 'sharpen', 'local_exposure_contrast_scale', 'local_exposure_highlight_contrast_scale',
      'local_exposure_shadow_contrast_scale', 'scene_color_tint']


def main():
    assert u.EditorLoadingAndSavingUtils.load_map(MAP)
    for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
        try:
            if isinstance(a, u.PostProcessVolume):
                s = a.get_editor_property('settings')
                o, e = a.get_actor_bounds(False)
                row = dict(label=a.get_actor_label(), priority=a.get_editor_property('priority'),
                           blend_radius=a.get_editor_property('blend_radius'), blend_weight=a.get_editor_property('blend_weight'),
                           unbound=a.get_editor_property('unbound'), c=src(o), e=[round(e.x / 100, 2), round(e.y / 100, 2), round(e.z / 100, 2)], set={})
                for k in PP:
                    try:
                        if s.get_editor_property('override_' + k):
                            v = s.get_editor_property(k)
                            row['set'][k] = v if isinstance(v, (int, float, bool, str)) else str(v)
                    except Exception:
                        pass
                R['volumes'].append(row)
                continue
            comp = a.get_component_by_class(u.LightComponent)
            if not comp:
                if isinstance(a, (u.SkyLight, u.ExponentialHeightFog, u.SkyAtmosphere)):
                    c = a.get_component_by_class(u.ActorComponent)
                    R['world'].append(dict(label=a.get_actor_label(), cls=a.get_class().get_name()))
                continue
            p = src(comp.get_world_location())
            cls = a.get_class().get_name()
            row = dict(label=a.get_actor_label(), cls=cls, p=p, rot=str(comp.get_world_rotation()), **props(comp, LP))
            if cls in ('DirectionalLight', 'SkyLight') or (HALL[0] <= p[0] <= HALL[1] and HALL[2] <= p[1] <= HALL[3]):
                R['lights' if cls not in ('DirectionalLight',) else 'world'].append(row)
        except Exception as ex:
            R.setdefault('errors', []).append(str(ex))
    for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
        if isinstance(a, u.SkyLight):
            c = a.get_component_by_class(u.SkyLightComponent)
            R['world'].append(dict(label=a.get_actor_label(), cls='SkyLight', **props(c, ['intensity', 'light_color', 'source_type', 'indirect_lighting_intensity', 'lower_hemisphere_color', 'mobility', 'real_time_capture'])))
    R['status'] = 'SUCCESS'


try:
    main()
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'LightInspect51.json').write_text(json.dumps(R, indent=1, default=str), encoding='utf-8')
print('LIGHTINSPECT51', R['status'])
