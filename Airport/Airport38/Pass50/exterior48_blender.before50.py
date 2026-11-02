"""Pass48 makeover: the outside of the airport.

  fins      Vertical oak fins (80 x 300 mm, 0.9 m centres) standing 30 mm off
            every solid run of the landside, south and airside facades, from
            the ground to the parapet. Runs come from Exterior48.json: a
            sample is solid only when the wall (or its finish) is what the
            trace hits at the face at every height, so glazing, doors, signs
            and anything mounted on the wall stay clear.
  car park  West of the access road, opposite the forecourt: an asphalt
            field with 52 bays in four rows, white bay lines, cars of six
            colours in about two bays in three, lamp posts, a hedge along
            the road, a driveway, and a footpath and zebra crossing to the
            forecourt's south corner.
  beds      Raised planting beds with shrubs and grasses along the south
            facade.
  arrival   A navy totem at the car park entrance ('SKYWARD AIR / Terminal /
            Departures - Arrivals - P Parking') and three flagpoles.
  apron     Behind and east of the wing, clear of the taxi route (x 16, south)
            and of the tailplane's sweep: a baggage tug with three carts, a
            belt loader at the aft hold, a fuel truck, and two floodlight
            masts.

Trees are placed as SM_AP_Tree actors by the level script (Trees48.json).
World source coordinates, exported at the origin. Headless.
Usage: blender -b --factory-startup -P exterior48_blender.py -- <out_dir> <report.json>
"""
import bpy, json, math, random, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from mesh48 import Mesh, export

ARGS = sys.argv[sys.argv.index('--') + 1:]
OUT, REPORT = Path(ARGS[0]), Path(ARGS[1])
R = random.Random(48)
MATS = dict(
    oak=('MI_AP_P43TOak', (.66, .46, .27)), asphalt=('MI_AP_Asphalt', (.15, .16, .17)),
    white=('MI_AP_F39White', (.92, .92, .9)), concrete=('MI_AP_P34Cream', (.72, .66, .53)),
    soil=('MI_AP_Soil', (.05, .06, .05)), leaf=('MI_AP_Leaf', (.18, .4, .2)), leaf2=('MI_AP_LightLeaf', (.35, .55, .25)),
    sage=('MI_AP_P38ASage', (.14, .27, .23)), navy=('MI_AP_P38ANavy', (.02, .05, .06)),
    gold=('MI_AP_P38AGold', (.72, .48, .11)), text=('MI_AP_P38AText', (.89, .78, .52)),
    steel=('MI_AP_Steel', (.5, .52, .54)), dark=('MI_AP_DarkSteel', (.1, .11, .12)),
    rubber=('MI_AP_Rubber', (.02, .02, .02)), glass=('MI_AP_P43TInk', (.03, .07, .1)),
    ivory=('MI_AP_Ivory', (.85, .82, .75)), red=('MI_AP_P36Terracotta', (.48, .15, .08)),
    yellow=('MI_AP_Gold', (.82, .47, .07)), teal=('MI_AP_Teal', (.1, .4, .4)),
    led=('MI_AP_WhiteLED', (1, 1, 1)), redled=('MI_AP_RedLED', (1, 0, 0)), opal=('MI_AP_P38AOpal', (1, .82, .55)),
)
WALL = ('Airport38 complete physical perimeter and partitions', 'Airport43 fitted public wall finishes')
GROUND = -0.08
SLAB = -0.03                      # car park asphalt top
APRON = -3.689


# ------------------------------------------------------------------ fins
def fin_runs(f):
    out = []
    run = []
    for s in f['samples']:
        ok, walls = True, 0
        for h, hit in s['hits'].items():
            if float(h) > 3.1:
                continue
            if not hit:
                ok = False; break
            coord = hit[0] if f['axis'] == 'x' else hit[1]
            d = abs(coord - f['plane'])
            if hit[3] in WALL and d < .2:
                walls += 1
            elif d > 1.0:
                pass
            else:
                ok = False; break
        top = s['top'][2] if s['top'] else None
        if ok and walls >= 2 and top and top > 3.0:
            run.append((s['at'], top))
        else:
            if len(run) >= 4:
                out.append(run)
            run = []
    if len(run) >= 4:
        out.append(run)
    return out


def fins(M, facades, rep):
    spec = {'landside': (-49.132, -1, GROUND - .03), 'south': (-22.132, -1, GROUND - .03),
            'airside': (-13.868, 1, -0.7)}
    n = 0
    for f in facades:
        if f['name'] not in spec:
            continue
        face, out, z0 = spec[f['name']]
        for run in fin_runs(f):
            a0, a1 = run[0][0] + .15, run[-1][0] - .15
            k = int((a1 - a0) / .9)
            if k < 1:
                continue
            for i in range(k + 1):
                a = a0 + (a1 - a0) * i / k
                top = min(t for s, t in run if abs(s - a) < .35) - .03
                d = face + out * (.03 + .15)
                c = (d, a, (z0 + top) / 2) if f['axis'] == 'x' else (a, d, (z0 + top) / 2)
                s = (.30, .08, top - z0) if f['axis'] == 'x' else (.08, .30, top - z0)
                M.box(c, s, 'oak'); n += 1
            rep.setdefault('fin_runs', []).append([f['name'], round(run[0][0], 2), round(run[-1][0], 2), k + 1])
    rep['fins'] = n


# ------------------------------------------------------------------ car
CAR_COLOURS = ['ivory', 'steel', 'navy', 'red', 'dark', 'teal', 'ivory', 'steel', 'yellow', 'red', 'navy']


def car(M, x, y, yaw, colour):
    """Stylised hatchback, 4.3 x 1.8 x 1.5 m, nose along +yaw."""
    cy, sy = math.cos(yaw), math.sin(yaw)

    def P(lx, ly, z):           # local x = forward, local y = left
        return (x + lx * cy - ly * sy, y + lx * sy + ly * cy, SLAB + z)
    M.box(P(0, 0, .52), (4.3, 1.8, .44), colour, rot=yaw)                        # lower body
    M.box(P(-.05, 0, .84), (3.9, 1.74, .2), colour, rot=yaw)                     # shoulder
    M.box(P(-.3, 0, 1.13), (2.2, 1.64, .38), 'glass', rot=yaw)                   # glasshouse
    M.box(P(-.35, 0, 1.36), (1.9, 1.56, .08), colour, rot=yaw)                   # roof
    M.box(P(2.16, .6, .72), (.04, .3, .12), 'led', rot=yaw)
    M.box(P(2.16, -.6, .72), (.04, .3, .12), 'led', rot=yaw)
    M.box(P(-2.16, .62, .78), (.04, .26, .1), 'redled', rot=yaw)
    M.box(P(-2.16, -.62, .78), (.04, .26, .1), 'redled', rot=yaw)
    for lx in (1.35, -1.35):
        for ly in (.84, -.84):
            cx, cyy, cz = P(lx, ly, .33)
            # wheel axis is the car's local y
            M.cylinder((cx, cyy, cz), .33, .24, 'rubber', seg=12, axis='y' if abs(sy) < .5 else 'x')


def carpark(M, rep, trees):
    x_e, x_w, y_s, y_n = -74.0, -108.0, -64.0, -25.0
    M.box(((x_w + x_e) / 2, (y_s + y_n) / 2, SLAB - .06), (x_e - x_w, y_n - y_s, .12), 'asphalt')
    # driveway to the road and footpath to the crossing
    M.box((-71.1, -56.5, SLAB - .06), (6.2, 7.0, .12), 'asphalt')
    M.box((-71.1, -26.3, SLAB - .055), (6.2, 2.6, .12), 'concrete')
    # zebra over the road (x -68..-62) and a landing on the forecourt side
    for i in range(8):
        x = -67.6 + i * .75
        M.quad([(x, -27.4, .028), (x + .45, -27.4, .028), (x + .45, -25.2, .028), (x, -25.2, .028)], 'white')
    M.box((-59.95, -25.8, -.06), (3.9, 3.6, .12), 'concrete')
    rows = [(-79.8, -75.0, +1), (-90.8, -86.0, -1), (-95.6, -90.8, +1), (-106.6, -101.8, -1)]
    cars = 0
    for r, (a, b, face) in enumerate(rows):
        for i in range(14):
            y0 = -61.0 + i * 2.5
            # bay separator lines (along x)
            M.quad([(a, y0 - .05, SLAB + .005), (b, y0 - .05, SLAB + .005), (b, y0 + .05, SLAB + .005), (a, y0 + .05, SLAB + .005)], 'white')
            if i == 13:
                break
            if R.random() < .68:
                yaw = 0.0 if face > 0 else math.pi                  # nose toward the aisle side noted below
                cx = (a + b) / 2 + R.uniform(-.15, .15)
                car(M, cx, y0 + 1.25 + R.uniform(-.08, .08), yaw + R.uniform(-.03, .03) + (math.pi if R.random() < .2 else 0),
                    R.choice(CAR_COLOURS)); cars += 1
        # end islands with a tree each end
        for yy in (-62.6, -27.4 + 0.0):
            M.box(((a + b) / 2, yy, GROUND + .1), (abs(b - a), 1.6, .2), 'concrete')
            M.box(((a + b) / 2, yy, GROUND + .205), (abs(b - a) - .2, 1.4, .01), 'soil')
            trees.append([(a + b) / 2, yy, GROUND + .2, R.uniform(0, 360), R.uniform(.75, .95)])
    # lamp posts in the aisles
    for xa in (-82.9, -98.7):
        for yl in (-56.0, -44.0, -32.0):
            M.cylinder((xa, yl, GROUND + 3.5), .07, 7.0, 'dark', seg=10)
            M.box((xa, yl, GROUND + 7.0), (1.2, .28, .12), 'dark')
            M.box((xa, yl, GROUND + 6.935), (1.0, .2, .01), 'led')
    # hedge along the road side, gaps for the driveway and footpath
    for y0, y1 in ((-64.0, -60.4), (-52.6, -28.0)):
        M.box((-73.6, (y0 + y1) / 2, GROUND + .55), (.9, y1 - y0, 1.1), 'leaf')
    rep['cars'] = cars


# ------------------------------------------------------------------ beds
def beds(M, trees):
    for x in (-45.0, -38.0, -31.0, -24.0, -17.5):          # a tree row on the grass beyond the beds
        trees.append([x, -27.5, GROUND, R.uniform(0, 360), R.uniform(.7, .9)])
    for x0, x1 in ((-48.4, -36.2), (-35.0, -26.6), (-25.4, -16.0)):
        M.box(((x0 + x1) / 2, -23.25, GROUND + .25), (x1 - x0, 1.4, .5), 'concrete')
        M.box(((x0 + x1) / 2, -23.25, GROUND + .505), (x1 - x0 - .16, 1.24, .01), 'soil')
        x = x0 + .5
        while x < x1 - .4:
            if R.random() < .55:
                M.blob((x, -23.25 + R.uniform(-.25, .25), GROUND + .7), R.uniform(.32, .48), R.choice(['leaf', 'leaf2']), squash=.75)
            else:
                for k in range(5):
                    a = 2 * math.pi * k / 5
                    M.box((x + .12 * math.cos(a), -23.25 + .12 * math.sin(a), GROUND + .85), (.04, .04, .7), 'sage')
            x += R.uniform(.55, .8)


# ------------------------------------------------------------------ arrival
def totem(M):
    x, y = -71.0, -67.0                      # verge west of the road, past the car park
    M.box((x, y, GROUND + 2.0), (.5, 1.6, 4.0), 'navy')
    M.box((x - .26, y, GROUND + 3.55), (.02, 1.4, .03), 'gold')
    lines = [('SKYWARD AIR', .26, 3.2, 'gold'), ('TERMINAL', .17, 2.75, 'text'),
             ('DEPARTURES', .13, 2.2, 'text'), ('ARRIVALS', .13, 1.9, 'text'), ('P  PARKING', .13, 1.5, 'text')]
    objs = []
    for body, size, z, mat in lines:
        for side in (-1, 1):                                    # both faces, read from either direction
            cu = bpy.data.curves.new(body, 'FONT'); cu.body = body; cu.size = size
            cu.align_x = 'CENTER'; cu.align_y = 'CENTER'; cu.extrude = .004
            o = bpy.data.objects.new(body, cu)
            o.location = (x + side * .256, y, GROUND + z)
            o.rotation_euler = (math.pi / 2, 0, -math.pi / 2 if side < 0 else math.pi / 2)
            cu.materials.append(bpy.data.materials.get(MATS[mat][0]) or bpy.data.materials.new(MATS[mat][0]))
            bpy.context.scene.collection.objects.link(o); objs.append(o)
    return objs


def flags(M):
    for i, y in enumerate((-30.5, -32.0, -33.5)):
        x = -60.4
        M.cylinder((x, y, GROUND + 4.5), .045, 9.0, 'steel', seg=10)
        M.cylinder((x, y, GROUND + 9.03), .07, .06, 'gold', seg=10)
        # flag: navy field with a gold band, slight wave
        for k in range(6):
            xa, xb = x + .05 + k * .27, x + .05 + (k + 1) * .27
            wa, wb = .06 * math.sin(k * .9), .06 * math.sin((k + 1) * .9)
            for pts in ([(xa, y + wa, GROUND + 7.6), (xb, y + wb, GROUND + 7.6), (xb, y + wb, GROUND + 8.85), (xa, y + wa, GROUND + 8.85)],
                        [(xa, y + wa - .004, GROUND + 8.85), (xb, y + wb - .004, GROUND + 8.85), (xb, y + wb - .004, GROUND + 7.6), (xa, y + wa - .004, GROUND + 7.6)]):
                M.quad(pts, 'navy' if i != 1 else 'ivory')
            M.quad([(xa, y + wa + .002, GROUND + 8.05), (xb, y + wb + .002, GROUND + 8.05),
                    (xb, y + wb + .002, GROUND + 8.25), (xa, y + wa + .002, GROUND + 8.25)], 'gold')


# ------------------------------------------------------------------ apron
def wheels(M, x, y, z, r, half_track, along_y, xs):
    for d in xs:
        for t in (-half_track, half_track):
            cx, cy = (x + t, y + d) if along_y else (x + d, y + t)
            M.cylinder((cx, cy, z + r), r, .22, 'rubber', seg=12, axis='x' if along_y else 'y')


def apron(M):
    z = APRON
    # baggage tug (nose south) and three carts behind it
    x, y = 28.0, 27.0
    M.box((x, y, z + .55), (1.4, 2.6, .7), 'yellow'); M.box((x, y + .5, z + 1.15), (1.3, 1.0, .5), 'glass')
    M.box((x, y + .5, z + 1.42), (1.4, 1.1, .05), 'yellow')
    wheels(M, x, y, z, .32, .6, True, (-.8, .8))
    for k in range(3):
        cy = y + 3.6 + k * 3.0
        M.box((x, cy, z + .55), (1.5, 2.4, .08), 'dark')
        for sx in (-.72, .72):
            M.box((x + sx, cy, z + 1.05), (.05, 2.4, 1.0), 'steel')
        M.box((x, cy, z + 1.58), (1.55, 2.45, .06), 'ivory')
        for b in range(R.randint(2, 4)):
            M.box((x + R.uniform(-.35, .35), cy + R.uniform(-.7, .7), z + .78), (R.uniform(.35, .55), R.uniform(.5, .75), R.uniform(.25, .4)),
                  R.choice(['navy', 'red', 'dark', 'teal']))
        wheels(M, x, cy, z, .2, .6, True, (-.8, .8))
        M.box((x, cy - 1.45, z + .45), (.06, .7, .06), 'dark')
    # belt loader at the aft hold, sloping up to the belly on the right side
    bx, by = 21.6, 31.0
    M.box((bx + 1.2, by, z + .5), (3.6, 1.8, .55), 'ivory')
    wheels(M, bx + 1.2, by, z, .3, .75, False, (-1.2, 1.2))
    L, top = 5.8, -2.35
    ang = math.atan2(top - (z + .9), L)
    for k in range(10):
        t0, t1 = k / 10, (k + 1) / 10
        xa, xb = bx + 3.0 - t0 * L * math.cos(ang), bx + 3.0 - t1 * L * math.cos(ang)
        za, zb = z + .9 + t0 * L * math.sin(-ang) * -1, z + .9 + t1 * L * math.sin(-ang) * -1
        M.quad([(xa, by - .35, za), (xa, by + .35, za), (xb, by + .35, zb), (xb, by - .35, zb)], 'rubber')   # belt faces up
        M.quad([(xa, by - .4, za - .12), (xb, by - .4, zb - .12), (xb, by - .4, zb + .05), (xa, by - .4, za + .05)], 'steel')
        M.quad([(xa, by + .4, za + .05), (xb, by + .4, zb + .05), (xb, by + .4, zb - .12), (xa, by + .4, za - .12)], 'steel')
    # fuel truck, parked aft and east, nose south
    fx, fy = 33.5, 38.0
    M.box((fx, fy - 3.4, z + 1.3), (2.4, 2.0, 2.0), 'ivory'); M.box((fx, fy - 4.35, z + 1.75), (2.2, .1, .8), 'glass')
    M.cylinder((fx, fy + 1.0, z + 1.75), 1.15, 6.4, 'steel', seg=20, axis='y')
    M.box((fx, fy + 1.0, z + .55), (2.4, 7.0, .3), 'dark')
    M.box((fx + 1.17, fy + 1.0, z + 1.75), (.02, 3.0, .35), 'red')
    wheels(M, fx, fy, z, .5, 1.0, True, (-3.6, -.2, 1.2, 3.4))
    # floodlight masts, outside the wing sweep
    for mx, my in ((44.0, -12.0), (44.0, 46.0)):
        M.cylinder((mx, my, z + 10.0), .22, 20.0, 'steel', seg=12)
        M.box((mx, my, z + 20.2), (2.6, .5, .9), 'dark')
        M.box((mx - .3, my, z + 19.74), (2.2, .4, .02), 'led')


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    OUT.mkdir(parents=True, exist_ok=True)
    survey = json.loads((HERE / 'Exterior48.json').read_text(encoding='utf-8'))
    spec = {f['name']: f for f in json.loads((HERE / 'Exterior48Spec.json').read_text(encoding='utf-8'))['facades']}
    for f in survey['facades']:
        f.update({k: v for k, v in spec[f['name']].items() if k != 'name'})
    rep, trees = {}, []
    M = Mesh(MATS)
    fins(M, survey['facades'], rep)
    carpark(M, rep, trees)
    beds(M, trees)
    flags(M)
    apron(M)
    words = totem(M)
    obj = M.finish('SM_AP_P48Exterior')
    bpy.ops.object.select_all(action='DESELECT')
    for o in words:
        o.select_set(True)
    bpy.context.view_layer.objects.active = words[0]
    bpy.ops.object.convert(target='MESH')
    for o in words + [obj]:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = 'SM_AP_P48Exterior'; obj.data.name = obj.name
    for p in obj.data.polygons:
        p.use_smooth = False
    fbx = OUT / 'SM_AP_P48Exterior.fbx'
    export(obj, fbx)
    (HERE / 'Trees48.json').write_text(json.dumps(dict(mesh='SM_AP_Tree', trees=trees)), encoding='utf-8')
    rep.update(status='SUCCESS', asset=obj.name, fbx=str(fbx.resolve()),
               materials=[m.name for m in obj.data.materials], polygons=len(obj.data.polygons), trees=len(trees))
    REPORT.write_text(json.dumps(rep, indent=1), encoding='utf-8')
    print('EXTERIOR48', rep['fins'], rep['cars'], rep['polygons'], len(trees))


main()
