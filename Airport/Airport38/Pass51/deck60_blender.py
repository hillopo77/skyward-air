"""Pass60: read-only - horizontal surfaces of the gallery stair/deck and the
glazing panes around the cafe (from Current/*.fbx). Writes Deck60.json."""
import bpy, bmesh, json
from mathutils import Matrix
from pathlib import Path
HERE = Path(__file__).resolve().parent
R = {}
for name in ('SM_AP_GalleryStair35', 'SM_AP_Glazing38'):
    for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.import_scene.fbx(filepath=str(HERE / 'Current' / (name + '.fbx')))
    o = [x for x in bpy.data.objects if x.type == 'MESH'][0]
    o.data.transform(o.matrix_world); o.matrix_world = Matrix.Identity(4)
    bm = bmesh.new(); bm.from_mesh(o.data)
    out = []
    for f in bm.faces:
        c = f.calc_center_median()
        if not (-50 < c.x < -31 and 15 < c.y < 35):
            continue
        n = f.normal
        vs = [v.co for v in f.verts]
        b = [round(min(v.x for v in vs), 2), round(max(v.x for v in vs), 2), round(min(v.y for v in vs), 2), round(max(v.y for v in vs), 2), round(min(v.z for v in vs), 2), round(max(v.z for v in vs), 2)]
        area = f.calc_area()
        if area < .3: continue
        out.append(dict(m=o.data.materials[f.material_index].name, n=[round(n.x, 2), round(n.y, 2), round(n.z, 2)], b=b, a=round(area, 2)))
    R[name] = sorted(out, key=lambda r: -r['a'])[:60]
(HERE / 'Deck60.json').write_text(json.dumps(R, indent=1))
print('DECK60 done')
