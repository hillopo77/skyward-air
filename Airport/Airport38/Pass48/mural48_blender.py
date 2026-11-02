"""Pass48: the arrivals welcome mural, 11.9 x 1.8 m, for the public return.

Arriving passengers walk the public-return corridor from reclaim to the
forecourt past a bare 12 m wall. This is the wall's mural, in the house
illustration language of the Pass47 posters (layered hills, disc sun, navy /
teal / gold / cream, Segoe UI): the Azure Bay coastline at golden hour with
a Skyward Air aircraft climbing out, and 'WELCOME TO AZURE BAY'.
Rendered flat (Workbench, orthographic), 4096 x 620.

Usage: blender -b --factory-startup -P mural48_blender.py -- <out_png>
"""
import bpy, bmesh, sys, math
from pathlib import Path

OUT = Path(sys.argv[sys.argv.index('--') + 1])
W, H = 4096, 620
EM, TOP = 1.8, -0.04


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


def disc(cx, cy, r, h, z, seg=64):
    poly([(cx + r * math.cos(2 * math.pi * k / seg), cy + r * math.sin(2 * math.pi * k / seg)) for k in range(seg)], h, z)


def ridge(base, amp, waves, phase, h, z, steps=240):
    pts = [(0, H)]
    for k in range(steps + 1):
        x = W * k / steps
        y = base - amp * (0.6 * math.sin(waves * 2 * math.pi * x / W + phase)
                          + 0.4 * math.sin(waves * 4.3 * math.pi * x / W + phase * 1.7))
        pts.append((x, y))
    pts.append((W, H))
    poly(pts, h, z)


def text(s, x, y, size, h, bold=False, z=1.0, align='LEFT'):
    cu = bpy.data.curves.new('t', 'FONT'); cu.body = s; cu.align_x = align
    cu.font = bpy.data.fonts.load('C:/Windows/Fonts/segoeuib.ttf' if bold else 'C:/Windows/Fonts/segoeui.ttf', check_existing=True)
    cu.size = size * EM; cu.align_y = 'TOP'
    ob = bpy.data.objects.new('t', cu); ob.data.materials.append(mat(h))
    X, Y = px(x, y + size * TOP); ob.location = (X, Y, z)
    bpy.context.scene.collection.objects.link(ob)


def plane(cx, cy, s, h, z):
    """Side-on airliner silhouette climbing to the right, scale s px per metre-ish."""
    fus = [(-60, -4), (40, -8), (58, -4), (62, 0), (56, 4), (-50, 6), (-62, 2)]
    tail = [(-48, -2), (-62, -26), (-52, -26), (-34, -4)]
    wing = [(-6, 0), (-26, 16), (-14, 16), (14, 2)]
    a = math.radians(-12)
    for shape in (fus, tail, wing):
        poly([(cx + s * (x * math.cos(a) - y * math.sin(a)), cy + s * (x * math.sin(a) + y * math.cos(a))) for x, y in shape], h, z)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    # golden-hour sky in bands
    for k, col in enumerate(['#1F4C5B', '#2C6170', '#3F7A82', '#6E9A8F', '#C9B387', '#E8C98E']):
        rect(0, k * 52, W, (k + 1) * 52 + 1, col, -1.0 + .01 * k)
    rect(0, 312, W, 360, '#E8C98E', -0.94)
    disc(3050, 300, 120, '#F6DFA4', -0.9)
    disc(3050, 300, 160, '#EFD08F', -0.91)
    # far headlands, sea, near hills
    ridge(300, 40, 1.2, 0.8, '#5B8A86', -0.85)
    rect(0, 330, W, H, '#2E6E78', -0.8)
    for k in range(9):                                     # glints on the water
        y = 350 + k * 12
        rect(2850 - k * 30, y, 3260 + k * 30, y + 3, '#E9CF94', -0.79)
    ridge(420, 60, 2.0, 2.2, '#2B4C55', -0.7)
    ridge(470, 40, 3.1, 0.6, '#1F3D45', -0.65)
    ridge(520, 26, 4.4, 4.1, '#447B7A', -0.6)
    plane(1250, 150, 2.4, '#F4EEDF', -0.5)
    # lettering band
    rect(0, 548, W, H, '#102C35', 0.5)
    text('WELCOME TO', 120, 34, 40, '#E5EBE3', True, z=2.0)
    text('AZURE BAY', 110, 80, 100, '#FFF1CF', True, z=2.0)
    text('SKYWARD AIR  /  Baggage reclaim behind you  /  Taxis & shuttle ahead  /  Have a lovely stay', 120, 566, 26, '#AECCC1', True)
    cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); cam.data.type = 'ORTHO'
    cam.data.ortho_scale = W; cam.location = (0, 0, 10); sc.collection.objects.link(cam); sc.camera = cam
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.display.shading.light = 'FLAT'; sc.display.shading.color_type = 'MATERIAL'
    sc.view_settings.view_transform = 'Standard'
    sc.render.resolution_x, sc.render.resolution_y = W, H
    OUT.parent.mkdir(parents=True, exist_ok=True)
    sc.render.filepath = str(OUT)
    bpy.ops.render.render(write_still=True)
    print('MURAL48', OUT)


main()
