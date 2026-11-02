"""Pass50: is the floor continuous where the partitions stood? (headless, read-only)"""
import bpy, sys
from pathlib import Path
from mathutils.geometry import intersect_point_tri_2d
HERE = Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(HERE.parent / 'Exports' / 'FBX' / 'SM_AP_Floors38.fbx'))
o = next(o for o in bpy.data.objects if o.type == 'MESH'); o.data.transform(o.matrix_world)
me = o.data; me.calc_loop_triangles()
tris = [[me.vertices[i].co for i in t.vertices] for t in me.loop_triangles
        if all(abs(me.vertices[i].co.z) < .01 for i in t.vertices)]
pts = [(-43.0, y) for y in (-17.5, -15.0, -12.0, -9.0)] + [(x, -8.0) for x in (-48.5, -45.0, -40.0, -35.0, -30.0, -27.0)]
for p in pts:
    hit = any(intersect_point_tri_2d(p, a.xy, b.xy, c.xy) for a, b, c in tris)
    print('FLOOR', p, hit)
