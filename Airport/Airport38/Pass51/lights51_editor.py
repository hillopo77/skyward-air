"""Pass51: light the landside hall like a place, not a gym (-run=pythonscript).
MUTATES AND SAVES the level.

Exposure is fixed for the whole map and there is no GI, so the sky fill lit
every surface of the hall the same and twelve identical downlights added an
even wash on top. From Lights51.json:
  grade      the hall's three room volumes: less flat ambient fill (the
             uplights and accents carry the light instead), warmer white
             balance, vignette, more AO and bloom (so the lit signs and runway
             lights glow); exposure stays at the level's EV 6.5 so no door
             pops; originals kept in HallLights51.orig.json
  floor      the terrazzo tinted warmer and a little darker, against glare
  downlights the twelve hall downlights warmer and dimmer; their original
             values are kept in HallLights51.orig.json, so a re-run is absolute
  Pass53: one warm, even fill. The room grade's ambient fill is warm and
  stronger, white balance warm (7200 K), contrast eased; the ceiling lights are
  gentle (2900 K), soft-shadowed and shielded by barn doors so they don't
  light up the slats beside them; one low glow under the check-in canopy.
  No uplights, washes or accents.
  accents    (Pass52, superseded) softer: no free-floating spots. Every added light comes
             from something visible: a glow under the check-in canopy, a wash
             on the check-in back wall, a light in the security portal header,
             and four wide uplights per side on the cove ledges, tilted off the
             wall onto the wave ceiling. Anything that could reach another
             room casts shadows, with low-resolution (soft) shadow maps.
Every new actor is labelled 'P51 ...' and replaced on a re-run.
"""
import unreal as u, json, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAP = '/Game/Airport38/L_Airport_Repair38'
SPEC = json.loads((HERE / 'Lights51.json').read_text(encoding='utf-8'))
ORIG = HERE / 'HallLights51.orig.json'
FOLDER = 'Lighting/Pass51'
R = dict(status='RUNNING', downlights=[], spawned=[])


def ue(p):
    return u.Vector(p[0] * 100, -p[1] * 100, p[2] * 100)


def common(c, lm, temp, att, shadows):
    c.set_editor_property('intensity_units', u.LightUnits.LUMENS)
    c.set_editor_property('intensity', float(lm))
    c.set_editor_property('use_temperature', True)
    c.set_editor_property('temperature', float(temp))
    c.set_editor_property('attenuation_radius', float(att))
    c.set_editor_property('cast_shadows', bool(shadows))


def main():
    assert u.EditorLoadingAndSavingUtils.load_map(MAP)
    EA = u.get_editor_subsystem(u.EditorActorSubsystem)
    x0, x1, y0, y1 = SPEC['hall']
    for a in EA.get_all_level_actors():
        if a.get_actor_label().startswith('P51 '):
            EA.destroy_actor(a)
    orig = json.loads(ORIG.read_text(encoding='utf-8')) if ORIG.exists() else {}
    mobility = None
    for a in EA.get_all_level_actors():
        if not isinstance(a, u.RectLight):
            continue
        p = a.get_actor_location()
        sx, sy, sz = p.x / 100, -p.y / 100, p.z / 100
        if x0 < sx < x1 and y0 < sy < y1 and sz > 5.5:
            c = a.get_component_by_class(u.LightComponent)
            lab = a.get_actor_label()
            o = orig.setdefault(lab, {})
            for k in ('intensity', 'temperature', 'source_width', 'source_height', 'attenuation_radius', 'shadow_resolution_scale'):
                o.setdefault(k, c.get_editor_property(k))       # first value seen is the original
            d = SPEC.get('downlight')
            if d:                                                # Pass52: one even, soft set
                c.set_editor_property('intensity', float(d['lm']))
                c.set_editor_property('temperature', float(d['temp']))
                c.set_editor_property('source_width', float(d['w']))
                c.set_editor_property('source_height', float(d['h']))
                c.set_editor_property('attenuation_radius', float(d['att']))
                c.set_editor_property('shadow_resolution_scale', float(d['shadow_res']))
                if 'z' in d:                                     # below the deepest slat, so no slat flares
                    o.setdefault('z', sz)
                    a.set_actor_location(u.Vector(p.x, p.y, d['z'] * 100), False, False)
                if 'shadow_margin' in d:                         # only lights near a wall need shadows (no leaks)
                    near = min(sx - x0, x1 - sx, sy - y0, y1 - sy) < d['shadow_margin']
                    o.setdefault('cast_shadows', c.get_editor_property('cast_shadows'))
                    c.set_editor_property('cast_shadows', bool(near))
                if 'barn_angle' in d:                            # shield the slats next to each light
                    for k in ('barn_door_angle', 'barn_door_length'):
                        o.setdefault(k, c.get_editor_property(k))
                    c.set_editor_property('barn_door_angle', float(d['barn_angle']))
                    c.set_editor_property('barn_door_length', float(d['barn_length']))
            else:
                c.set_editor_property('intensity', o['intensity'] * SPEC['downlight_scale'])
                c.set_editor_property('temperature', float(SPEC['downlight_temp']))
            mobility = c.get_editor_property('mobility')
            R['downlights'].append([lab, round(o['intensity']), round(c.get_editor_property('intensity'))])
    t = SPEC.get('tall_rooms')
    if t:                                                        # Pass53: the other tall rooms' lifted lights
        for a in EA.get_all_level_actors():
            if not isinstance(a, u.RectLight):
                continue
            p = a.get_actor_location()
            sx, sy, sz = p.x / 100, -p.y / 100, p.z / 100
            if sz > 5.5 and any(h[0] < sx < h[1] and h[2] < sy < h[3] for h in t['halls']):
                c = a.get_component_by_class(u.LightComponent)
                o = orig.setdefault(a.get_actor_label(), {})
                for k in ('attenuation_radius', 'shadow_resolution_scale', 'barn_door_angle', 'barn_door_length'):
                    o.setdefault(k, c.get_editor_property(k))
                o.setdefault('z', sz)
                if 'z' in t:
                    a.set_actor_location(u.Vector(p.x, p.y, t['z'] * 100), False, False)
                c.set_editor_property('attenuation_radius', float(t['att']))
                c.set_editor_property('shadow_resolution_scale', float(t['shadow_res']))
                c.set_editor_property('barn_door_angle', float(t['barn_angle']))
                c.set_editor_property('barn_door_length', float(t['barn_length']))
                R.setdefault('tall_room_lights', []).append(a.get_actor_label())
    if SPEC.get('sun_veil'):                                     # Pass53: shadow-only, never seen
        for a in EA.get_all_level_actors():
            if a.get_actor_label() == SPEC['sun_veil']:
                c = a.static_mesh_component
                c.set_editor_property('cast_shadow', True)
                c.set_editor_property('cast_hidden_shadow', True)
                c.set_editor_property('hidden_in_game', True)
                c.set_editor_property('affect_distance_field_lighting', False)
                R['sun_veil'] = a.get_actor_label()
    ORIG.write_text(json.dumps(orig, indent=1), encoding='utf-8')
    R['mobility'] = str(mobility)

    for s in SPEC['spots']:
        rot = u.MathLibrary.find_look_at_rotation(ue(s['p']), ue(s['at']))
        a = EA.spawn_actor_from_class(u.SpotLight, ue(s['p']), rot)
        a.set_actor_label(s['label']); a.set_folder_path(FOLDER)
        c = a.get_component_by_class(u.SpotLightComponent)
        if mobility is not None:
            c.set_editor_property('mobility', mobility)
        common(c, s['lm'], s.get('temp', 3000), s.get('att', 800), s.get('shadows', True))
        c.set_editor_property('outer_cone_angle', float(s['outer']))
        c.set_editor_property('inner_cone_angle', float(s['inner']))
        c.set_editor_property('source_radius', 4.0)
        R['spawned'].append(s['label'])
    for s in SPEC['rects']:
        rot = u.Rotator(0, 90, 0) if s.get('up') else u.MathLibrary.find_look_at_rotation(ue(s['p']), ue(s['at']))
        a = EA.spawn_actor_from_class(u.RectLight, ue(s['p']), rot)
        a.set_actor_label(s['label']); a.set_folder_path(FOLDER)
        c = a.get_component_by_class(u.RectLightComponent)
        if mobility is not None:
            c.set_editor_property('mobility', mobility)
        common(c, s['lm'], s.get('temp', 3000), s.get('att', 800), s.get('shadows', False))
        if 'shadow_res' in s:                                    # low-res shadow maps filter to soft edges
            c.set_editor_property('shadow_resolution_scale', float(s['shadow_res']))
        c.set_editor_property('source_width', float(s['w']))
        c.set_editor_property('source_height', float(s['h']))
        R['spawned'].append(s['label'])

    # The grade goes on the hall's own room volumes (a volume spawned from
    # Python has no brush, so it never contains the camera).
    g = SPEC['ppv']
    keys = dict(auto_exposure_min_brightness=g['exposure'], auto_exposure_max_brightness=g['exposure'],
                white_temp=g['white_temp'], vignette_intensity=g['vignette'], bloom_intensity=g['bloom'],
                ambient_occlusion_intensity=g['ao'], ambient_occlusion_radius=g['ao_radius'],
                ambient_cubemap_intensity=g['ambient_cubemap'])
    if 'ambient_tint' in g:                                      # Pass53: a warm fill, not a neutral one
        keys['ambient_cubemap_tint'] = u.LinearColor(*g['ambient_tint'], 1)
    if 'contrast' in g:
        keys['color_contrast'] = u.Vector4(g['contrast'], g['contrast'], g['contrast'], 1)
    vol_orig = orig.setdefault('_volumes', {})
    for a in EA.get_all_level_actors():
        if isinstance(a, u.PostProcessVolume) and a.get_actor_label() in g['volumes']:
            st = a.get_editor_property('settings')
            lab = a.get_actor_label()
            for k in keys:                      # first value seen per key is the original
                v0 = st.get_editor_property(k)
                vol_orig.setdefault(lab, {}).setdefault(k, [bool(st.get_editor_property('override_' + k)),
                                                            v0 if isinstance(v0, (int, float)) else str(v0)])
            for k, v in keys.items():
                st.set_editor_property('override_' + k, True)
                st.set_editor_property(k, v if isinstance(v, (u.LinearColor, u.Vector4)) else float(v))
            a.set_editor_property('settings', st)
            R.setdefault('graded', []).append(lab)
    # A warmer, less glaring terrazzo (every terminal floor uses this one instance).
    f = SPEC.get('floor')
    if f:
        mi = u.load_asset(f['material'])
        ML = u.MaterialEditingLibrary
        if '_floor_tint' not in orig:
            c = ML.get_material_instance_vector_parameter_value(mi, 'Tint')
            orig['_floor_tint'] = [c.r, c.g, c.b]
        ML.set_material_instance_vector_parameter_value(mi, 'Tint', u.LinearColor(*f['tint'], 1))
        assert u.EditorAssetLibrary.save_loaded_asset(mi)
        R['floor_tint'] = [orig['_floor_tint'], f['tint']]
    ORIG.write_text(json.dumps(orig, indent=1), encoding='utf-8')
    assert u.EditorLoadingAndSavingUtils.save_current_level()
    R['status'] = 'SUCCESS'


try:
    main()
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'Lights51Report.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
print('LIGHTS51', R['status'])
