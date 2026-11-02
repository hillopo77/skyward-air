"""Pass47: three Skyward Air travel posters for the bare corridors.

The public-return and landside corridors are bare wall end to end. Airports
fill such walls with lit advertising, so these go into advert lightboxes on the
corridor walls. Same flat illustrative language as the check-in hall's
'AZURE BAY / YOUR NEXT CHAPTER' artwork: layered hills, a disc sun, house
navy / teal / gold / cream, Segoe UI lettering. 1024 x 640, rendered flat.

Usage: blender -b --factory-startup -P posters47_blender.py -- <out_dir>
"""
import bpy, bmesh, sys, math
from pathlib import Path

OUT = Path(sys.argv[sys.argv.index('--') + 1])
W, H = 1024, 640
EM, TOP = 1.8, -0.04          # calibrated against make_display_art38 (Pass47)


def lin(h):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return (*[v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c], 1.0)


def mat(h):
    m = bpy.data.materials.new('m'); m.diffuse_color = lin(h); return m


def px(x, y):
    return x - W / 2, H / 2 - y


def poly(pts, h, z):
    bm = bmesh.new()
    bm.faces.new([bm.verts.new((*px(x, y), z)) for x, y in pts])
    me = bpy.data.meshes.new('p'); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new('p', me); ob.data.materials.append(mat(h))
    bpy.context.scene.collection.objects.link(ob)


def rect(x0, y0, x1, y1, h, z):
    poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], h, z)


def disc(cx, cy, r, h, z, seg=48):
    poly([(cx + r * math.cos(2 * math.pi * k / seg), cy + r * math.sin(2 * math.pi * k / seg)) for k in range(seg)], h, z)


def ridge(base, amp, waves, phase, h, z, steps=96):
    pts = [(0, H)]
    for k in range(steps + 1):
        x = W * k / steps
        y = base - amp * (0.6 * math.sin(waves * 2 * math.pi * x / W + phase)
                          + 0.4 * math.sin(waves * 4.3 * math.pi * x / W + phase * 1.7))
        pts.append((x, y))
    pts.append((W, H))
    poly(pts, h, z)


def text(s, x, y, size, h, bold=False, z=1.0):
    cu = bpy.data.curves.new('t', 'FONT'); cu.body = s
    cu.font = bpy.data.fonts.load('C:/Windows/Fonts/segoeuib.ttf' if bold else 'C:/Windows/Fonts/segoeui.ttf', check_existing=True)
    cu.size = size * EM; cu.align_y = 'TOP'
    ob = bpy.data.objects.new('t', cu); ob.data.materials.append(mat(h))
    X, Y = px(x, y + size * TOP); ob.location = (X, Y, z)
    bpy.context.scene.collection.objects.link(ob)


def poster(name, sky, sun, layers, title, line, foot):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    rect(0, 0, W, H, sky, -1.0)
    disc(*sun, -0.9)
    for k, (base, amp, waves, phase, col) in enumerate(layers):
        ridge(base, amp, waves, phase, col, -0.8 + 0.05 * k)
    rect(0, 470, W, H, '#102C35', 0.5)
    text('SKYWARD AIR', 48, 492, 22, '#A3C3BC', True)
    text(title, 46, 520, 46, '#F1D69C', True)
    text(line, 48, 592, 22, '#E5EBE3')
    text(foot, 700, 600, 16, '#AECCC1', True)
    cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); cam.data.type = 'ORTHO'
    cam.data.ortho_scale = W; cam.location = (0, 0, 10); sc.collection.objects.link(cam); sc.camera = cam
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.display.shading.light = 'FLAT'; sc.display.shading.color_type = 'MATERIAL'
    sc.view_settings.view_transform = 'Standard'
    sc.render.resolution_x, sc.render.resolution_y = W, H
    sc.render.filepath = str(OUT / ('T_AP_Poster47_%s.png' % name))
    bpy.ops.render.render(write_still=True)


OUT.mkdir(parents=True, exist_ok=True)
poster('AzureBay', '#2E5E6B', (760, 170, 62, '#F1D69C'),
       [(330, 46, 1.1, 0.4, '#2B4C55'), (380, 34, 1.7, 1.9, '#1F3D45'), (430, 20, 2.3, 3.1, '#447B7A')],
       'AZURE BAY', 'Your next chapter starts at Gate A07', 'DAILY  /  SA107')
poster('Highlands', '#5C7F82', (250, 150, 54, '#E9C98A'),
       [(300, 90, 1.3, 2.4, '#3B5A5E'), (360, 60, 2.1, 0.8, '#2A464B'), (420, 30, 2.9, 4.0, '#1C414B')],
       'THE HIGHLANDS', 'Quiet peaks, two hours away', 'FROM AUTUMN  /  SA211')
poster('CoralCoast', '#447B7A', (512, 200, 80, '#F1D69C'),
       [(400, 14, 2.0, 0.0, '#5C9C97'), (430, 10, 3.5, 1.2, '#2E5E6B'), (455, 6, 5.0, 2.6, '#E5D9B8')],
       'CORAL COAST', 'Sun, sea and nowhere to be', 'WEEKENDS  /  SA305')
print('POSTERS47 done')
