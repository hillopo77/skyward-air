import bpy, math
from mathutils import Vector
from pathlib import Path
HERE = Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True)
for n in ('SM_AP_P60CafeSoft', 'SM_AP_P60Cafe'):
    bpy.ops.import_scene.fbx(filepath=str(HERE / 'CafeBuild' / (n + '.fbx')))
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.data.transform(o.matrix_world); o.matrix_world.identity()
print('BOUNDS', [(o.name, [round(min((o.matrix_world @ Vector(c))[k] for c in o.bound_box), 1) for k in range(3)]) for o in bpy.data.objects if o.type == 'MESH'])
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.color_type = 'MATERIAL'
sc.display.shading.light = 'STUDIO'
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.lens = 35
for name, e, t in (('chairs', (-40.6, 19.6, 1.5), (-43.9, 18.4, .45)), ('library', (-36.0, 21.5, 1.7), (-32.2, 20.0, 1.4))):
    cam.location = e; cam.rotation_euler = (Vector(t) - Vector(e)).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = str(HERE / 'Preview' / ('p61_' + name + '.png')); bpy.ops.render.render(write_still=True)
