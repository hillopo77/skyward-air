"""Pass71: preview renders of the extinguisher in its cabinet (headless, workbench, studio light)."""
import bpy, sys
from mathutils import Vector
from pathlib import Path
HERE = Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True)
sys.path.insert(0, str(HERE))
from props71_blender import MATS as _M
for n, at in (('SM_AP_P71ExtCabinet', (0, 0, 0)), ('SM_AP_P71Extinguisher', (0, -.13, .48))):
    bpy.ops.import_scene.fbx(filepath=str(HERE / 'Props71Build' / (n + '.fbx')))
    bpy.context.selected_objects[0].location = at
bpy.ops.mesh.primitive_plane_add(size=4, location=(0, -1, 0)); bpy.ops.mesh.primitive_plane_add(size=4, location=(0, .002, 2), rotation=(1.5708, 0, 0))
for m in bpy.data.materials:
    rgb = next((v[1] for v in _M.values() if m.name.startswith(v[0])), None)
    if rgb: m.diffuse_color = (*rgb, 1)
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.color_type = 'MATERIAL'
sc.display.shading.light = 'STUDIO'; sc.display.shading.show_shadows = True; sc.display.shading.show_cavity = True
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera = cam
for name, e, t, lens in (('cab_front', (.9, -1.9, 1.3), (0, -.1, .95), 40), ('ext_close', (.28, -.55, .82), (0, -.13, .75), 45),
                         ('cab_side', (-1.0, -1.2, 1.0), (0, -.1, .9), 40)):
    cam.data.lens = lens; cam.location = e; cam.rotation_euler = (Vector(t) - Vector(e)).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = str(HERE / 'Preview' / ('p71_' + name + '.png')); bpy.ops.render.render(write_still=True)
print('PREVIEW71 done')
