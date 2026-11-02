"""Pass70: preview renders of the new extinguisher, stand and play plane (headless, workbench)."""
import bpy
from mathutils import Vector
from pathlib import Path
HERE = Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True)
spots = {'SM_AP_P70Extinguisher': (0, .02, .04), 'SM_AP_P70ExtStand': (0, 0, 0), 'SM_AP_P70PlayPlane': (2.2, 0, 0)}
for n, at in spots.items():
    bpy.ops.import_scene.fbx(filepath=str(HERE / 'Props70Build' / (n + '.fbx')))
    o = bpy.context.selected_objects[0]
    o.location = at
import sys; sys.path.insert(0, str(HERE)); from props70_blender import MATS as _M
for m in bpy.data.materials:
    rgb = next((v[1] for v in _M.values() if m.name.startswith(v[0])), None)
    if rgb: m.diffuse_color = (*rgb, 1)
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.color_type = 'MATERIAL'
sc.display.shading.light = 'STUDIO'; sc.display.shading.show_shadows = True; sc.display.shading.show_cavity = True
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera = cam
out = HERE / 'Preview'; out.mkdir(exist_ok=True)
for name, e, t, lens in (('ext_front', (.55, -1.1, .9), (0, 0, .62), 40), ('ext_close', (.25, -.55, .62), (0, 0, .45), 45),
                         ('plane_3q', (4.4, -2.6, 1.6), (2.2, 0, .55), 32), ('plane_side', (5.0, .2, .9), (2.2, 0, .55), 32)):
    cam.data.lens = lens
    cam.location = e; cam.rotation_euler = (Vector(t) - Vector(e)).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = str(out / ('p70_' + name + '.png')); bpy.ops.render.render(write_still=True)
print('PREVIEW70 done')
