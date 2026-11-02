"""Pass51: workbench previews of the fit-out alone (headless), to check lettering
faces and arrows before it goes into the level. Writes Preview/*.png."""
import bpy, math, sys
from mathutils import Vector
from pathlib import Path
HERE = Path(__file__).resolve().parent
exec(compile(open(HERE / 'fitout51_blender.py', encoding='utf-8').read(), 'fitout51', 'exec'))
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.color_type = 'MATERIAL'
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
out = HERE / 'Preview'; out.mkdir(exist_ok=True)
VIEWS = [('p1_entrance', (-48.3, -12.8, 1.62), (-36, -13.5, 2.8)), ('p2_from_desks', (-33.5, -12.5, 1.62), (-46, -12, 3.0)),
         ('p3_to_security', (-32.1, -11.0, 1.62), (-38, -5, 2.6)), ('p4_air', (-52, -24, 14), (-37, -11, 0))]
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 18
for n, e, t in VIEWS:
    cam.location = e
    cam.rotation_euler = (Vector(t) - Vector(e)).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = str(out / (n + '.png'))
    bpy.ops.render.render(write_still=True)
print('PREVIEW51 done')
