"""Pass47: an Arrivals screen in the house style of make_display_art38.py.

Pass46 put a flight board in Arrivals & Reclaim and gave it the Departures
role, so the arrivals hall shows DEPARTURES. There is no arrivals artwork to
route it to. make_display_art38 drew every screen with PIL, which is no longer
installed, so this reproduces its layout exactly in Blender: 1024 x 640, the
same hex colours, Segoe UI and Segoe UI Bold at the same pixel sizes and
positions, rendered flat (Workbench, Standard view transform) so colours are
exact.

Usage: blender -b --factory-startup -P arrivals_art47_blender.py -- <out.png>
"""
import bpy, bmesh, sys, math

ARGS = sys.argv[sys.argv.index('--') + 1:]
OUT = ARGS[0]
WHICH = ARGS[1] if len(ARGS) > 1 else 'Arrivals'
EM = float(ARGS[2]) if len(ARGS) > 2 else 1.0
TOP = float(ARGS[3]) if len(ARGS) > 3 else 0.0
W, H = 1024, 640
DEPARTURES = ('DEPARTURES', 'SKYWARD AIR', [('SA107', 'Azure Bay / Gate A07'), ('A07', 'Check in, screen, then board'), ('A08', 'Flight information only')], 'FOLLOW THE GOLD ROUTE TO YOUR GATE')
SPEC = ('ARRIVALS', 'SKYWARD AIR / BAGGAGE RECLAIM',
        [('SA106', 'From Azure Bay / Landed'), ('BELT 1', 'Bags from SA106 / On belt'),
         ('EXIT', 'Public exit / Taxis and shuttle')],
        'WELCOME TO SKYWARD AIR')


def hexc(h):
    h = h.lstrip('#')
    srgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    # Workbench flat colour is linear; convert so the PNG reads back the hex.
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]
    return (*lin, 1.0)


def mat(name, h):
    m = bpy.data.materials.new(name)
    m.diffuse_color = hexc(h)
    return m


def px(x, y):
    """Image pixels (origin top-left) to scene units (1 unit = 1 px, origin centre)."""
    return x - W / 2, H / 2 - y


def _outline(x0, y0, x1, y1, r, seg=10):
    pts = []
    for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        for k in range(seg + 1):
            a = math.radians(a0 + 90 * k / seg)
            pts.append(px(cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def _poly(pts, h, z):
    bm = bmesh.new()
    bm.faces.new([bm.verts.new((x, y, z)) for x, y in pts])
    me = bpy.data.meshes.new('r'); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new('r', me); ob.data.materials.append(mat('m', h))
    bpy.context.scene.collection.objects.link(ob)


def rrect(x0, y0, x1, y1, r, h, z=0.0, outline=0, inner=None):
    """Filled rounded rect; with outline, a ring of that width over `inner`."""
    r = max(r, 0.01)
    _poly(list(reversed(_outline(x0, y0, x1, y1, r))), h, z)
    if outline:
        _poly(list(reversed(_outline(x0 + outline, y0 + outline, x1 - outline, y1 - outline,
                                     max(0.01, r - outline)))), inner, z + 0.01)


def line(x0, y, x1, h, wpx=2):
    rrect(x0, y - wpx / 2, x1, y + wpx / 2, 0.001, h, z=0.1)


def text(s, x, y, size, h, bold=False):
    cu = bpy.data.curves.new('t', 'FONT')
    cu.body = s
    cu.font = bpy.data.fonts.load('C:/Windows/Fonts/segoeuib.ttf' if bold else 'C:/Windows/Fonts/segoeui.ttf',
                                  check_existing=True)
    cu.size = size * EM
    cu.align_y = 'TOP'
    ob = bpy.data.objects.new('t', cu)
    ob.data.materials.append(mat('m', h))
    # PIL draws from the top of the line box; nudge by the font's internal leading.
    X, Y = px(x, y + size * TOP)
    ob.location = (X, Y, 0.2)
    bpy.context.scene.collection.objects.link(ob)


bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
title, sub, rows, footer = DEPARTURES if WHICH == 'Departures' else SPEC
rrect(0, 0, W, H, 0.001, '#102C35', z=-0.2)
rrect(18, 18, 1006, 622, 24, '#447B7A', z=-0.1, outline=3, inner='#102C35')
text('SKYWARD AIR', 48, 35, 27, '#A3C3BC', True)
text(title, 48, 86, 56, '#F1D69C', True)
text(sub, 50, 166, 30, '#E5EBE3')
line(48, 220, 976, '#4C7776')
for j, (tag, body) in enumerate(rows):
    y = 258 + j * 92
    rrect(42, y - 8, 982, y + 65, 9, '#1C414B', z=0.0)
    text(tag, 60, y, 29, '#A1C8B2', True)
    text(body, 210, y, 29, '#F1E9D6')
text(footer, 49, 568, 24, '#AECCC1', True)

cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
cam.data.type = 'ORTHO'; cam.data.ortho_scale = W
cam.location = (0, 0, 10); sc.collection.objects.link(cam); sc.camera = cam
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'FLAT'; sc.display.shading.color_type = 'MATERIAL'
sc.view_settings.view_transform = 'Standard'
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.render.film_transparent = False
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print('ARRIVALS_ART47', OUT)
