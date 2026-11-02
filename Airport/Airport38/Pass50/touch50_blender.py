"""Pass50: which pieces of a mesh reach a room's old ceiling (hung from it)? (headless, read-only)
Usage: blender -b --factory-startup -P touch50_blender.py -- <mesh> <x0> <x1> <y0> <y1> <ceiling>"""
import bpy, bmesh, sys
from pathlib import Path
a = sys.argv[sys.argv.index('--') + 1:]
name, (x0, x1, y0, y1, c) = a[0], [float(v) for v in a[1:6]]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(Path(__file__).resolve().parent / 'Current' / (name + '.fbx')))
o = next(o for o in bpy.data.objects if o.type == 'MESH'); o.data.transform(o.matrix_world)
bm = bmesh.new(); bm.from_mesh(o.data)
hit = [v for v in bm.verts if x0 < v.co.x < x1 and y0 < v.co.y < y1 and abs(v.co.z - c) < .05]
seen, pieces = set(), []
for v in hit:
    if v.index in seen:
        continue
    comp, stack = set(), [v]
    while stack:
        w = stack.pop()
        if w.index in comp:
            continue
        comp.add(w.index)
        stack += [e.other_vert(w) for e in w.link_edges]
    seen |= comp
    vs = [bm.verts[i] for i in comp] if hasattr(bm.verts, 'ensure_lookup_table') and not bm.verts.ensure_lookup_table() else []
    vs = [bm.verts[i] for i in comp]
    pieces.append([round(min(q.co.x for q in vs), 2), round(max(q.co.x for q in vs), 2), round(min(q.co.y for q in vs), 2),
                   round(max(q.co.y for q in vs), 2), round(min(q.co.z for q in vs), 2), round(max(q.co.z for q in vs), 2), len(vs)])
print('TOUCH', name, len(hit), 'verts in', len(pieces), 'pieces')
for p in sorted(pieces):
    print('TOUCH', p)
