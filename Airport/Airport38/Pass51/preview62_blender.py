import bpy
from mathutils import Vector
from pathlib import Path
HERE = Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True)
for d, n in (('LoungeBuild', 'SM_AP_P62Lounges'), ('LoungeBuild', 'SM_AP_P62LoungeSoft'), ('LoungeBuild', 'SM_AP_P62LoungeFloor'), ('CafeBuild', 'SM_AP_P60Cafe'), ('CafeBuild', 'SM_AP_P60CafeSoft')):
    bpy.ops.import_scene.fbx(filepath=str(HERE / d / (n + '.fbx')))
for o in bpy.data.objects:
    if o.type == 'MESH': o.data.transform(o.matrix_world); o.matrix_world.identity()
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.color_type = 'MATERIAL'
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.lens = 22
for name, e, t in (('a08', (-27.5, 15.5, 2.2), (-28.0, 27.0, 1.0)), ('a07', (-18.5, 2.0, 1.9), (-18.5, 9.0, 1.6)), ('cafe', (-41.5, 24.0, 1.9), (-46.5, 27.5, .6))):
    cam.location = e; cam.rotation_euler = (Vector(t) - Vector(e)).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = str(HERE / 'Preview' / ('p62_' + name + '.png')); bpy.ops.render.render(write_still=True)
