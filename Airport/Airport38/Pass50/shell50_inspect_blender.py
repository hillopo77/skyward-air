"""Pass50: read the exported shell meshes and report what stands in the landside block (headless)."""
import bpy, sys, json
from pathlib import Path
FBX = Path(__file__).resolve().parent / 'Current'
A = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
X0, X1, Y0, Y1 = [float(v) for v in A[:4]] if A else (-49.5, -25.5, -22.5, -3.5)
OUT = Path(__file__).resolve().parent / ((A[4] if len(A) > 4 else 'ShellInspect50') + '.json')
bpy.ops.wm.read_factory_settings(use_empty=True)
rep = {}
for name in ['SM_AP_Walls38', 'SM_AP_Ceilings38', 'SM_AP_Roofs38', 'SM_AP_Glazing38', 'SM_AP_TerminalWallFinish43']:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(FBX / (name + '.fbx')))
    objs = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
    r = dict(objects=[], faces=0, region_faces=0)
    for o in objs:
        me = o.data; mw = o.matrix_world
        mats = [m.name if m else None for m in me.materials]
        groups = {}
        for p in me.polygons:
            c = mw @ p.center
            r['faces'] += 1
            if X0 <= c.x <= X1 and Y0 <= -c.y <= Y1 if False else (X0 <= c.x <= X1 and Y0 <= c.y <= Y1):
                r['region_faces'] += 1
                n = (mw.to_3x3() @ p.normal).normalized()
                key = (mats[p.material_index] if p.material_index < len(mats) else '?', 'x' if abs(n.x) > .9 else 'y' if abs(n.y) > .9 else 'z' if abs(n.z) > .9 else 'o',
                       round(c.x if abs(n.x) > .9 else c.y if abs(n.y) > .9 else c.z, 2))
                g = groups.setdefault(str(key), [1e9, -1e9, 1e9, -1e9, 1e9, -1e9, 0])
                for v in p.vertices:
                    w = mw @ me.vertices[v].co
                    g[0] = min(g[0], w.x); g[1] = max(g[1], w.x); g[2] = min(g[2], w.y); g[3] = max(g[3], w.y); g[4] = min(g[4], w.z); g[5] = max(g[5], w.z)
                g[6] += 1
        r['objects'].append(dict(name=o.name, mats=mats, scale=list(o.scale), loc=list(o.location), rot=list(o.rotation_euler)))
        r['planes'] = {k: [round(v, 2) for v in g[:6]] + [g[6]] for k, g in sorted(groups.items())}
    rep[name] = r
OUT.write_text(json.dumps(rep, indent=1))
print('SHELL50 done')
