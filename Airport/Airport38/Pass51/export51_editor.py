"""Pass51: export the meshes named in Cut51.json exactly as they are in the project (-run=pythonscript).

The FBX files in Exports/FBX are not all what the level uses (some were
re-exported later and never imported), so the landside-hall rebuild starts
from the live assets: each mesh is exported to Pass51/Current/<name>.fbx and
its slots, materials, collision and the actors placing it are recorded in
Current51.json, so the rebuilt meshes can be re-imported into the same assets
with the same slots. Read-only for the level and the assets.
"""
import unreal as u, json, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / 'Current'
MAP = '/Game/Airport38/L_Airport_Repair38'
NAMES = list(json.loads((HERE / 'Cut51.json').read_text(encoding='utf-8'))['meshes'])
R = dict(status='RUNNING', meshes={})


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    assert u.EditorLoadingAndSavingUtils.load_map(MAP)
    actors = u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
    found = {}
    for a in actors:
        if isinstance(a, u.StaticMeshActor) and a.static_mesh_component.static_mesh:
            sm = a.static_mesh_component.static_mesh
            if sm.get_name() in NAMES:
                found.setdefault(sm.get_name(), [sm, []])[1].append(dict(
                    label=a.get_actor_label(), location=list(a.get_actor_location().to_tuple()),
                    rotation=list(a.get_actor_rotation().to_tuple()), scale=list(a.get_actor_scale3d().to_tuple()),
                    hidden=a.is_hidden_ed(), collision=str(a.static_mesh_component.get_collision_profile_name())))
    for name in NAMES:
        if name not in found:
            R['meshes'][name] = dict(missing=True); continue
        sm, placed = found[name]
        opt = u.FbxExportOption()
        for k, v in dict(collision=False, level_of_detail=False, vertex_color=True, export_morph_targets=False).items():
            try:
                opt.set_editor_property(k, v)
            except Exception:
                pass
        t = u.AssetExportTask()
        for k, v in dict(object=sm, filename=str(OUT / (name + '.fbx')), automated=True, prompt=False,
                         replace_identical=True, exporter=u.StaticMeshExporterFBX(), options=opt).items():
            t.set_editor_property(k, v)
        ok = u.Exporter.run_asset_export_task(t)
        bs = sm.get_editor_property('body_setup')
        R['meshes'][name] = dict(
            path=sm.get_path_name(), exported=bool(ok), actors=placed,
            slots=[dict(slot=str(m.get_editor_property('material_slot_name')),
                        material=m.get_editor_property('material_interface').get_path_name() if m.get_editor_property('material_interface') else None)
                   for m in sm.get_editor_property('static_materials')],
            trace_flag=str(bs.get_editor_property('collision_trace_flag')) if bs else None,
            double_sided=bool(bs.get_editor_property('double_sided_geometry')) if bs else None,
            triangles=sm.get_num_triangles(0) if hasattr(sm, 'get_num_triangles') else None)
    R['status'] = 'SUCCESS'


try:
    main()
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'Current51.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
print('EXPORT51', R['status'])
