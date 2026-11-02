"""Pass54: one warm, hazy light for the whole airport, sun rays through the
windows, and back-to-back seats in the middle of the hall (-run=pythonscript).
MUTATES AND SAVES the level. Every original value is kept in Atmos54.orig.json
(first run wins), so a re-run sets absolute values.

From Atmos54.json:
  grade     every room grade (the 'AP38 warm grade' volumes and the older room
            grades) and the unbound daylight grades get the same warm fill,
            white balance, contrast, AO and bloom, so rooms match each other
            and the outside
  lights    every interior ceiling light ('AP38 practical') warm white, so
            the artificial light reads as the same family as the late sun
  haze      one exponential height fog with volumetric fog: a light warm haze
            outside and in, in which the sun coming through the windows shows
            as shafts (the directional light's volumetric scattering is raised;
            ceiling lights scatter only a little, so they don't bloom)
  veil      the Pass53 clerestory sun veil is removed: the sun may come in
  seats     each named bench that now stands free in the hall gets a twin,
            back to back, turned 180 degrees
"""
import unreal as u, json, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAP = '/Game/Airport38/L_Airport_Repair38'
SPEC = json.loads((HERE / 'Atmos54.json').read_text(encoding='utf-8'))
ORIG = HERE / 'Atmos54.orig.json'
R = dict(status='RUNNING', graded=[], lights=0, seats=[], removed=[])


def plain(v):
    return v if isinstance(v, (int, float, bool, str)) else str(v)


def val(k, v):
    if isinstance(v, list) and k.endswith('tint'):
        return u.LinearColor(*v, 1)
    if isinstance(v, list):
        return u.Vector4(*v, 1)
    return float(v)


def grade(a, keys, orig):
    st = a.get_editor_property('settings')
    o = orig.setdefault('volumes', {}).setdefault(a.get_actor_label(), {})
    for k, v in keys.items():
        o.setdefault(k, [bool(st.get_editor_property('override_' + k)), plain(st.get_editor_property(k))])
        st.set_editor_property('override_' + k, True)
        st.set_editor_property(k, val(k, v))
    a.set_editor_property('settings', st)
    R['graded'].append(a.get_actor_label())


def main():
    assert u.EditorLoadingAndSavingUtils.load_map(MAP)
    EA = u.get_editor_subsystem(u.EditorActorSubsystem)
    orig = json.loads(ORIG.read_text(encoding='utf-8')) if ORIG.exists() else {}
    actors = EA.get_all_level_actors()
    for a in actors:
        lab = a.get_actor_label()
        if lab.startswith('P54 '):
            EA.destroy_actor(a)
        elif lab in SPEC.get('remove', []):
            EA.destroy_actor(a); R['removed'].append(lab)
    actors = EA.get_all_level_actors()
    g = SPEC['grade']
    for a in actors:
        if not isinstance(a, u.PostProcessVolume):
            continue
        lab = a.get_actor_label()
        if a.get_editor_property('unbound'):
            grade(a, g['outdoor'], orig)
        elif any(lab.startswith(p) for p in g['room_prefixes']):
            keys = dict(g['room'])
            keys.update(g.get('room_overrides', {}).get(lab, {}))
            grade(a, keys, orig)
    L = SPEC['lights']
    lo = orig.setdefault('lights', {})
    for a in actors:
        if isinstance(a, u.Light) and not isinstance(a, u.DirectionalLight) and a.get_actor_label().startswith(L['prefix']):
            c = a.get_component_by_class(u.LightComponent)
            o = lo.setdefault(a.get_actor_label(), {})
            for k in ('temperature', 'use_temperature', 'volumetric_scattering_intensity'):
                o.setdefault(k, plain(c.get_editor_property(k)))
            c.set_editor_property('use_temperature', True)
            c.set_editor_property('temperature', float(L['temp']))
            c.set_editor_property('volumetric_scattering_intensity', float(L['volumetric']))
            R['lights'] += 1
    s = SPEC['sun']
    for a in actors:
        if isinstance(a, u.DirectionalLight):
            c = a.get_component_by_class(u.LightComponent)
            o = orig.setdefault('sun', {})
            for k in ('volumetric_scattering_intensity', 'temperature', 'use_temperature', 'intensity'):
                o.setdefault(k, plain(c.get_editor_property(k)))
            c.set_editor_property('volumetric_scattering_intensity', float(s['volumetric']))
            c.set_editor_property('use_temperature', True)
            c.set_editor_property('temperature', float(s['temp']))
            if s.get('volumetric_shadow'):                      # beams, not an evenly lit haze
                o.setdefault('cast_volumetric_shadow', plain(c.get_editor_property('cast_volumetric_shadow')))
                c.set_editor_property('cast_volumetric_shadow', True)
            R['sun'] = a.get_actor_label()
        elif isinstance(a, u.SkyLight) and SPEC.get('sky'):
            c = a.get_component_by_class(u.SkyLightComponent)
            o = orig.setdefault('sky', {})
            o.setdefault('volumetric_scattering_intensity', plain(c.get_editor_property('volumetric_scattering_intensity')))
            c.set_editor_property('volumetric_scattering_intensity', float(SPEC['sky']['volumetric']))
            R['sky'] = a.get_actor_label()
    f = SPEC['haze']
    a = EA.spawn_actor_from_class(u.ExponentialHeightFog, u.Vector(0, 0, f['z'] * 100), u.Rotator(0, 0, 0))
    a.set_actor_label('P54 warm haze'); a.set_folder_path('Lighting/Pass54')
    c = a.get_component_by_class(u.ExponentialHeightFogComponent)
    for k, v in f['props'].items():
        v = u.LinearColor(*v, 1) if isinstance(v, list) else (bool(v) if isinstance(v, bool) else float(v))
        for name in (k, k.replace('luminance', 'color')):       # older engines call it inscattering_color
            try:
                c.set_editor_property(name, v); break
            except Exception as e:
                err = str(e)
        else:
            R.setdefault('notes', []).append('haze %s: %s' % (k, err))
    for prop in SPEC['seats']:
        src = next((x for x in actors if x.get_actor_label() == prop['label']), None)
        if not src:
            R.setdefault('notes', []).append('no seat ' + prop['label']); continue
        p, r = src.get_actor_location(), src.get_actor_rotation()
        dx, dy = prop['offset']
        twin = EA.spawn_actor_from_class(u.StaticMeshActor, u.Vector(p.x + dx * 100, p.y - dy * 100, p.z),
                                         u.Rotator(r.roll, r.pitch, r.yaw + 180))
        twin.set_actor_label('P54 ' + prop['label'] + ' twin'); twin.set_folder_path(str(src.get_folder_path()))
        twin.set_actor_scale3d(src.get_actor_scale3d())
        sc, tc = src.static_mesh_component, twin.static_mesh_component
        tc.set_static_mesh(sc.static_mesh)
        for i in range(sc.get_num_materials()):
            tc.set_material(i, sc.get_material(i))
        tc.set_mobility(sc.mobility)
        tc.set_collision_profile_name(sc.get_collision_profile_name())
        tc.set_collision_enabled(sc.get_collision_enabled())
        R['seats'].append([prop['label'], round(r.yaw, 1)])
    ORIG.write_text(json.dumps(orig, indent=1), encoding='utf-8')
    assert u.EditorLoadingAndSavingUtils.save_current_level()
    R['status'] = 'SUCCESS'


try:
    main()
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'Atmos54Report.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
print('ATMOS54', R['status'])
