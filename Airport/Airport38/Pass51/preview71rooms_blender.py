"""Pass71: preview renders of the rebuilt security hall and washrooms (headless, workbench).

The room kits with grey stand-ins for what the level already has there (wall shells with the oak
wainscot, ceiling, the portals, scanners and belts, tray stations, cubicle doors, toilets), so the
composition can be judged before the kits go into the game.
"""
import bpy
from math import radians
from mathutils import Vector
from pathlib import Path
HERE = Path(__file__).resolve().parent
g = dict(__name__='rooms70', __file__=str(HERE / 'rooms70_blender.py'))
exec(compile((HERE / 'rooms70_blender.py').read_text(encoding='utf-8').split('\ndef main():')[0], 'rooms70', 'exec'), g)
bpy.ops.wm.read_factory_settings(use_empty=True)
COL = {}
for d in (g['MATS'], g['FLOOR_MATS70'], g['SOFT_MATS']):
    for k, (mi, rgb) in d.items():
        COL.setdefault(mi, rgb)
for n in ('SM_AP_P70Rooms', 'SM_AP_P70RoomsSoft', 'SM_AP_P70RoomsFloor'):
    bpy.ops.import_scene.fbx(filepath=str(HERE / 'Rooms70Build' / (n + '.fbx')))
for m in bpy.data.materials:
    rgb = next((v for k, v in COL.items() if m.name.startswith(k)), None)
    if rgb:
        m.diffuse_color = (*rgb, 1)


def box(c, s, rgb):
    bpy.ops.mesh.primitive_cube_add(size=1, location=c); o = bpy.context.object; o.scale = s
    m = bpy.data.materials.new('x'); m.diffuse_color = (*rgb, 1); o.data.materials.append(m)


WALL, WAIN, CEIL, MACH = (.86, .83, .76), (.5, .31, .15), (.55, .36, .2), (.8, .8, .8)
for (x0, x1, y0, y1, h) in ((-49, -36, -4, 10, 3.5), (-23, -14, -12, -3, 3.2), (-26, -23, -12, -1, 3.2)):
    f = .18
    for (c, s) in ((((x0 + x1) / 2, y0 + f - .05, h / 2), (x1 - x0, .1, h)), (((x0 + x1) / 2, y1 - f + .05, h / 2), (x1 - x0, .1, h)),
                   ((x0 + f - .05, (y0 + y1) / 2, h / 2), (.1, y1 - y0, h)), ((x1 - f + .05, (y0 + y1) / 2, h / 2), (.1, y1 - y0, h))):
        box(c, s, WALL)
        box((c[0], c[1], .6), (s[0] + (.04 if s[0] < .2 else 0), s[1] + (.04 if s[1] < .2 else 0), 1.2), WAIN)
    box(((x0 + x1) / 2, (y0 + y1) / 2, -.01), (x1 - x0, y1 - y0, .02), (.84, .8, .72))
for px in (-45.5, -40.4):                                                   # portals
    for dx in (-.7, .7):
        box((px + dx, 3.0, 1.3), (.2, .6, 2.6), MACH)
    box((px, 3.0, 2.5), (1.6, .6, .25), MACH)
for bx in (-43.15, -38.05):                                                 # scanners, belts, tray stations
    box((bx + .28, 3.0, 1.09), (2.26, 2.2, 2.18), MACH)
    box((bx, 3.0, 1.3), (1.4, 2.3, 1.0), (.05, .05, .06))
    box((bx, 3.0, .8), (1.0, 3.6, .1), (.3, .3, .3))
    box((bx, .54, .41), (.68, .5, .82), (.1, .2, .25))
box((-48.05, 7.6, .86), (.8, 1.45, 1.73), (.1, .15, .2))                    # operator console
for cx in (-21.02, -17.12):                                                 # cubicle doors, toilets
    box((cx, -7.2, 1.14), (1.12, .05, 2.1), (.9, .88, .82))
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.color_type = 'MATERIAL'
sc.display.shading.light = 'STUDIO'; sc.display.shading.show_shadows = True; sc.display.shading.show_cavity = True
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.clip_start = .05
for name, e, t, lens in (('wc_stall1', (-21.0, -7.0, 1.6), (-21.6, -5.4, .8), 16), ('wc_stall4', (-17.12, -6.95, 1.6), (-17.12, -5.4, .7), 16),
                         ('wc_fronts', (-18.6, -11.2, 1.6), (-18.6, -7.3, 1.7), 16), ('wc_entry', (-22.4, -8.5, 1.6), (-16.0, -10.8, 1.3), 18),
                         ('sec_feature', (-38.0, 8.6, 1.7), (-48.8, 1.5, 1.7), 20)):
    cam.data.lens = lens; cam.location = e; cam.rotation_euler = (Vector(t) - Vector(e)).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = str(HERE / 'Preview' / ('r71_' + name + '.png')); bpy.ops.render.render(write_still=True)
print('PREVIEW71ROOMS done')
