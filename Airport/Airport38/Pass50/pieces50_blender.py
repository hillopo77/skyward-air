"""Pass50: connected pieces of a mesh with any vertex inside a box, with bounds (headless, read-only).
Usage: -- <fbx> x0 x1 y0 y1 z0 z1"""
import bpy, bmesh, sys
a = sys.argv[sys.argv.index('--') + 1:]
b = [float(v) for v in a[1:7]]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=a[0])
o = next(o for o in bpy.data.objects if o.type == 'MESH'); o.data.transform(o.matrix_world)
bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
seen = set(); out = []
for v in bm.verts:
    if v.index in seen or not (b[0] <= v.co.x <= b[1] and b[2] <= v.co.y <= b[3] and b[4] <= v.co.z <= b[5]):
        continue
    comp, st = set(), [v]
    while st:
        w = st.pop()
        if w.index in comp: continue
        comp.add(w.index); st += [e.other_vert(w) for e in w.link_edges]
    seen |= comp
    vs = [bm.verts[i] for i in comp]
    mats = sorted({o.data.materials[f.material_index].name for q in vs for f in q.link_faces})
    out.append([round(min(q.co.x for q in vs), 2), round(max(q.co.x for q in vs), 2), round(min(q.co.y for q in vs), 2),
                round(max(q.co.y for q in vs), 2), round(min(q.co.z for q in vs), 2), round(max(q.co.z for q in vs), 2), len(vs), mats])
for r in sorted(out, key=lambda r: -r[6])[:15]:
    print('PIECE', r)
