"""Pass50: Workbench preview of the new tree and two cars (headless)."""
import bpy, math
from pathlib import Path

HERE = Path(__file__).resolve().parent
COL = {'MI_AP_Bark': (.25, .16, .1), 'MI_AP_Leaf': (.16, .36, .17), 'MI_AP_LightLeaf': (.33, .52, .22),
       'MI_AP_P36Terracotta': (.48, .15, .08), 'MI_AP_Teal': (.1, .4, .4), 'MI_AP_P43TInk': (.03, .06, .09),
       'MI_AP_Rubber': (.02, .02, .02), 'MI_AP_Steel': (.6, .62, .64), 'MI_AP_WhiteLED': (1, 1, .9),
       'MI_AP_RedLED': (.9, .05, .05), 'MI_AP_DarkSteel': (.08, .09, .1)}
bpy.ops.wm.read_factory_settings(use_empty=True)
for name, loc in (('SM_AP_P50Tree', (0, 0, 0)), ('SM_AP_P50Car_Red', (4.5, -2.5, 0)), ('SM_AP_P50Car_Teal', (4.5, 1.0, 0))):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(HERE / 'StyleBuild' / (name + '.fbx')))
    for o in set(bpy.data.objects) - before:
        o.location = loc
        for m in o.data.materials:
            m.diffuse_color = (*COL.get(m.name.split('.')[0], (.7, .7, .7)), 1)
sc = bpy.context.scene
cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera = cam
cam.location = (13, -9, 3.2); cam.rotation_euler = (math.radians(82), 0, math.radians(56)); cam.data.lens = 35
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'MATERIAL'
sc.display.shading.show_shadows = True; sc.display.shading.show_cavity = True
sc.render.resolution_x, sc.render.resolution_y = 1400, 800
sc.render.filepath = str(HERE / 'StyleBuild' / 'preview.png')
bpy.ops.render.render(write_still=True)
print('PREVIEW50 done')
