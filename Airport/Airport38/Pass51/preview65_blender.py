import bpy
from mathutils import Vector
from pathlib import Path
HERE = Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True)
for n in ('SM_AP_P62Lounges', 'SM_AP_P62LoungeSoft', 'SM_AP_P62LoungeFloor'):
    bpy.ops.import_scene.fbx(filepath=str(HERE / 'LoungeBuild' / (n + '.fbx')))
for o in bpy.data.objects:
    if o.type == 'MESH': o.data.transform(o.matrix_world); o.matrix_world.identity()
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.color_type = 'MATERIAL'
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.lens = 20
for name, e, t in (('terrace', (-25.2, 22.0, 1.62), (-30.5, 27.5, 1.6)), ('art', (-26.0, 26.9, 2.2), (-31.8, 26.9, 3.6))):
    cam.location = e; cam.rotation_euler = (Vector(t) - Vector(e)).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = str(HERE / 'Preview' / ('p65_' + name + '.png')); bpy.ops.render.render(write_still=True)
