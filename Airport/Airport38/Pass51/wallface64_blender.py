import bpy, bmesh, sys
from mathutils import Matrix
a = sys.argv[sys.argv.index('--') + 1:]
for path in a:
    for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.import_scene.fbx(filepath=path)
    o = [x for x in bpy.data.objects if x.type == 'MESH'][0]; o.data.transform(o.matrix_world)
    bm = bmesh.new(); bm.from_mesh(o.data); bm.normal_update()
    for f in bm.faces:
        c = f.calc_center_median(); n = f.normal
        if -26.6 < c.x < -25.6 and 10.0 < c.y < 14.0 and 0.8 < c.z < 3.0 and n.x < -.9 and f.calc_area() > .05:
            print('FACE', path.split('/')[-1], round(c.x, 3), round(c.y, 2), round(c.z, 2), o.data.materials[f.material_index].name, round(f.calc_area(), 2))
