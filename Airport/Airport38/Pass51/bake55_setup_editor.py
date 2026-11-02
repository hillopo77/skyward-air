"""Pass55: strip every fake and set the level up for real, baked lighting
(-run=pythonscript). MUTATES AND SAVES the level and some mesh assets.

The level had no global illumination: a movable sky light lit every surface
straight through the roofs, every room grade added a flat 'ambient cubemap'
glow, and Pass51-54 added accent lights, a canopy glow, a haze and fake sun
shafts on top. Lightmass (installed, static lighting allowed) computes real
bounce from real sources instead. This script:

  strip    destroys every Pass51-54 light, the haze and the sun-shaft mesh;
           switches the ambient-cubemap fill off on every post-process volume;
           grades go back to plain (neutral-warm white balance, light AO)
  sources  the terminal's own fittings ('AP38 practical', at their fixtures)
           become STATIC area lights, 3000 K, soft; the sun and the sky light
           become STATIONARY (baked bounce and sky occlusion, live shadows for
           people and moving things); everything the game moves (the aircraft,
           its lights and crew, the bridge, doors, belts, bags: actors the game
           tags or lists as movable) is set MOVABLE so it is not baked in place
  ambient  (Pass56) a few large soft panels in the tall rooms fill the dark
           spots; the sun's shadow edge is softer (5 degrees); (Pass57) the
           low rooms get panels too, fittings are a neutral 4000 K and bounced
           light keeps only 55% of its colour (the wood was tinting everything)
  bake     a Lightmass importance volume round the terminal and apron; 4
           bounces, baked AO; huge sky domes and hidden collision boxes cast
           no shadow; the architecture meshes get lightmap resolutions sized
           to their area (UVs re-packed at that size), the hall, slats,
           walls and floors 2048 (more runs Lightmass out of memory on 16 GB), the
           rest of the architecture 1024, props with overlapping lightmap UVs re-packed and the sky dome the minimum (Bake55.json)
  dense    meshes too dense for a lightmap (the slat ceilings, the hall shell,
           props with overlapping lightmap UVs) take their light from a finer
           (50 cm) volumetric lightmap instead
  capture  a sphere reflection capture in every room, so floors reflect the room,
           not the sky
Every changed value is kept in Bake55.orig.json (first run wins).
"""
import unreal as u, json, math, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAP = '/Game/Airport38/L_Airport_Repair38'
LAYOUT = HERE.parents[1] / 'Exports' / 'airport_layout.json'
ORIG = HERE / 'Bake55.orig.json'
SPEC = json.loads((HERE / 'Bake55.json').read_text(encoding='utf-8'))
R = dict(status='RUNNING', destroyed=[], static_lights=0, movable=[], no_shadow=[], meshes={}, captures=0, notes=[])
ST, SY, MO = u.ComponentMobility.STATIC, u.ComponentMobility.STATIONARY, u.ComponentMobility.MOVABLE


def src(v):
    return [v.x / 100, -v.y / 100, v.z / 100]


def ue(p):
    return u.Vector(p[0] * 100, -p[1] * 100, p[2] * 100)


def plain(v):
    return v if isinstance(v, (int, float, bool, str)) else str(v)


def keep(orig, group, key, obj, props):
    o = orig.setdefault(group, {}).setdefault(key, {})
    for p in props:
        try:
            o.setdefault(p, plain(obj.get_editor_property(p)))
        except Exception:
            pass


def main():
    assert u.EditorLoadingAndSavingUtils.load_map(MAP)
    EA = u.get_editor_subsystem(u.EditorActorSubsystem)
    orig = json.loads(ORIG.read_text(encoding='utf-8')) if ORIG.exists() else {}
    layout = json.loads(LAYOUT.read_text(encoding='utf-8'))
    moving_labels = {q['actor'] for q in layout['interactions'] if q.get('actor')}
    moving_labels |= {q['name'] for q in layout['conveyors']}

    # ---------------- strip
    for a in EA.get_all_level_actors():
        lab = a.get_actor_label()
        fake = lab in SPEC['destroy'] or (lab[:4] in ('P51 ', 'P52 ', 'P53 ', 'P54 ', 'P55 ') and
                                          (isinstance(a, (u.Light, u.ExponentialHeightFog, u.ReflectionCapture,
                                                          u.LightmassImportanceVolume))))
        if fake:
            R['destroyed'].append(lab); EA.destroy_actor(a)
    g = SPEC['grade']
    for a in EA.get_all_level_actors():
        if isinstance(a, u.PostProcessVolume):
            st = a.get_editor_property('settings')
            keep(orig, 'volumes', a.get_actor_label(), st, ['override_ambient_cubemap_intensity', 'ambient_cubemap_intensity'] +
                 ['override_' + k for k in g] + list(g))
            st.set_editor_property('override_ambient_cubemap_intensity', False)
            st.set_editor_property('ambient_cubemap_intensity', 0.0)
            for k, v in g.items():
                st.set_editor_property('override_' + k, True)
                st.set_editor_property(k, u.Vector4(v, v, v, 1) if k == 'color_contrast' else float(v))
            if 'grade_tint' in SPEC:                    # Pass59: a gentle warm fill, so nothing drops to black
                st.set_editor_property('override_ambient_cubemap_tint', True)
                st.set_editor_property('ambient_cubemap_tint', u.LinearColor(*SPEC['grade_tint'], 1))
            a.set_editor_property('settings', st)

    # ---------------- what the game moves: never baked in place
    for a in EA.get_all_level_actors():
        lab = a.get_actor_label()
        tags = [str(t) for t in a.tags]
        game_moves = any(t.startswith(('Skyward:', 'SkywardLight:', 'SkywardCamera:')) for t in tags) or \
            lab.startswith(('COL_', 'MOTION_PROXY', 'Flight39 ', 'CH12COLL ')) or lab in moving_labels
        if game_moves and not isinstance(a, (u.DirectionalLight, u.SkyLight)):
            root = a.root_component
            if root and root.get_editor_property('mobility') != MO:
                keep(orig, 'mobility', lab, root, ['mobility'])
                root.set_mobility(MO); R['movable'].append(lab)

    # ---------------- real sources
    L = SPEC['practical']
    for a in EA.get_all_level_actors():
        if not isinstance(a, u.Light):
            continue
        lab = a.get_actor_label()
        c = a.get_component_by_class(u.LightComponent)
        if isinstance(a, u.DirectionalLight):
            keep(orig, 'sun', lab, c, ['mobility', 'light_source_angle', 'dynamic_shadow_distance_stationary_light', 'volumetric_scattering_intensity'])
            c.set_mobility(SY)
            c.set_editor_property('light_source_angle', float(SPEC['sun']['source_angle']))
            c.set_editor_property('dynamic_shadow_distance_stationary_light', float(SPEC['sun']['dynamic_shadow_cm']))
            c.set_editor_property('volumetric_scattering_intensity', 1.0)
            if 'rotation' in SPEC['sun']:                  # Pass62: golden hour, so the sun reaches deep into rooms
                keep(orig, 'sun_rot', lab, a.root_component, ['relative_rotation'])
                pi, ya = SPEC['sun']['rotation']
                a.set_actor_rotation(u.Rotator(0, pi, ya), False)
                c.set_editor_property('use_temperature', True)
                c.set_editor_property('temperature', float(SPEC['sun'].get('temp', 5200)))
        elif lab.startswith(L['prefix']):
            keep(orig, 'lights', lab, c, ['mobility', 'temperature', 'use_temperature', 'cast_shadows', 'barn_door_angle', 'barn_door_length'])
            c.set_mobility(ST)
            c.set_editor_property('use_temperature', True)
            c.set_editor_property('temperature', float(L['temp']))
            c.set_editor_property('cast_shadows', True)
            R['static_lights'] += 1
    for a in EA.get_all_level_actors():
        if isinstance(a, u.SkyLight):
            c = a.get_component_by_class(u.SkyLightComponent)
            keep(orig, 'sky', a.get_actor_label(), c, ['mobility', 'intensity', 'lower_hemisphere_is_black', 'volumetric_scattering_intensity'])
            c.set_mobility(SY)
            c.set_editor_property('intensity', float(SPEC['sky']['intensity']))
            c.set_editor_property('volumetric_scattering_intensity', 1.0)

    # Pass56: a few large, soft ambient panels in the tall rooms. Their sources
    # are metres wide, so their shadows are almost invisible; they lift the dark
    # spots the fittings and sun leave without adding hot spots.
    for s in SPEC.get('ambient', []):
        a = EA.spawn_actor_from_class(u.RectLight, ue(s['p']), u.Rotator(0, -90, 0))
        a.set_actor_label(s['label']); a.set_folder_path('Lighting/Pass55')
        c = a.get_component_by_class(u.RectLightComponent)
        c.set_mobility(ST)
        c.set_editor_property('intensity_units', u.LightUnits.LUMENS)
        c.set_editor_property('intensity', float(s['lm']))
        c.set_editor_property('use_temperature', True)
        c.set_editor_property('temperature', float(s['temp']))
        c.set_editor_property('attenuation_radius', float(s['att']))
        c.set_editor_property('source_width', float(s['w']))
        c.set_editor_property('source_height', float(s['h']))
        c.set_editor_property('cast_shadows', True)
        R.setdefault('ambient', []).append(s['label'])

    # Pass57: the low rooms (security, concourse, baggage, cafe, amenities ...)
    # get the same soft ambient panels, sized and spaced from each room's own
    # grade volume, just under its ceiling.
    ra = SPEC.get('room_ambient')
    if ra:
        for v in EA.get_all_level_actors():
            lab = v.get_actor_label()
            if not (isinstance(v, u.PostProcessVolume) and lab.startswith('AP38 warm grade ')):
                continue
            room = lab.replace('AP38 warm grade ', '')
            if room in ra['skip']:
                continue
            o, e = v.get_actor_bounds(False)
            cx, cy, top = o.x / 100, -o.y / 100, (o.z + e.z) / 100
            lx, ly = 2 * e.x / 100, 2 * e.y / 100
            along_x = lx >= ly
            L, W = (lx, ly) if along_x else (ly, lx)
            # Pass58: a grid across the whole ceiling (both directions), so no
            # half of a room is left to one panel's falloff.
            n = max(1, round(L / ra['spacing'])); m = max(1, round(W / ra['spacing']))
            cover = ra.get('cover', .7)
            for k in range(n * m):
                t0 = -L / 2 + L * (k // m + .5) / n
                t1 = -W / 2 + W * (k % m + .5) / m
                px, py = (cx + t0, cy + t1) if along_x else (cx + t1, cy + t0)
                w = min(ra['max_size'], L / n * 100 * cover); h = min(ra['max_size'], W / m * 100 * cover)
                drop = ra.get('below_top_tall', ra['below_top']) if top > 4.5 else ra['below_top']   # under the slats
                a = EA.spawn_actor_from_class(u.RectLight, ue([px, py, top - drop]), u.Rotator(0, -90, 0))
                a.set_actor_label('P55 ambient %s %d' % (room, k)); a.set_folder_path('Lighting/Pass55')
                c = a.get_component_by_class(u.RectLightComponent)
                c.set_mobility(ST)
                c.set_editor_property('intensity_units', u.LightUnits.LUMENS)
                tall = max(1.0, (top / 3.2) ** 1.5)       # high ceilings: the same light has further to fall
                c.set_editor_property('intensity', float(max(ra['min_lm'], ra['lm_per_m2'] * L / n * W / m * tall)))
                c.set_editor_property('use_temperature', True)
                c.set_editor_property('temperature', float(ra['temp']))
                c.set_editor_property('attenuation_radius', float(max(L / n, W / m) * 100 + 400))
                c.set_editor_property('source_width', float(w if along_x else h))
                c.set_editor_property('source_height', float(h if along_x else w))
                c.set_editor_property('cast_shadows', True)
                R.setdefault('ambient', []).append(a.get_actor_label())

    # Pass58: downlights in the check-in canopy soffit (their fittings are in
    # the fit-out mesh), so the desks and the agents under it are lit.
    for s in SPEC.get('canopy_lights', []):
        a = EA.spawn_actor_from_class(u.RectLight, ue(s['p']), u.Rotator(0, -90, 0))
        a.set_actor_label(s['label']); a.set_folder_path('Lighting/Pass55')
        c = a.get_component_by_class(u.RectLightComponent)
        c.set_mobility(ST)
        c.set_editor_property('intensity_units', u.LightUnits.LUMENS)
        c.set_editor_property('intensity', float(s['lm']))
        c.set_editor_property('use_temperature', True)
        c.set_editor_property('temperature', float(s['temp']))
        c.set_editor_property('attenuation_radius', float(s['att']))
        c.set_editor_property('source_width', float(s['w']))
        c.set_editor_property('source_height', float(s['h']))
        c.set_editor_property('cast_shadows', True)
        R.setdefault('canopy', []).append(s['label'])

    # Pass58: the cafe's lights that hung in drum pendants (removed) go up to
    # the ceiling, where their flush fittings now are.
    mu = SPEC.get('move_up')
    if mu:
        for a in EA.get_all_level_actors():
            if isinstance(a, u.Light) and mu['match'] in a.get_actor_label():
                p = a.get_actor_location()
                if mu['from'][0] * 100 < p.z < mu['from'][1] * 100:
                    keep(orig, 'moved', a.get_actor_label(), a.root_component, ['relative_location'])
                    a.set_actor_location(u.Vector(p.x, p.y, mu['to'] * 100), False, False)
                    R.setdefault('moved', []).append(a.get_actor_label())
    # Pass58: glazing never blocks baked daylight (Lightmass treats the glass as
    # a partial shadow caster, so the cafe got almost no daylight).
    for a in EA.get_all_level_actors():
        if a.get_actor_label() in SPEC.get('no_shadow_labels', []):
            c = a.get_component_by_class(u.StaticMeshComponent)
            keep(orig, 'shadow', a.get_actor_label(), c, ['cast_shadow'])
            c.set_editor_property('cast_shadow', False)
            R.setdefault('glass', []).append(a.get_actor_label())

    # Pass57: bounced light keeps less of the colour of what it bounced off, so
    # the wood ceilings and panelling stop tinting whole rooms orange.
    if 'indirect_saturation' in SPEC:
        for a in EA.get_all_level_actors():
            if isinstance(a, u.Light):
                c = a.get_component_by_class(u.LightComponent)
                if c.get_editor_property('mobility') == MO:
                    continue
                ls = c.get_editor_property('lightmass_settings')
                keep(orig, 'lightmass_light', a.get_actor_label(), ls, ['indirect_lighting_saturation'])
                ls.set_editor_property('indirect_lighting_saturation', float(SPEC['indirect_saturation']))
                c.set_editor_property('lightmass_settings', ls)
                R['desaturated'] = R.get('desaturated', 0) + 1

    # Pass59: a light warm haze, for atmosphere.
    hz = SPEC.get('haze')
    if hz:
        f = EA.spawn_actor_from_class(u.ExponentialHeightFog, u.Vector(0, 0, 0), u.Rotator(0, 0, 0))
        f.set_actor_label('P55 warm haze'); f.set_folder_path('Lighting/Pass55')
        fc = f.get_component_by_class(u.ExponentialHeightFogComponent)
        fc.set_editor_property('fog_density', float(hz['density']))
        fc.set_editor_property('fog_height_falloff', float(hz['falloff']))
        fc.set_editor_property('start_distance', float(hz['start_cm']))
        for name in ('fog_inscattering_luminance', 'fog_inscattering_color'):
            try:
                fc.set_editor_property(name, u.LinearColor(*hz['color'], 1)); break
            except Exception:
                pass

    # ---------------- bake set-up
    ws = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world().get_world_settings()
    lm = ws.get_editor_property('lightmass_settings')
    keep(orig, 'lightmass', 'world', lm, list(SPEC['lightmass']))
    for k, v in SPEC['lightmass'].items():
        lm.set_editor_property(k, v)
    ws.set_editor_property('lightmass_settings', lm)
    x0, x1, y0, y1, z0, z1 = SPEC['importance']
    v = EA.spawn_actor_from_class(u.LightmassImportanceVolume, ue([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2]), u.Rotator(0, 0, 0))
    v.set_actor_label('P55 lightmass importance'); v.set_folder_path('Lighting/Pass55')
    v.set_actor_scale3d(u.Vector((x1 - x0) / 2, (y1 - y0) / 2, (z1 - z0) / 2))     # default brush is 200 uu across

    used = {}
    for a in EA.get_all_level_actors():
        if not isinstance(a, u.StaticMeshActor):
            continue
        c = a.static_mesh_component
        lab = a.get_actor_label()
        hidden = a.is_hidden_ed() or c.get_editor_property('hidden_in_game') or not c.is_visible()
        sm = c.static_mesh
        o, e = a.get_actor_bounds(False)
        size = 2 * max(e.x, e.y) / 100
        if hidden or 'COLL' in lab or size > SPEC['no_shadow_over_m'] or (sm and sm.get_name() in SPEC['no_shadow_meshes']):
            if c.get_editor_property('cast_shadow'):
                keep(orig, 'shadow', lab, c, ['cast_shadow'])
                c.set_editor_property('cast_shadow', False); R['no_shadow'].append(lab)
        keep_lm = SPEC.get('keep_lightmaps')
        if (sm and c.get_editor_property('mobility') == ST and not hidden and keep_lm is not None
                and sm.get_name() not in keep_lm and sm.get_name() not in SPEC.get('force_volumetric', [])):
            # Pass59: only the building shell and the ground keep baked lightmaps;
            # every prop (signs, desks, furniture) is lit from the volumetric
            # lightmap, which cannot bake black on a bad lightmap layout.
            keep(orig, 'lightmap_type', lab, c, ['lightmap_type'])
            c.set_editor_property('lightmap_type', u.LightmapType.FORCE_VOLUMETRIC)
            R['props_volumetric'] = R.get('props_volumetric', 0) + 1
            continue
        if sm and sm.get_name() in SPEC.get('force_volumetric', []):
            # too dense to pack a lightmap (overlap warnings / black): lit from the
            # volumetric lightmap instead, still static and still casting baked shadows
            keep(orig, 'lightmap_type', lab, c, ['lightmap_type'])
            c.set_editor_property('lightmap_type', u.LightmapType.FORCE_VOLUMETRIC)
            R.setdefault('volumetric', []).append(lab)
            continue
        if sm and c.get_editor_property('mobility') == ST and not hidden:
            area = 2 * (e.x * e.y + e.x * e.z + e.y * e.z) / 1e4            # m2 of the bounding box surface
            used[sm.get_path_name()] = max(used.get(sm.get_path_name(), 0), area)
    for path, area in used.items():
        res = 64
        for lim, r in SPEC['lightmap_by_area']:
            if area >= lim:
                res = r
        name = path.split('.')[-1]
        res = SPEC.get('lightmap_overrides', {}).get(name, res)
        sm = u.load_asset(path)
        if res <= 64 and name not in SPEC.get('lightmap_overrides', {}):
            continue
        bs0 = u.EditorStaticMeshLibrary.get_lod_build_settings(sm, 0)
        if sm.get_editor_property('light_map_resolution') == res and bs0.get_editor_property('min_lightmap_resolution') == res                 and sm.get_editor_property('light_map_coordinate_index') == bs0.get_editor_property('dst_lightmap_index'):
            continue
        keep(orig, 'meshes', path, sm, ['light_map_resolution'])
        bs = u.EditorStaticMeshLibrary.get_lod_build_settings(sm, 0)
        bs.set_editor_property('generate_lightmap_u_vs', True)
        bs.set_editor_property('min_lightmap_resolution', res)
        u.EditorStaticMeshLibrary.set_lod_build_settings(sm, 0, bs)
        sm.set_editor_property('light_map_resolution', res)
        # the lightmap must read the generated channel, not the texture UVs (overlap warnings)
        keep(orig, 'meshes', path, sm, ['light_map_coordinate_index'])
        sm.set_editor_property('light_map_coordinate_index', bs.get_editor_property('dst_lightmap_index'))
        u.EditorAssetLibrary.save_loaded_asset(sm)
        R['meshes'][sm.get_name()] = [round(area), res]

    for a in EA.get_all_level_actors():
        if isinstance(a, u.PostProcessVolume) and not a.get_editor_property('unbound') and a.get_actor_label().startswith('AP38 warm grade'):
            o, e = a.get_actor_bounds(False)
            cap = EA.spawn_actor_from_class(u.SphereReflectionCapture, o, u.Rotator(0, 0, 0))
            cap.set_actor_label('P55 reflections ' + a.get_actor_label().replace('AP38 warm grade ', ''))
            cap.set_folder_path('Lighting/Pass55')
            cap.get_component_by_class(u.SphereReflectionCaptureComponent).set_editor_property(
                'influence_radius', float(math.sqrt(e.x ** 2 + e.y ** 2)))
            R['captures'] += 1
    ORIG.write_text(json.dumps(orig, indent=1), encoding='utf-8')
    assert u.EditorLoadingAndSavingUtils.save_current_level()
    R['status'] = 'SUCCESS'


try:
    main()
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'Bake55Setup.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
print('BAKE55SETUP', R['status'])
