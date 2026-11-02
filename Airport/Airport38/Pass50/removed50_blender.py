"""Pass50: list the connected pieces the hall cut removes from a mesh, with bounds (headless, read-only)."""
import bpy, bmesh, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = json.loads((HERE / 'Hall50.json').read_text(encoding='utf-8'))
out = {}
for name in sys.argv[sys.argv.index('--') + 1:]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(HERE / 'Current' / (name + '.fbx')))
    o = next(o for o in bpy.data.objects if o.type == 'MESH')
    o.data.transform(o.matrix_world)
    bm = bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table()
    boxes = SPEC['cuts'][name]['boxes']

    def dead(f):
        c = f.calc_center_median()
        return any(b[0] <= c.x <= b[1] and b[2] <= c.y <= b[3] and b[4] <= c.z <= b[5] for b in boxes)
    seen, pieces = set(), []
    for f in bm.faces:
        if f.index in seen or not dead(f):
            continue
        comp, stack = set(), [f]
        while stack:
            g = stack.pop()
            if g.index in comp:
                continue
            comp.add(g.index)
            for e in g.edges:
                stack += [h for h in e.link_faces if h.index not in comp]
        seen |= comp
        vs = {v for i in comp for v in bm.faces[i].verts}
        n_dead = sum(dead(bm.faces[i]) for i in comp)
        mats = sorted({o.data.materials[bm.faces[i].material_index].name for i in comp})
        pieces.append(dict(faces=len(comp), dead=n_dead, mats=mats,
                           box=[round(min(v.co[k] for v in vs), 2) for k in range(3)] + [round(max(v.co[k] for v in vs), 2) for k in range(3)]))
    # Merge tiny pieces (letters) by rounding their bounds into 0.5 m cells.
    cells = {}
    for p in pieces:
        b = p['box']
        k = (round(b[0] * 2) / 2, round(b[1] * 2) / 2, round(b[2] * 2) / 2, p['mats'][0])
        c = cells.setdefault(str(k), dict(pieces=0, faces=0, dead=0, box=list(b), mats=set()))
        c['pieces'] += 1; c['faces'] += p['faces']; c['dead'] += p['dead']; c['mats'] |= set(p['mats'])
        c['box'] = [min(c['box'][i], b[i]) for i in range(3)] + [max(c['box'][i + 3], b[i + 3]) for i in range(3)]
    out[name] = sorted(([v['faces'], v['dead'], v['pieces'], v['box'], sorted(v['mats'])] for v in cells.values()), key=lambda r: -r[0])
(HERE / 'Removed50.json').write_text(json.dumps(out, indent=1), encoding='utf-8')
print('REMOVED50 done')
