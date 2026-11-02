"""Pass60: Cloud Nine cafe redesign (headless).

The cafe is a 17 x 18 m, 6.8 m glass box (x -49..-32, y 16..34): west and north
walls glazed 1.0-6.7 m, a gallery deck in the north-west corner (x -49..-41,
y 25..34, underside 2.87 m) over the service counters, and a 2.4 m stair along
the west glass (x -47.7..-45.3). The sun comes in through the west glass.

  SM_AP_P60Cafe       furniture and fit-out, complex collision
    lounge            (Pass62) under the gallery beside the stair (x -48.8..-42.3,
                      y 25.4..29.3, 2.87 m deck ceiling): a rug, a rounded sofa
                      facing the west glass, two armchairs facing it, a coffee
                      table, two floor lamps; trees in planters against the
                      glass beside the stair. The stair foot stays clear.
    library wall      the east wall (x -32): teal banquettes on oak plinths with
                      tall oak shelving above (books, plants, a warm light strip
                      under every shelf)
    window bar        an oak counter along the north glass with high stools
    counter           'CLOUD NINE' on the gallery front, three hanging menu
                      boards over the counters, six downlights in the deck
                      underside (their lights in Bake55.json 'canopy_lights')
  SM_AP_P60CafeFloor  oak plank floor over the dining area (no collision)
Seated passengers, their chairs and tables, the barista, the coffee cart, the
cup and luggage pickups and the safety station are not moved.
World source metres. Usage: blender -b --factory-startup -P cafe60_blender.py
"""
import bpy, json, math, random, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'Pass48'))
from mesh48 import Mesh, export

MATS = dict(oak=('MI_AP_P43TOak', (.5, .31, .15)), walnut=('MI_AP_P27Walnut', (.25, .13, .06)),
            teal=('MI_AP_P27Teal', (.05, .3, .3)), navy=('MI_AP_P38ANavy', (.02, .05, .06)),
            steel=('MI_AP_P27Steel', (.5, .52, .54)), black=('MI_AP_P36Black', (.03, .03, .03)),
            gold=('MI_AP_P38AGold', (.72, .48, .11)), glow=('MI_AP_P51SignGlow', (1, .88, .66)),
            shade=('MI_AP_P51Soffit', (1, .84, .62)), rug=('MI_AP_P34Carpet', (.2, .25, .3)),
            clay=('MI_AP_P36Terracotta', (.6, .3, .2)), cream=('MI_AP_P34Cream', (.8, .75, .6)),
            sage=('MI_AP_P38ASage', (.4, .5, .4)), leaf=('MI_AP_Leaf', (.15, .4, .15)),
            leaf2=('MI_AP_LightLeaf', (.3, .55, .2)), fabric=('MI_AP_P36Sand', (.7, .6, .45)),
            ink=('MI_AP_P38AText', (.9, .8, .5)))
FLOOR_MATS = dict(plank=('MI_AP_P43TOak', (.6, .42, .25)), edge=('MI_AP_P27Walnut', (.25, .13, .06)))   # Pass62: honey oak, walnut edge
FONT = 'C:/Windows/Fonts/segoeuib.ttf'
R = random.Random(60)
WORDS = []
SOFT = None
SOFT_MATS = dict(fabric=('MI_AP_P36Sand', (.7, .6, .45)), cushion=('MI_AP_P34Cream', (.8, .75, .6)),
                 accent=('MI_AP_P27Teal', (.05, .3, .3)), teal=('MI_AP_P27Teal', (.05, .3, .3)))


def text(body, at, yaw, size, mat='glow', depth=.004):
    """Raised lettering standing on a vertical face; yaw = direction the text faces."""
    cu = bpy.data.curves.new('t', 'FONT'); cu.body = body
    cu.font = bpy.data.fonts.load(FONT, check_existing=True)
    cu.size = size; cu.resolution_u = 4; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'; cu.extrude = depth
    o = bpy.data.objects.new('t', cu)
    o.location = (at[0] + math.cos(yaw) * depth, at[1] + math.sin(yaw) * depth, at[2])
    o.rotation_euler = (math.pi / 2, 0, yaw + math.pi / 2)
    cu.materials.append(bpy.data.materials.get(MATS[mat][0]) or bpy.data.materials.new(MATS[mat][0]))
    bpy.context.scene.collection.objects.link(o); WORDS.append(o)


def armchair(M, x, y, yaw):
    """Lounge armchair facing yaw: rounded shell (soft mesh), loose seat and back
    cushions, tapered walnut legs."""
    c, s = math.cos(yaw), math.sin(yaw)
    def P(f, sd, z):                                # forward, side offsets
        return (x + c * f - s * sd, y + s * f + c * sd, z)
    for f in (-.28, .28):                           # legs on the frame (main mesh)
        for sd in (-.33, .33):
            M.cylinder(P(f, sd, .07), .024, .14, 'walnut', seg=12)
    S = SOFT
    S.box(P(0, 0, .25), (.82, .84, .16), 'fabric', rot=yaw)            # base
    S.box(P(-.36, 0, .58), (.16, .84, .58), 'fabric', rot=yaw)         # back shell
    for sd in (-.37, .37):
        S.box(P(.02, sd, .47), (.78, .12, .36), 'fabric', rot=yaw)     # arms
    S.box(P(.06, 0, .38), (.66, .62, .14), 'cushion', rot=yaw)         # seat cushion
    S.box(P(-.22, 0, .66), (.14, .6, .46), 'cushion', rot=yaw)         # back cushion
    S.box(P(-.12, .18, .52), (.1, .3, .26), 'accent', rot=yaw)         # scatter cushion


def side_table(M, x, y):
    M.cylinder((x, y, .52), .26, .03, 'walnut', seg=24)
    M.cylinder((x, y, .26), .03, .5, 'black', seg=10)
    M.cylinder((x, y, .01), .18, .02, 'black', seg=20)


def floor_lamp(M, x, y):
    M.cylinder((x, y, .015), .17, .03, 'black', seg=20)
    M.cylinder((x, y, .78), .015, 1.5, 'gold', seg=10)
    M.cylinder((x, y, 1.62), .22, .3, 'shade', seg=28)                # glowing linen drum


def planter(M, x, y, r=.55, h=.62):
    M.cylinder((x, y, h / 2), r, h, 'clay', seg=32)
    M.cylinder((x, y, h - .02), r - .04, .02, 'black', seg=32, cap_bottom=False)


def sofa(M, x, y, yaw, length=2.0):
    """Rounded three-seat sofa facing yaw (upholstery in the soft mesh)."""
    c, s = math.cos(yaw), math.sin(yaw)
    def P(f, sd, z):
        return (x + c * f - s * sd, y + s * f + c * sd, z)
    for f in (-.3, .3):
        for sd in (-length / 2 + .1, length / 2 - .1):
            M.cylinder(P(f, sd, .07), .024, .14, 'walnut', seg=12)
    S = SOFT
    S.box(P(0, 0, .25), (.86, length, .16), 'fabric', rot=yaw)
    S.box(P(-.38, 0, .6), (.16, length, .6), 'fabric', rot=yaw)
    for sd in (-length / 2 + .06, length / 2 - .06):
        S.box(P(.02, sd, .47), (.82, .12, .36), 'fabric', rot=yaw)
    n = 3
    for k in range(n):
        sd = -length / 2 + .12 + (length - .24) * (k + .5) / n
        S.box(P(.06, sd, .38), (.68, (length - .24) / n - .03, .14), 'cushion', rot=yaw)
        S.box(P(-.24, sd, .68), (.14, (length - .24) / n - .03, .46), 'cushion', rot=yaw)
    S.box(P(-.12, -length / 2 + .35, .52), (.1, .32, .28), 'accent', rot=yaw)


def coffee_table(M, x, y, w=1.1, d=.62):
    M.box((x, y, .4), (w, d, .04), 'walnut')
    M.box((x, y, .2), (w - .1, d - .1, .03), 'walnut')                 # lower shelf
    for dx in (-w / 2 + .06, w / 2 - .06):
        for dy in (-d / 2 + .06, d / 2 - .06):
            M.box((x + dx, y + dy, .2), (.04, .04, .4), 'black')


def lounge(M):
    """Pass62: the lounge moves under the gallery, beside the stair, where the
    deck makes a low, cosy ceiling. The stair foot and its approach stay clear,
    and the counter keeps a 1.6 m queue strip in front of it."""
    x0, x1, y0, y1 = -48.75, -42.3, 25.35, 29.25
    M.box(((x0 + x1) / 2, (y0 + y1) / 2, .006), (x1 - x0, y1 - y0, .012), 'rug')
    sofa(M, -43.05, 27.3, math.pi)                     # faces the west glass
    armchair(M, -47.75, 26.55, 0.0)                    # two armchairs face it, backs to the glass
    armchair(M, -47.75, 28.05, 0.0)
    coffee_table(M, -45.4, 27.3)
    side_table(M, -47.75, 27.3)
    floor_lamp(M, -48.45, 25.7); floor_lamp(M, -42.65, 28.95)
    planter(M, -48.35, 16.85, .48, .6); planter(M, -48.35, 19.9, .48, .6)   # beside the stair, against the glass
    return [(-48.35, 16.85), (-48.35, 19.9)]


def library_wall(M):
    xw = -32.08                                       # east wall inner face
    for y0, y1 in ((16.6, 24.9), (26.5, 31.3)):
        L, yc = y1 - y0, (y0 + y1) / 2
        M.box((xw - .32, yc, .2), (.6, L, .4), 'oak')                     # plinth
        n_c = max(1, round(L / 1.2))                                      # separate seat and back cushions
        for k in range(n_c):
            cy = y0 + L * (k + .5) / n_c
            SOFT.box((xw - .32, cy, .45), (.6, L / n_c - .03, .12), 'teal')
            SOFT.box((xw - .1, cy, .82), (.16, L / n_c - .03, .6), 'teal')
        # shelving above the back cushion
        z0, z1, d = 1.3, 3.75, .32                                       # tops stay under the wave slats
        M.box((xw - d / 2, yc, z1 + .03), (d, L + .06, .06), 'oak')
        for yy in [y0 + k * (L / max(1, round(L / 1.4))) for k in range(int(round(L / 1.4)) + 1)]:
            M.box((xw - d / 2, yy, (z0 + z1) / 2), (d, .04, z1 - z0), 'oak')   # uprights
        n = 5
        for k in range(n):
            z = z0 + k * (z1 - z0) / (n - 1)
            M.box((xw - d / 2, yc, z), (d, L, .035), 'oak')
            M.box((xw - d + .03, yc, z - .025), (.02, L - .1, .012), 'glow')   # warm strip under the shelf
            if k == n - 1:
                continue
            yy = y0 + .1
            while yy < y1 - .25:                                          # books and plants
                if R.random() < .16:
                    pr = R.uniform(.09, .12)
                    M.cylinder((xw - .16, yy + pr, z + .08), pr, .14, 'clay', seg=14)
                    for dx, dy, dz, k in ((0, 0, .26, 1.3), (-.05, -.06, .21, 1.0), (.04, .07, .22, 1.0), (0, .02, .33, .9)):
                        M.blob((xw - .16 + dx, yy + pr + dy, z + dz), pr * k, R.choice(['leaf', 'leaf2']), squash=.85, subdiv=2)
                    yy += pr * 2 + .08
                else:
                    w = R.uniform(.03, .06); h = R.uniform(.26, .5)
                    M.box((xw - .17, yy + w / 2, z + h / 2 + .02), (.22, w, h),
                          R.choice(['navy', 'teal', 'clay', 'cream', 'sage', 'gold', 'walnut']))
                    yy += w + .004
    # small round tables in front of the south banquette
    for y in (17.7, 19.9):
        M.cylinder((xw - 1.05, y, .74), .33, .03, 'walnut', seg=24)
        M.cylinder((xw - 1.05, y, .37), .03, .72, 'black', seg=10)
        M.cylinder((xw - 1.05, y, .01), .22, .02, 'black', seg=20)


def window_bar(M):
    y, x0, x1 = 33.55, -40.6, -34.25
    M.box(((x0 + x1) / 2, y, 1.04), (x1 - x0, .5, .05), 'oak')
    for x in (x0 + .1, (x0 + x1) / 2, x1 - .1):
        M.box((x, y + .05, .52), (.06, .3, 1.0), 'black')
    M.box(((x0 + x1) / 2, y + .1, .22), (x1 - x0, .03, .03), 'steel')        # foot rail
    n = 7
    for k in range(n):
        x = x0 + (x1 - x0) * (k + .5) / n
        M.cylinder((x, y - .55, .76), .2, .05, 'oak', seg=20)               # stool seat
        M.cylinder((x, y - .55, .38), .025, .72, 'black', seg=10)
        M.cylinder((x, y - .55, .3), .16, .015, 'steel', seg=16, cap_top=False, cap_bottom=False)
        M.cylinder((x, y - .55, .01), .2, .02, 'black', seg=20)


def counter(M):
    # 'CLOUD NINE' on the gallery front (fascia y 25.0, z 2.87-3.17)
    M.box((-46.2, 24.97, 3.02), (4.6, .04, .28), 'navy')
    text('CLOUD NINE  ·  COFFEE & BAKERY', (-46.2, 24.95, 3.02), -math.pi / 2, .17)
    # three menu boards hung from the deck underside, facing the queue (south)
    for x, title in ((-47.2, 'COFFEE'), (-44.9, 'BAKERY'), (-42.6, 'TEA')):
        M.box((x, 30.2, 2.42), (1.8, .05, .62), 'black')
        M.box((x, 30.2, 2.42 + .33), (1.84, .07, .03), 'oak')
        for dx in (-.7, .7):
            M.box((x + dx, 30.2, 2.8), (.012, .012, .14), 'steel')
        text(title, (x, 30.17, 2.6), -math.pi / 2, .12, 'ink')
        for k in range(4):
            M.box((x - .2, 30.17, 2.47 - k * .1), (1.1, .006, .025), 'cream')
            M.box((x + .72, 30.17, 2.47 - k * .1), (.16, .006, .025), 'gold')
    # downlights in the deck underside
    for x in (-47.3, -44.9, -42.5):
        for y in (27.6, 30.9):
            M.cylinder((x, y, 2.865), .1, .01, 'shade', seg=18)
            M.cylinder((x, y, 2.868), .13, .006, 'steel', seg=18, cap_bottom=False)


def floor():
    F = Mesh(FLOOR_MATS)
    x0, x1, y0, y1 = -41.0, -32.1, 16.1, 33.9
    F.box(((x0 + x1) / 2, (y0 + y1) / 2, .006), (x1 - x0, y1 - y0, .012), 'plank')
    for xx in (x0, x1):                                        # oak edge strips
        F.box((xx, (y0 + y1) / 2, .007), (.06, y1 - y0, .014), 'edge')
    for yy in (y0, y1):
        F.box(((x0 + x1) / 2, yy, .007), (x1 - x0, .06, .014), 'edge')
    return F


def finish(M, name, out, words):
    obj = M.finish(name)
    if words:
        bpy.ops.object.select_all(action='DESELECT')
        for o in words: o.select_set(True)
        bpy.context.view_layer.objects.active = words[0]
        bpy.ops.object.convert(target='MESH')
        for o in words + [obj]: o.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.join()
        obj = bpy.context.view_layer.objects.active
        obj.name = obj.data.name = name
    fbx = out / (name + '.fbx')
    export(obj, fbx)
    return dict(status='SUCCESS', asset=name, fbx=str(fbx.resolve()), materials=[m.name for m in obj.data.materials],
                polygons=len(obj.data.polygons))


def main():
    out = HERE / 'CafeBuild'; out.mkdir(exist_ok=True)
    global SOFT
    bpy.ops.wm.read_factory_settings(use_empty=True)
    M = Mesh(MATS)
    SOFT = Mesh(SOFT_MATS)                          # upholstery: built apart, rounded far more
    trees = lounge(M); library_wall(M); window_bar(M); counter(M)
    rep = finish(M, 'SM_AP_P60Cafe', out, WORDS)
    import mesh48
    w0, s0 = mesh48.SOFT_WIDTH, mesh48.SOFT_SEGMENTS
    mesh48.SOFT_WIDTH, mesh48.SOFT_SEGMENTS = .045, 4
    rep3 = finish(SOFT, 'SM_AP_P60CafeSoft', out, [])
    mesh48.SOFT_WIDTH, mesh48.SOFT_SEGMENTS = w0, s0
    (HERE / 'Cafe60SoftBuild.json').write_text(json.dumps(rep3, indent=1), encoding='utf-8')
    rep['trees'] = trees
    (HERE / 'Cafe60Build.json').write_text(json.dumps(rep, indent=1), encoding='utf-8')
    for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
    rep2 = finish(floor(), 'SM_AP_P60CafeFloor', out, [])
    (HERE / 'Cafe60FloorBuild.json').write_text(json.dumps(rep2, indent=1), encoding='utf-8')
    print('CAFE60', rep['polygons'], rep2['polygons'])


main()
