"""Pass48 makeover: four feature pieces inside the terminal.

Each sits on a wall run that Walls48.json measured clear (the wall or its
finish is the first thing hit at 1.2, 2.2 and 3.0 m all along it).

  check-in    South wall, x -34.6..-27.4, face y -17.868: a floor-to-baffle
              field of vertical oak slats (45 x 40 mm at 100 mm) on a navy
              backing above the wainscot, with 'WHERE WILL YOU GO TODAY?' in
              gold Segoe UI Bold standing off the slats.
  concourse   West wall, y -3.5..3.3, face x -31.868: a living green wall,
              oak-framed, dense foliage in three greens on a dark backing.
  foyer       'Flock': 28 folded paper planes in gold and ivory hanging on
              fine cables under the baffles (2.45..3.25 m), circling the
              middle of the entrance foyer.
  arrivals    Public return south wall, x -38.3..-26.4, face y -21.868: the
              11.9 x 1.8 m 'WELCOME TO AZURE BAY' mural (mural48_blender.py) in
              a slim oak frame, material MI_AP_P48Mural.

World source coordinates, exported at the origin. Headless.
Usage: blender -b --factory-startup -P features48_blender.py -- <out_dir> <report.json>
"""
import bpy, json, math, random, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from mesh48 import Mesh, export

ARGS = sys.argv[sys.argv.index('--') + 1:]
OUT, REPORT = Path(ARGS[0]), Path(ARGS[1])
R = random.Random(4848)
MATS = dict(oak=('MI_AP_P43TOak', (.66, .46, .27)), navy=('MI_AP_P38ANavy', (.02, .05, .06)),
            gold=('MI_AP_P38AGold', (.72, .48, .11)), ivory=('MI_AP_Ivory', (.85, .82, .75)),
            leaf=('MI_AP_Leaf', (.18, .4, .2)), leaf2=('MI_AP_LightLeaf', (.35, .55, .25)),
            sage=('MI_AP_P38ASage', (.14, .27, .23)), frame=('MI_AP_P38AFrame', (.13, .18, .17)),
            backing=('MI_AP_P38ARubber', (.02, .04, .04)), mural=('MI_AP_P48Mural', (.3, .5, .5)))


def slat_wall(M, words):
    face, x0, x1, z0, z1 = -17.868, -34.5, -27.5, 1.11, 3.62
    M.box(((x0 + x1) / 2, face + .006, (z0 + z1) / 2), (x1 - x0 + .1, .012, z1 - z0), 'navy')
    n = int(round((x1 - x0) / .1))
    for i in range(n + 1):
        x = x0 + i * .1
        M.box((x, face + .012 + .02, (z0 + z1) / 2), (.045, .04, z1 - z0), 'oak')
    cu = bpy.data.curves.new('wh', 'FONT'); cu.body = 'WHERE WILL YOU GO TODAY?'
    cu.font = bpy.data.fonts.load('C:/Windows/Fonts/segoeuib.ttf', check_existing=True)
    cu.size = .34; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'; cu.extrude = .012
    o = bpy.data.objects.new('wh', cu); o.location = ((x0 + x1) / 2, face + .075, 2.55)
    o.rotation_euler = (math.pi / 2, 0, math.pi)                     # faces +y, reads toward -x
    cu.materials.append(bpy.data.materials.get(MATS['gold'][0]) or bpy.data.materials.new(MATS['gold'][0]))
    bpy.context.scene.collection.objects.link(o); words.append(o)
    # small gold standoffs behind the words
    for k in range(9):
        M.cylinder(((x0 + 0.6) + k * (x1 - x0 - 1.2) / 8, face + .06, 2.55), .012, .03, 'gold', seg=8, axis='y')


def green_wall(M):
    face, y0, y1, z0, z1 = -31.868, -3.5, 3.3, 1.15, 3.18
    M.box((face + .02, (y0 + y1) / 2, (z0 + z1) / 2), (.04, y1 - y0, z1 - z0), 'backing')
    for (cy, sy) in (((y0 + y1) / 2, y1 - y0 + .12),):
        M.box((face + .07, cy, z1 + .03), (.1, sy, .06), 'oak')
        M.box((face + .07, cy, z0 - .03), (.1, sy, .06), 'oak')
    M.box((face + .07, y0 - .03, (z0 + z1) / 2), (.1, .06, z1 - z0 + .12), 'oak')
    M.box((face + .07, y1 + .03, (z0 + z1) / 2), (.1, .06, z1 - z0 + .12), 'oak')
    # Leaves: pointed two-sided cards, dense, angled out of the wall in three greens.
    n = 0
    for _ in range(4200):
        y, z = R.uniform(y0 + .05, y1 - .05), R.uniform(z0 + .05, z1 - .05)
        L, Wd = R.uniform(.09, .16), R.uniform(.04, .07)
        tilt, roll = R.uniform(.3, 1.2), R.uniform(0, 2 * math.pi)
        d = (math.cos(roll), math.sin(roll))                 # leaf direction in the wall plane
        base = (face + .045 + R.uniform(0, .05), y, z)
        tip = (base[0] + L * math.sin(tilt), y + L * math.cos(tilt) * d[0], z + L * math.cos(tilt) * d[1])
        mid = ((base[0] + tip[0]) / 2 + .01, (y + tip[1]) / 2, (z + tip[2]) / 2)
        side = (0, -d[1] * Wd, d[0] * Wd)
        pts = [base, (mid[0], mid[1] + side[1], mid[2] + side[2]), tip, (mid[0], mid[1] - side[1], mid[2] - side[2])]
        mat = R.choice(['leaf', 'leaf', 'leaf2', 'leaf'])
        M.quad(pts, mat); M.quad(list(reversed(pts)), mat)
        n += 1
    return n


def paper_plane(M, x, y, z, yaw, s, mat):
    """Folded paper plane: two wings and a keel, nose along yaw."""
    c, sn = math.cos(yaw), math.sin(yaw)

    def P(lx, ly, lz):
        return (x + s * (lx * c - ly * sn), y + s * (lx * sn + ly * c), z + s * lz)
    nose, tail = P(.5, 0, 0), P(-.5, 0, 0)
    for side in (1, -1):
        wing = [nose, P(-.5, .32 * side, .06), tail]
        M.quad(wing if side > 0 else list(reversed(wing)), mat)
        M.quad(list(reversed(wing)) if side > 0 else wing, mat)          # both faces visible
    keel = [nose, tail, P(-.45, 0, -.12)]
    M.quad(keel, mat); M.quad(list(reversed(keel)), mat)


def flock(M):
    cx, cy = -45.9, -13.0
    n = 0
    for k in range(28):
        a = 2 * math.pi * k / 28 + R.uniform(-.08, .08)
        rr = 1.4 + 1.3 * (k % 3) / 2 + R.uniform(-.2, .2)
        x, y = cx + rr * math.cos(a) * .55, cy + rr * math.sin(a)
        z = 2.45 + .8 * ((k * 7) % 11) / 10
        yaw = a + math.pi / 2 + R.uniform(-.2, .2)
        paper_plane(M, x, y, z, yaw, R.uniform(.38, .5), 'gold' if k % 3 == 0 else 'ivory')
        M.box((x, y, (z + .02 + 3.45) / 2), (.004, .004, 3.45 - z - .02), 'frame')
        n += 1
    return n


def mural(M):
    face, x0, x1, z0, z1 = -21.868, -38.3, -26.4, 1.2, 3.0
    yf = face + .025
    M.quad_uv([(x1, yf, z0), (x0, yf, z0), (x0, yf, z1), (x1, yf, z1)], [(0, 0), (1, 0), (1, 1), (0, 1)], 'mural')
    # quad faces +y (north, into the corridor); u runs from x1 (viewer's left) to x0
    M.box(((x0 + x1) / 2, face + .015, z1 + .03), (x1 - x0 + .12, .05, .06), 'oak')
    M.box(((x0 + x1) / 2, face + .015, z0 - .03), (x1 - x0 + .12, .05, .06), 'oak')
    for x in (x0 - .03, x1 + .03):
        M.box((x, face + .015, (z0 + z1) / 2), (.06, .05, z1 - z0 + .12), 'oak')


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    OUT.mkdir(parents=True, exist_ok=True)
    M = Mesh(MATS)
    words = []
    slat_wall(M, words)
    leaves = green_wall(M)
    planes = flock(M)
    mural(M)
    obj = M.finish('SM_AP_P48Features')
    bpy.ops.object.select_all(action='DESELECT')
    for o in words:
        o.select_set(True)
    bpy.context.view_layer.objects.active = words[0]
    bpy.ops.object.convert(target='MESH')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = 'SM_AP_P48Features'; obj.data.name = obj.name
    for p in obj.data.polygons:
        p.use_smooth = False
    fbx = OUT / 'SM_AP_P48Features.fbx'
    export(obj, fbx)
    rep = dict(status='SUCCESS', asset=obj.name, fbx=str(fbx.resolve()), materials=[m.name for m in obj.data.materials],
               polygons=len(obj.data.polygons), leaves=leaves, planes=planes)
    REPORT.write_text(json.dumps(rep, indent=1), encoding='utf-8')
    print('FEATURES48', rep['polygons'], leaves, planes)


main()
