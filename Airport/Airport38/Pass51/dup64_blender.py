import bpy, bmesh, sys, json
from collections import Counter
from mathutils import Matrix
a = sys.argv[sys.argv.index('--') + 1:]
out = {}
for path in a:
    for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.import_scene.fbx(filepath=path)
    o = [x for x in bpy.data.objects if x.type == 'MESH'][0]
    o.data.transform(o.matrix_world)
    bm = bmesh.new(); bm.from_mesh(o.data); bm.normal_update()
    keys = Counter()
    ex = {}
    for f in bm.faces:
        c = f.calc_center_median(); n = f.normal
        k = (round(c.x, 2), round(c.y, 2), round(c.z, 2), round(n.x, 1), round(n.y, 1), round(n.z, 1))
        keys[k] += 1; ex.setdefault(k, o.data.materials[f.material_index].name)
    d = [(k, v, ex[k]) for k, v in keys.items() if v > 1]
    mats = Counter(m for k, v, m in d)
    zs = sorted(k[2] for k, v, m in d)
    out[path.split('/')[-1]] = dict(faces=len(bm.faces), dup_groups=len(d), mats=dict(mats.most_common(8)), z=[zs[0], zs[-1]] if zs else None, sample=[list(k) for k, v, m in d[:6]])
print('DUP64', json.dumps(out))
