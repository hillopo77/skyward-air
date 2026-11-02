"""Pass51: the landside hall fit-out - one clear route, signed and lit (headless).

The hall had everything in it but no order: a free-standing START HERE board
in the middle of the entrance view, a check-in sign pointing sideways at desks
that were straight ahead, no sign at all on the security door, and one even
white floor. This builds SM_AP_P51Fitout (no collision; nothing the journey
walks or uses moves):

  route     a navy carpet runner with gold edges from the entrance door down
            the queue lane to the desks (1), then north and west to the
            security door (2), with warm flush 'runway' lights on its centre
            line and gold chevrons pointing the way
  gantry    over the runner past the information desk, two-sided:
            '1 CHECK-IN - BAG DROP  ^' facing the door, 'EXIT  ^' facing back
  canopy    an oak canopy over the check-in desks and belts at 3.9 m with
            '1 CHECK-IN - BAG DROP' on its fascia
  security  a sign after check-in, '2 SECURITY - GATES  <' (and '1 CHECK-IN'
            on its back), and an oak portal round the screening door with
            '2 SECURITY' and the gates on its header
  kiosks    a two-sided SELF CHECK-IN sign replacing the one-sided panel
  floor     a sand stone border round the hall and oak flooring under the
            check-in canopy, so the hall reads as zones, not one white floor
  cove      an oak ledge along the long walls at 3.75 m
World source metres, exported at the origin.
Usage: blender -b --factory-startup -P fitout51_blender.py
"""
import bpy, json, math, sys
from mathutils import Vector
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'Pass48'))
from mesh48 import Mesh, export

MATS = dict(navy=('MI_AP_P38ANavy', (.02, .05, .06)), gold=('MI_AP_P38AGold', (.72, .48, .11)),
            glow=('MI_AP_P51SignGlow', (1, .88, .66)), oak=('MI_AP_P43TOak', (.5, .31, .15)),
            steel=('MI_AP_P27Steel', (.5, .52, .54)), carpet=('MI_AP_P30Carpet', (.03, .06, .12)),
            lamp=('MI_AP_P51Runway', (1, .8, .52)), opal=('MI_AP_P51Soffit', (1, .87, .68)),
            stone=('MI_AP_P38AStone', (.58, .52, .38)))
FONT = 'C:/Windows/Fonts/segoeuib.ttf'
CEIL = 6.6
HALL = (-48.95, -26.1, -17.9, -4.12)                 # inner wall faces
WORDS = []
UP = Vector((0, 0, 1))


# ---------------------------------------------------------------- lettering

def text(body, at, normal, size, mat='glow', align='CENTER', depth=.004):
    """Raised lettering on a face: 'at' on the face, reading to the viewer's right."""
    n = Vector(normal).normalized()
    cu = bpy.data.curves.new('t', 'FONT'); cu.body = body
    cu.font = bpy.data.fonts.load(FONT, check_existing=True)
    cu.size = size; cu.resolution_u = 4; cu.align_x = align; cu.align_y = 'CENTER'; cu.extrude = depth; cu.space_character = 1.04
    o = bpy.data.objects.new('t', cu)
    o.location = Vector(at) + n * depth
    o.rotation_euler = (math.pi / 2, 0, math.atan2(n.y, n.x) + math.pi / 2)
    cu.materials.append(bpy.data.materials.get(MATS[mat][0]) or bpy.data.materials.new(MATS[mat][0]))
    bpy.context.scene.collection.objects.link(o); WORDS.append(o)


class Face:
    """2-D layout on one face of a sign: u to the viewer's right, v up."""

    def __init__(self, M, centre, normal):
        self.M, self.c, self.n = M, Vector(centre), Vector(normal).normalized()
        self.r = (-self.n).cross(UP).normalized()

    def P(self, u, v, out=0.0):
        return self.c + self.r * u + UP * v + self.n * out

    def panel(self, u0, u1, v0, v1, mat, out=.003):
        self.M.quad([tuple(self.P(u0, v0, out)), tuple(self.P(u1, v0, out)), tuple(self.P(u1, v1, out)),
                     tuple(self.P(u0, v1, out))], mat)

    def text(self, body, u, v, size, mat='glow', align='CENTER'):
        text(body, self.P(u, v), self.n, size, mat, align)

    def badge(self, digit, u, v, r=.2):
        """Gold disc with a navy numeral."""
        seg, pts = 28, []
        for k in range(seg):
            a = 2 * math.pi * k / seg
            pts.append(tuple(self.P(u + r * math.cos(a), v + r * math.sin(a), .006)))
        self.M.quad(pts, 'gold')
        text(digit, self.P(u, v - r * .06, .006), self.n, r * 1.35, 'navy')

    def arrow(self, u, v, s, d, mat='glow'):
        """Arrow of size s pointing d ('up', 'left', 'right'): a shaft and a head."""
        rot = {'up': (0, 1), 'left': (-1, 0), 'right': (1, 0), 'down': (0, -1)}[d]

        def Q(a, b):                                   # a along the arrow, b across it
            return tuple(self.P(u + a * rot[0] - b * rot[1], v + a * rot[1] + b * rot[0], .005))
        w = s * .14
        self.M.quad([Q(-s * .5, -w), Q(s * .1, -w), Q(s * .1, w), Q(-s * .5, w)], mat)
        self.M.quad([Q(s * .02, -s * .36), Q(s * .5, 0), Q(s * .02, s * .36)], mat)


def rods(M, pts, z0):
    for x, y in pts:
        M.box((x, y, (z0 + CEIL) / 2), (.016, .016, CEIL - z0), 'steel')
        M.cylinder((x, y, CEIL - .012), .05, .024, 'steel', seg=12)


def board(M, c, length, axis, h, depth=.14, edge=True):
    """Navy sign box with an oak edge band top and bottom; axis is the long direction."""
    x, y, z = c
    s = (length, depth, h) if axis == 'x' else (depth, length, h)
    M.box((x, y, z), s, 'navy')
    if edge:
        for dz in (h / 2 + .02, -h / 2 - .02):
            M.box((x, y, z + dz), (s[0] + .04, s[1] + .04, .04), 'oak')


# ---------------------------------------------------------------- pieces

def gantry(M):
    """Check-in gantry over the runner, past the information desk and the Flock."""
    x, y, z, L, h = -41.6, -13.0, 3.5, 5.6, .86
    board(M, (x, y, z), L, 'y', h)
    rods(M, [(x, y - L / 2 + .3), (x, y + L / 2 - .3)], z + h / 2 + .04)
    f = Face(M, (x - .07, y, z), (-1, 0, 0))         # facing the entrance
    f.badge('1', -L / 2 + .42, .08, .25)
    f.text('CHECK-IN  ·  BAG DROP', -L / 2 + .8, .1, .3, align='LEFT')
    f.text('Information and self check-in on your left', -L / 2 + .8, -.24, .12, 'gold', align='LEFT')
    f.arrow(L / 2 - .45, .0, .58, 'up')
    b = Face(M, (x + .07, y, z), (1, 0, 0))          # facing the desks
    b.text('EXIT  ·  TAXIS  ·  CAR PARK', -.3, 0, .26)
    b.arrow(L / 2 - .45, 0, .5, 'up')


def security_sign(M):
    """After check-in: turn left for security."""
    x, y, z, L, h = -32.4, -8.4, 3.5, 4.2, .8
    board(M, (x, y, z), L, 'x', h)
    rods(M, [(x - L / 2 + .3, y), (x + L / 2 - .3, y)], z + h / 2 + .04)
    f = Face(M, (x, y - .07, z), (0, -1, 0))         # seen walking north from the desks
    f.arrow(-L / 2 + .45, 0, .55, 'left')
    f.badge('2', -L / 2 + 1.05, .07, .23)
    f.text('SECURITY  ·  GATES', -L / 2 + 1.42, .09, .27, align='LEFT')
    f.text('Have your boarding pass ready', -L / 2 + 1.42, -.22, .11, 'gold', align='LEFT')
    b = Face(M, (x, y + .07, z), (0, 1, 0))          # seen from the security side
    b.badge('1', -.95, .0, .22)
    b.text('CHECK-IN', .25, 0, .27)
    b.arrow(L / 2 - .45, 0, .5, 'up')


def kiosk_sign(M):
    x, y, z, L, h = -39.45, -8.3, 2.92, 3.9, .5
    board(M, (x, y, z), L, 'x', h, depth=.1, edge=False)
    rods(M, [(x - L / 2 + .25, y), (x + L / 2 - .25, y)], z + h / 2)
    for n in ((0, -1, 0), (0, 1, 0)):
        f = Face(M, (x, y + .05 * n[1], z), n)
        f.text('SELF CHECK-IN', 0, .06, .24)
        f.text('Boarding passes  ·  bag tags', 0, -.16, .1, 'gold')


def canopy(M):
    """Oak canopy over the desks and belts: a ceiling at human height for check-in."""
    x0, x1, y0, y1, zb, zt = -31.9, -26.45, -17.55, -9.45, 3.92, 4.22
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    M.box((cx, cy, (zb + zt) / 2), (x1 - x0, y1 - y0, zt - zb), 'oak')
    # Pass53: no glowing soffit panels (they read as three glaring slabs); plain oak underneath.
    # Pass58: six small round downlights in the soffit light the desks and the
    # agents under the canopy (lights in Bake55.json 'canopy_lights').
    for x in (-30.6, -28.2):
        for y in (-16.3, -13.5, -10.7):
            M.cylinder((x, y, zb - .006), .11, .012, 'opal', seg=20)
            M.cylinder((x, y, zb - .002), .14, .008, 'steel', seg=20, cap_bottom=False)
    rods(M, [(x0 + .35, y0 + .35), (x0 + .35, y1 - .35), (x1 - .35, y0 + .35), (x1 - .35, y1 - .35)], zt)
    f = Face(M, (x0, cy, (zb + zt) / 2), (-1, 0, 0))
    f.panel(-3.4, 3.4, -.14, .14, 'navy')
    f.badge('1', -2.95, 0, .12)
    f.text('CHECK-IN  ·  BAG DROP', .15, -.005, .17)
    for side, yy in ((1, y0), (-1, y1)):               # the long faces carry it too
        g = Face(M, (cx, yy, (zb + zt) / 2), (0, -side, 0))
        g.panel(-2.4, 2.4, -.14, .14, 'navy')
        g.text('CHECK-IN', 0, -.005, .17)


def portal(M):
    """Oak portal round the screening door, with its sign above."""
    y, d = -4.14, .3
    for xa, xb in ((-43.5, -43.22), (-40.78, -40.5)):
        M.box(((xa + xb) / 2, y - d / 2, 1.39), (xb - xa, d, 2.78), 'oak')
    hx0, hx1, hz0, hz1 = -43.9, -40.1, 2.78, 3.5
    M.box(((hx0 + hx1) / 2, y - d / 2, (hz0 + hz1) / 2), (hx1 - hx0, d, hz1 - hz0), 'navy')
    M.box(((hx0 + hx1) / 2, y - d / 2, hz1 + .025), (hx1 - hx0 + .04, d + .04, .05), 'oak')
    f = Face(M, ((hx0 + hx1) / 2, y - d, (hz0 + hz1) / 2), (0, -1, 0))
    f.badge('2', -1.5, .06, .23)
    f.text('SECURITY', -1.12, .1, .3, align='LEFT')
    f.text('All gates  ·  A07  ·  A08', -1.12, -.21, .12, 'gold', align='LEFT')


# ---------------------------------------------------------------- floor

def strip(M, x0, x1, y0, y1, z, mat):
    M.box(((x0 + x1) / 2, (y0 + y1) / 2, z / 2), (x1 - x0, y1 - y0, z), mat)


def chevron(M, x, y, d, z=.0105, s=.36):
    """Gold V on the runner pointing along d (unit 2-D)."""
    a = math.atan2(d[1], d[0])
    for side in (1, -1):
        b = a + side * math.radians(135)
        cx, cy = x + math.cos(b) * s / 2, y + math.sin(b) * s / 2
        M.box((cx, cy, z - .002), (s, .06, .004), 'gold', rot=b)


def route(M):
    T, E = .008, .045                                   # carpet height, gold edge width
    legs = [  # (x0, x1, y0, y1, centre-line start, end)
        (-48.85, -31.3, -13.9, -12.1, (-48.3, -13.0), (-31.9, -13.0)),        # 1: door -> queue -> desks
        (-32.9, -31.3, -12.1, -6.8, (-32.1, -11.6), (-32.1, -6.8)),           # 2: north from the desks
        (-42.8, -31.3, -6.8, -5.2, (-31.9, -6.0), (-42.0, -6.0)),             #    west along the hall
        (-42.8, -41.2, -5.2, -4.2, (-42.0, -5.6), (-42.0, -4.5)),             #    into the security door
    ]
    for x0, x1, y0, y1, a, b in legs:
        strip(M, x0, x1, y0, y1, T, 'carpet')
    # gold edges on the outside of the route (none across the joins)
    edges = [(-48.85, -31.3, -13.9, -13.9 + E), (-48.85, -32.9, -12.1 - E, -12.1),     # leg 1 south, north
             (-31.3 - E, -31.3, -13.9, -5.2), (-32.9, -32.9 + E, -12.1, -6.8),          # east side, leg 2 west
             (-42.8, -32.9, -6.8, -6.8 + E), (-41.2, -31.3, -5.2 - E, -5.2),            # leg 3 south, north
             (-41.2 - E, -41.2, -5.2, -4.2), (-42.8, -42.8 + E, -6.8, -4.2)]            # leg 4 east, west side
    for x0, x1, y0, y1 in edges:
        strip(M, x0, x1, y0, y1, T + .001, 'gold')
    lamps = chevrons = 0
    for x0, x1, y0, y1, a, b in legs:
        a, b = Vector(a), Vector(b)
        d = (b - a); L = d.length; d.normalize()
        k = 0
        while k * 1.5 <= L:
            p = a + d * k * 1.5
            if k % 3 == 1:
                chevron(M, p.x, p.y, d); chevrons += 1
            else:
                M.cylinder((p.x, p.y, T + .003), .05, .006, 'lamp', seg=14); lamps += 1
            k += 1
    return lamps, chevrons


def zones(M):
    x0, x1, y0, y1 = HALL
    w, T = .5, .006
    door0, door1 = -13.9, -11.1                        # leave the entrance threshold to the runner
    strip(M, x0, x1, y0, y0 + w, T, 'stone')
    strip(M, x0, x1, y1 - w, y1, T, 'stone')
    strip(M, x0, x0 + w, y0 + w, door0, T, 'stone')
    strip(M, x0, x0 + w, door1, y1 - w, T, 'stone')
    strip(M, x1 - w, x1, y0 + w, y1 - w, T, 'stone')
    strip(M, -31.9, x1 - w, y0 + w, -9.45, T, 'oak')     # under the check-in canopy, to the runner's edge
    # cove ledge on the long walls for the ceiling uplights
    for yy, s in ((y0, 1), (y1, -1)):
        M.box(((x0 + x1) / 2, yy + s * .15, 3.76), (x1 - x0 - .1, .3, .06), 'oak')
        M.box(((x0 + x1) / 2, yy + s * .29, 3.81), (x1 - x0 - .1, .02, .16), 'oak')


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    M = Mesh(MATS)
    zones(M)
    lamps, chevrons = route(M)
    gantry(M); security_sign(M); kiosk_sign(M); canopy(M); portal(M)
    obj = M.finish('SM_AP_P51Fitout')
    bpy.ops.object.select_all(action='DESELECT')
    for o in WORDS:
        o.select_set(True)
    bpy.context.view_layer.objects.active = WORDS[0]
    bpy.ops.object.convert(target='MESH')
    for o in WORDS + [obj]:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = obj.data.name = 'SM_AP_P51Fitout'
    out = HERE / 'FitoutBuild'; out.mkdir(exist_ok=True)
    fbx = out / 'SM_AP_P51Fitout.fbx'
    export(obj, fbx)
    rep = dict(status='SUCCESS', asset=obj.name, fbx=str(fbx.resolve()), materials=[m.name for m in obj.data.materials],
               polygons=len(obj.data.polygons), runway_lamps=lamps, chevrons=chevrons, words=len(WORDS))
    (HERE / 'Fitout51Build.json').write_text(json.dumps(rep, indent=1), encoding='utf-8')
    print('FITOUT51', rep['polygons'])


try:
    main()
except Exception:
    import traceback
    (HERE / 'Fitout51Build.json').write_text(json.dumps(dict(status='ERROR', error=traceback.format_exc())), encoding='utf-8')
    print('FITOUT51 ERROR')
