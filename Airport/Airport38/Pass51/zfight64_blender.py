"""Pass64: find z-fighting - faces from the building meshes that lie in the same
plane (within 2 mm, facing the same way) and overlap (headless, read-only).
Args: -- out.json fbx [fbx ...]   Writes clusters of fighting faces by mesh/material pair.
"""
import bpy, bmesh, json, sys
from collections import defaultdict
from mathutils import Matrix

a = sys.argv[sys.argv.index('--') + 1:]
OUT, FILES = a[0], a[1:]
faces = []
for path in FILES:
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.import_scene.fbx(filepath=path)
    for o in [x for x in bpy.data.objects if x.type == 'MESH']:
        o.data.transform(o.matrix_world); o.matrix_world = Matrix.Identity(4)
        bm = bmesh.new(); bm.from_mesh(o.data); bm.normal_update()
        name = path.replace('\\', '/').split('/')[-1][:-4]
        for f in bm.faces:
            n = f.normal
            if f.calc_area() < .002 or n.length < .5:
                continue
            c = f.calc_center_median()
            vs = [v.co.copy() for v in f.verts]
            mat = o.data.materials[f.material_index].name if f.material_index < len(o.data.materials) else '?'
            faces.append((name, mat, (round(n.x, 2), round(n.y, 2), round(n.z, 2)), round(n.dot(c), 3), c, vs))
        bm.free()
buckets = defaultdict(list)
for i, (_, _, n, d, _, _) in enumerate(faces):
    buckets[(n, round(d / .002))].append(i)


def box(vs):
    return [min(v.x for v in vs), max(v.x for v in vs), min(v.y for v in vs), max(v.y for v in vs), min(v.z for v in vs), max(v.z for v in vs)]


def overlap(b1, b2):
    o = [max(0, min(b1[1], b2[1]) - max(b1[0], b2[0])), max(0, min(b1[3], b2[3]) - max(b1[2], b2[2])), max(0, min(b1[5], b2[5]) - max(b1[4], b2[4]))]
    o.sort()
    return o[1] * o[2]                                  # the two largest extents (the plane)


clusters = defaultdict(lambda: dict(count=0, area=0.0, z=[99, -99], where=[]))
seen = set()
for (n, dq), idx in buckets.items():
    cand = idx + buckets.get((n, dq + 1), [])
    boxes = {i: box(faces[i][5]) for i in cand}
    for x in range(len(cand)):
        for y in range(x + 1, len(cand)):
            i, j = cand[x], cand[y]
            if (i, j) in seen:
                continue
            seen.add((i, j))
            fi, fj = faces[i], faces[j]
            if abs(fi[3] - fj[3]) > .002:
                continue
            ov = overlap(boxes[i], boxes[j])
            if ov < .003:
                continue
            key = tuple(sorted([fi[0] + ':' + fi[1], fj[0] + ':' + fj[1]]))
            cl = clusters[key]
            cl['count'] += 1; cl['area'] += ov
            c = fi[4]
            cl['z'] = [min(cl['z'][0], round(c.z, 2)), max(cl['z'][1], round(c.z, 2))]
            if len(cl['where']) < 6:
                cl['where'].append([round(c.x, 2), round(c.y, 2), round(c.z, 2), list(n)])
res = sorted(([list(k), v] for k, v in clusters.items()), key=lambda kv: -kv[1]['area'])
json.dump(dict(faces=len(faces), clusters=res[:60]), open(OUT, 'w'), indent=1)
print('ZFIGHT64', len(faces), len(res))
