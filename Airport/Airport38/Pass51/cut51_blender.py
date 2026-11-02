"""Pass51: list and cut pieces of live meshes (headless Blender).

For every mesh in Cut51.json (exported by export51_editor.py to Current/):
  pieces   each connected piece whose centre is inside 'region' (default the
           landside hall) with its bounds, material and face count, so a cut
           can be aimed at one sign and nothing else
  boxes    every face whose centre is inside a box goes (Pass50 cut rule)
  against  (Pass64) FBX files of meshes drawn in front: every face of this mesh
           lying in one of their planes (3 mm, same facing) and overlapping
           it goes, which ends the z-fighting (flicker) between them
Rebuilt meshes go to Rebuilt/ in the exported frame, for reimport51_editor.py.
Usage: blender -b --factory-startup -P cut51_blender.py
"""
import bpy, bmesh, json, sys
from mathutils import Matrix, Vector
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'Pass48'))
from mesh48 import export

CUR, OUT = HERE / 'Current', HERE / 'Rebuilt'
SPEC = json.loads((HERE / 'Cut51.json').read_text(encoding='utf-8'))
REP = dict(status='RUNNING', meshes={})
HALL = [-49.5, -25.5, -18.5, -3.5, -0.5, 7.5]


def inside(p, box):
    return box[0] <= p.x <= box[1] and box[2] <= p.y <= box[3] and box[4] <= p.z <= box[5]


def load(name):
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.import_scene.fbx(filepath=str(CUR / (name + '.fbx')))
    objs = [o for o in bpy.data.objects if o.type == 'MESH']
    assert len(objs) == 1, (name, [o.name for o in objs])
    o = objs[0]
    o.data.transform(o.matrix_world); o.matrix_world = Matrix.Identity(4)
    o.data.transform(Matrix(SPEC['to_src']))
    return o


def pieces(o, bm, region):
    bm.faces.ensure_lookup_table()
    seen, out = set(), []
    for f in bm.faces:
        if f.index in seen:
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
        lo = [min(v.co[k] for v in vs) for k in range(3)]
        hi = [max(v.co[k] for v in vs) for k in range(3)]
        c = Vector([(a + b) / 2 for a, b in zip(lo, hi)])
        if inside(c, region):
            mats = sorted({o.data.materials[bm.faces[i].material_index].name for i in comp})
            out.append(dict(b=[round(lo[0], 2), round(hi[0], 2), round(lo[1], 2), round(hi[1], 2), round(lo[2], 2), round(hi[2], 2)],
                            faces=len(comp), mats=mats))
    out.sort(key=lambda p: (p['b'][0], p['b'][2]))
    return out


def plane_faces(paths):
    """Faces of other meshes (source metres), bucketed by plane, for the z-fight check."""
    from collections import defaultdict
    B = defaultdict(list)
    for path in paths:
        for o in list(bpy.data.objects):
            bpy.data.objects.remove(o, do_unlink=True)
        bpy.ops.import_scene.fbx(filepath=str(path))
        for o in [x for x in bpy.data.objects if x.type == 'MESH']:
            o.data.transform(o.matrix_world); o.matrix_world = Matrix.Identity(4)
            bm = bmesh.new(); bm.from_mesh(o.data); bm.normal_update()
            for f in bm.faces:
                if f.calc_area() < .002:
                    continue
                n = f.normal.copy(); d = n.dot(f.calc_center_median())
                vs = [v.co for v in f.verts]
                b = [min(v.x for v in vs), max(v.x for v in vs), min(v.y for v in vs), max(v.y for v in vs), min(v.z for v in vs), max(v.z for v in vs)]
                B[(round(n.x, 1), round(n.y, 1), round(n.z, 1), round(d / .004))].append((n, d, b))
            bm.free()
    return B


def fights(f, B):
    """True when face f lies in the plane of an 'against' face (3 mm, same facing) and overlaps it."""
    n = f.normal; d = n.dot(f.calc_center_median())
    vs = [v.co for v in f.verts]
    b = [min(v.x for v in vs), max(v.x for v in vs), min(v.y for v in vs), max(v.y for v in vs), min(v.z for v in vs), max(v.z for v in vs)]
    k = (round(n.x, 1), round(n.y, 1), round(n.z, 1))
    for dq in (round(d / .004) - 1, round(d / .004), round(d / .004) + 1):
        for n2, d2, b2 in B.get(k + (dq,), []):
            if abs(d - d2) > .003 or n.dot(n2) < .98:
                continue
            o = sorted([max(0, min(b[1], b2[1]) - max(b[0], b2[0])), max(0, min(b[3], b2[3]) - max(b[2], b2[2])),
                        max(0, min(b[5], b2[5]) - max(b[4], b2[4]))])
            if o[1] * o[2] > .25 * max(f.calc_area(), 1e-4):
                return True
    return False


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for name, job in SPEC['meshes'].items():
        B = plane_faces([HERE.parent / p for p in job.get('against', [])]) if job.get('against') else None
        o = load(name)
        bm = bmesh.new(); bm.from_mesh(o.data); bm.normal_update()
        rep = dict(faces_before=len(bm.faces), pieces=pieces(o, bm, job.get('region', HALL)) if not B else [])
        boxes = job.get('boxes', [])
        if job.get('dedupe'):
            # Pass64: exact duplicate faces (same plane, centre and size) are drawn twice
            # with different shading and shimmer; keep one of each.
            seen, dups = set(), []
            for f in bm.faces:
                c = f.calc_center_median(); n = f.normal
                k = (round(c.x, 3), round(c.y, 3), round(c.z, 3), round(n.x, 2), round(n.y, 2), round(n.z, 2), round(f.calc_area(), 4))
                (dups.append(f) if k in seen else seen.add(k))
            bmesh.ops.delete(bm, geom=dups, context='FACES')
            rep['deduped'] = len(dups)
        if boxes or B or job.get('dedupe'):
            bm.faces.ensure_lookup_table(); bm.normal_update()
            dead = [f for f in bm.faces if any(inside(f.calc_center_median(), b) for b in boxes) or (B and fights(f, B))]
            rep['removed'] = len(dead)
            bmesh.ops.delete(bm, geom=dead, context='FACES')
            bm.to_mesh(o.data)
            o.data.transform(Matrix(SPEC['to_src']).inverted())
            o.name = o.data.name = name
            OUT.mkdir(parents=True, exist_ok=True)
            export(o, OUT / (name + '.fbx'))
            rep['rebuilt'] = True
        bm.free()
        REP['meshes'][name] = rep
    REP['status'] = 'SUCCESS'


try:
    main()
except Exception:
    import traceback
    REP['status'] = 'ERROR'; REP['error'] = traceback.format_exc()
(HERE / 'Cut51Report.json').write_text(json.dumps(REP, indent=1), encoding='utf-8')
print('CUT51', REP['status'])
