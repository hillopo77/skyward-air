"""Pass69: read-only inventory for the cabin lighting redesign (-run=pythonscript, no save).

Writes Pass51/Cabin69Inspect.json:
  pp       every PostProcessVolume: label, unbound, priority, blend, extent, and the
           bloom / exposure / AO / ambient-cubemap settings that are overridden
  lights   every light inside the cabin box (or labelled Cabin / PSU / P58 / P66):
           class, location (source m), rotation, intensity + units, source size,
           attenuation, temperature, shadows, mobility
  meshes   every distinct static mesh inside the cabin box: actor count, an example
           label, bounds size, and each material slot's name and material
  sun      the directional light's shadow settings
"""
import unreal as u, json, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
BOX = ((12.9, -1.5, -0.6), (19.1, 30.5, 3.4))           # source metres: the cabin, at the gate
R = dict(status='RUNNING', pp=[], lights=[], meshes={}, sun=[])


def src(v):
    return [round(v.x / 100, 3), round(-v.y / 100, 3), round(v.z / 100, 3)]


def inside(p):
    return all(BOX[0][i] <= p[i] <= BOX[1][i] for i in range(3))


def prop(o, n):
    try:
        v = o.get_editor_property(n)
        return v if isinstance(v, (int, float, bool, str)) or v is None else str(v)
    except Exception:
        return '?'


try:
    assert u.EditorLoadingAndSavingUtils.load_map('/Game/Airport38/L_Airport_Repair38')
    actors = u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
    for a in actors:
        lab = a.get_actor_label()
        if isinstance(a, u.PostProcessVolume):
            s = a.get_editor_property('settings')
            keys = {}
            for n in ('bloom_intensity', 'bloom_threshold', 'auto_exposure_method', 'auto_exposure_bias', 'auto_exposure_min_brightness',
                      'auto_exposure_max_brightness', 'auto_exposure_apply_physical_camera_exposure', 'ambient_occlusion_intensity',
                      'ambient_occlusion_radius', 'ambient_occlusion_static_fraction', 'ambient_cubemap_intensity', 'indirect_lighting_intensity',
                      'white_temp', 'color_saturation', 'vignette_intensity', 'film_toe', 'film_shoulder'):
                if prop(s, 'override_' + n) is True:
                    keys[n] = prop(s, n)
            o, e = a.get_actor_bounds(False)
            R['pp'].append(dict(label=lab, unbound=prop(a, 'unbound'), priority=prop(a, 'priority'), blend=prop(a, 'blend_weight'),
                                centre=src(o), half=[round(e.x / 100, 1), round(e.y / 100, 1), round(e.z / 100, 1)], overrides=keys))
        elif isinstance(a, u.Light):
            p = src(a.get_actor_location())
            if not (inside(p) or any(k in lab for k in ('Cabin', 'PSU', 'P58', 'P66'))):
                continue
            c = a.get_component_by_class(u.LightComponent)
            r = a.get_actor_rotation()
            d = dict(label=lab, cls=a.get_class().get_name(), p=p, rot=[round(r.roll, 1), round(r.pitch, 1), round(r.yaw, 1)],
                     i=prop(c, 'intensity'), units=prop(c, 'intensity_units'), shadows=prop(c, 'cast_shadows'),
                     mob=prop(c, 'mobility'), temp=prop(c, 'temperature'), use_temp=prop(c, 'use_temperature'),
                     att=prop(c, 'attenuation_radius'), visible=prop(c, 'visible'), tags=[str(t) for t in a.tags])
            for n in ('source_width', 'source_height', 'barn_door_angle', 'barn_door_length', 'source_radius', 'soft_source_radius',
                      'inner_cone_angle', 'outer_cone_angle', 'specular_scale'):
                v = prop(c, n)
                if v != '?':
                    d[n] = v
            par = a.get_attach_parent_actor()
            d['parent'] = par.get_actor_label() if par else None
            R['lights'].append(d)
        elif isinstance(a, u.DirectionalLight):
            c = a.get_component_by_class(u.LightComponent)
            R['sun'].append({n: prop(c, n) for n in ('intensity', 'mobility', 'cast_shadows', 'dynamic_shadow_distance_stationary_light',
                                                    'light_source_angle', 'shadow_sharpen', 'cast_dynamic_shadows', 'contact_shadow_length')})
        elif isinstance(a, u.StaticMeshActor):
            o, e = a.get_actor_bounds(False)
            p = src(o)
            if not inside(p):
                continue
            c = a.static_mesh_component
            m = c.static_mesh if c else None
            if not m:
                continue
            k = m.get_name()
            rec = R['meshes'].setdefault(k, dict(n=0, example=lab, size=[round(e.x / 50, 2), round(e.y / 50, 2), round(e.z / 50, 2)],
                                                  hidden=prop(c, 'hidden_in_game'), slots=[]))
            rec['n'] += 1
            if not rec['slots']:
                names = [str(n) for n in c.get_material_slot_names()]
                for i in range(c.get_num_materials()):
                    mat = c.get_material(i)
                    rec['slots'].append([names[i] if i < len(names) else str(i), mat.get_path_name() if mat else None])
    R['status'] = 'SUCCESS'
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'Cabin69Inspect.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
print('CABIN69INSPECT', R['status'])
