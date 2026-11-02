"""Pass66: check every Pass66 prop mesh has simple collision; give any that has none a box (-run=pythonscript).
MUTATES AND SAVES only meshes that lacked collision. Writes Collide66.json with the shape counts."""
import unreal as u, json, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIR = '/Game/Airport38/Pass48Meshes'
R = dict(status='RUNNING', meshes={}, fixed=[])


def shapes(mesh):
    bs = mesh.get_editor_property('body_setup')
    if not bs:
        return None
    g = bs.get_editor_property('agg_geom')
    out = {}
    for k in ('box_elems', 'sphere_elems', 'sphyl_elems', 'convex_elems'):
        try:
            out[k] = len(g.get_editor_property(k))
        except Exception as e:
            out[k] = str(e)[:40]
    out['trace_flag'] = str(bs.get_editor_property('collision_trace_flag'))
    return out


def main():
    lib = u.EditorStaticMeshLibrary
    for path in u.EditorAssetLibrary.list_assets(DIR, recursive=False, include_folder=False):
        name = path.split('/')[-1].split('.')[0]
        if not name.startswith('SM_AP_P66'):
            continue
        mesh = u.load_asset(path)
        before = shapes(mesh)
        total = sum(v for k, v in (before or {}).items() if k.endswith('elems') and isinstance(v, int))
        if not total:
            shape = u.ScriptCollisionShapeType.SPHERE if 'Ball' in name else u.ScriptCollisionShapeType.BOX
            idx = lib.add_simple_collisions(mesh, shape)
            u.EditorAssetLibrary.save_loaded_asset(mesh)
            R['fixed'].append([name, idx])
        R['meshes'][name] = dict(before=before, after=shapes(mesh))
    R['status'] = 'SUCCESS'


try:
    main()
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'Collide66.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
print('COLLIDE66', R['status'])
