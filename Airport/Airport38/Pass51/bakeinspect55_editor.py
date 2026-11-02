"""Pass55: read-only - can this level bake lighting? World settings, light
mobility counts, and lightmap set-up of the biggest static meshes."""
import unreal as u, json, traceback
from pathlib import Path
HERE = Path(__file__).resolve().parent
MAP = '/Game/Airport38/L_Airport_Repair38'
R = dict(status='RUNNING')
try:
    assert u.EditorLoadingAndSavingUtils.load_map(MAP)
    w = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    ws = w.get_world_settings()
    R['force_no_precomputed_lighting'] = ws.get_editor_property('force_no_precomputed_lighting')
    lm = ws.get_editor_property('lightmass_settings')
    R['lightmass'] = {k: str(lm.get_editor_property(k)) for k in ('num_indirect_lighting_bounces', 'indirect_lighting_quality', 'indirect_lighting_smoothness', 'environment_color', 'environment_intensity', 'static_lighting_level_scale', 'use_ambient_occlusion', 'compress_lightmaps', 'volume_lighting_method')}
    EA = u.get_editor_subsystem(u.EditorActorSubsystem)
    mob, meshes, classes = {}, {}, {}
    for a in EA.get_all_level_actors():
        cls = a.get_class().get_name(); classes[cls] = classes.get(cls, 0) + 1
        lc = a.get_component_by_class(u.LightComponentBase)
        if lc:
            k = cls + ' ' + str(lc.get_editor_property('mobility')).split('.')[-1].split(':')[0]
            mob[k] = mob.get(k, 0) + 1
        if isinstance(a, u.StaticMeshActor):
            c = a.static_mesh_component; sm = c.static_mesh
            if sm:
                o, e = a.get_actor_bounds(False)
                size = max(e.x, e.y, e.z) * 2 / 100
                m = meshes.setdefault(sm.get_name(), dict(count=0, size=0))
                m['count'] += 1; m['size'] = max(m['size'], round(size, 1))
                m.setdefault('mobility', str(c.get_editor_property('mobility')).split('.')[-1].split(':')[0])
                m.setdefault('hidden', a.is_hidden_ed())
    big = sorted(meshes.items(), key=lambda kv: -kv[1]['size'])[:45]
    for name, m in big:
        sm = u.EditorAssetLibrary.find_asset_data(name) if False else None
    out = []
    reg = u.AssetRegistryHelpers.get_asset_registry()
    want = {n for n, _ in big}
    for ad in reg.get_assets_by_class(u.TopLevelAssetPath('/Script/Engine', 'StaticMesh'), True):
        n = str(ad.asset_name)
        if n in want:
            sm = ad.get_asset()
            src = sm.get_editor_property('source_models') if hasattr(sm, 'source_models') else None
            try:
                bs = sm.get_editor_property('build_settings') if False else None
            except Exception:
                bs = None
            gen = None
            try:
                gen = u.EditorStaticMeshLibrary.get_lod_build_settings(sm, 0).get_editor_property('generate_lightmap_u_vs')
            except Exception as ex:
                gen = str(ex)[:60]
            out.append(dict(name=n, path=str(ad.package_name), lm_res=sm.get_editor_property('light_map_resolution'),
                            lm_uv=sm.get_editor_property('light_map_coordinate_index'), uv_channels=u.EditorStaticMeshLibrary.get_num_uv_channels(sm, 0),
                            gen_lm=gen, tris=sm.get_num_triangles(0), **meshes[n]))
    R['meshes'] = sorted(out, key=lambda m: -m['size'])
    R['lights'] = mob; R['classes'] = {k: v for k, v in classes.items() if v > 3 or 'Light' in k or 'Volume' in k or 'Fog' in k}
    R['status'] = 'SUCCESS'
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'BakeInspect55.json').write_text(json.dumps(R, indent=1, default=str), encoding='utf-8')
print('BAKEINSPECT55', R['status'])
