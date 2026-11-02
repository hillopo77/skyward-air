"""Pass66: loose props for the Gameplay66 physics sandbox (headless).

Everything here is a separate, light, grabbable object, placed on the
furniture built in Pass60-64. Each mesh is modelled at the origin, base centre
at (0, 0, 0), in metres. Placements are source coordinates; the editor step
(loose66_editor.py) spawns them a few centimetres above their surface,
simulating, so they settle onto whatever is really there.

  cafe        mugs and takeaway cups on the window bar and round tables,
              magazines and books on the coffee table, throw cushions on
              the library banquette
  gallery     cups on the sunset bar, a book and a mug on the coffee table
  A08         mugs on the work bar, cushions on the terrace tiers, a book
              by the armchairs, a toy plane and balls in the kids' corner
  A07         cups and a magazine on the wave-bench side tables
  concourse   a 'renovation corner' south of the departures display: toolbox, hammer, mallet, wet-floor sign
Usage: blender -b --factory-startup -P loose66_blender.py
"""
import bpy, json, math, sys, random
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'Pass48'))
from mesh48 import Mesh, export

MATS = dict(oak=('MI_AP_P43TOak', (.5, .31, .15)), walnut=('MI_AP_P27Walnut', (.25, .13, .06)),
            teal=('MI_AP_P27Teal', (.05, .3, .3)), navy=('MI_AP_P38ANavy', (.02, .05, .06)),
            steel=('MI_AP_P27Steel', (.5, .52, .54)), black=('MI_AP_P36Black', (.03, .03, .03)),
            gold=('MI_AP_P38AGold', (.72, .48, .11)), clay=('MI_AP_P36Terracotta', (.6, .3, .2)),
            cream=('MI_AP_P34Cream', (.8, .75, .6)), sage=('MI_AP_P38ASage', (.4, .5, .4)),
            leaf=('MI_AP_Leaf', (.15, .4, .15)), leaf2=('MI_AP_LightLeaf', (.3, .55, .2)),
            fabric=('MI_AP_P36Sand', (.7, .6, .45)), ink=('MI_AP_P38AText', (.9, .8, .5)))
DECK = 3.17
R = random.Random(66)


def mug(M, body):
    M.cylinder((0, 0, .048), .042, .092, body, seg=20, mat_bottom=body)
    M.cylinder((0, 0, .089), .036, .004, 'walnut', seg=20, cap_bottom=False)     # coffee
    M.box((.053, 0, .07), (.012, .014, .012), body); M.box((.053, 0, .03), (.012, .014, .012), body)
    M.box((.062, 0, .05), (.012, .014, .05), body)                              # handle


def takeaway(M):
    M.cylinder((0, 0, .06), .038, .12, 'cream', seg=20)
    M.cylinder((0, 0, .058), .0395, .045, 'fabric', seg=20, cap_top=False, cap_bottom=False)   # card sleeve
    M.cylinder((0, 0, .126), .041, .012, 'black', seg=20)                                       # lid
    M.cylinder((.018, 0, .134), .008, .006, 'black', seg=10)


def book(M, cover, w=.16, t=.032, h=.235):
    """Lying flat: w across, h along y, t thick."""
    M.box((0, 0, t / 2), (w, h, t), cover)
    M.box((.006, 0, t / 2), (w - .008, h - .01, t - .008), 'cream')            # page block (pokes out at the fore-edge)
    M.box((-w / 2 + .01, 0, t + .0005), (.006, h - .02, .001), 'gold')          # spine stripe


def magazine(M, cover):
    M.box((0, 0, .004), (.21, .28, .008), 'cream')
    M.box((0, 0, .0085), (.21, .28, .001), cover)
    M.box((0, .07, .0092), (.17, .05, .0005), 'ink')                           # masthead


def cushion(M, mat, w=.42, t=.16):
    """A square throw pillow: full in the middle, pinched to a seam at the edges, slightly pulled-in corners."""
    import bmesh
    before = set(M.bm.verts)
    res = bmesh.ops.create_cube(M.bm, size=1.0)
    edges = list({e for v in res['verts'] for e in v.link_edges})
    bmesh.ops.subdivide_edges(M.bm, edges=edges, cuts=7, use_grid_fill=True)
    verts = [v for v in M.bm.verts if v not in before]
    for v in verts:
        x, y, z = v.co.x * 2, v.co.y * 2, v.co.z * 2            # -1..1
        puff = (1 - abs(x) ** 3) * (1 - abs(y) ** 3)
        v.co.x = x * w / 2 * (1 - .14 * abs(y) ** 3)            # edges curve in toward the corners
        v.co.y = y * w / 2 * (1 - .14 * abs(x) ** 3)
        v.co.z = t / 2 + z * (t / 2) * (.12 + .88 * puff)
    for f in {f for v in verts for f in v.link_faces}:
        f.material_index = M.index[mat]
        M.solid.append(f)


def potted(M):
    M.cylinder((0, 0, .07), .085, .14, 'clay', seg=16)
    M.cylinder((0, 0, .132), .075, .01, 'walnut', seg=16, cap_bottom=False)
    for dx, dy, dz, k, m in ((0, 0, .27, 1.25, 'leaf'), (-.05, -.05, .21, .95, 'leaf2'), (.05, .05, .22, .95, 'leaf'),
                             (.02, -.04, .33, .8, 'leaf2')):
        M.blob((dx, dy, dz), .085 * k, m, squash=.85, subdiv=2)


def toy_plane(M):
    M.cylinder((0, 0, .07), .055, .46, 'cream', seg=16, axis='x')
    M.blob((.23, 0, .07), .055, 'cream', squash=1.0, subdiv=2)                 # nose
    M.box((.02, 0, .07), (.11, .56, .016), 'teal')                              # wings
    M.box((-.2, 0, .085), (.06, .2, .012), 'teal')                              # tailplane
    M.box((-.205, 0, .13), (.07, .012, .1), 'clay')                             # fin
    for y in (-.13, .13):
        M.cylinder((.04, y, .045), .018, .05, 'black', seg=10, axis='x')        # engines
    M.box((.15, 0, .1), (.06, .07, .02), 'navy')                                # cockpit


def ball(M, mat):
    M.blob((0, 0, .1), .1, mat, subdiv=3)


def toolbox(M):
    M.box((0, 0, .1), (.5, .22, .2), 'clay')
    M.box((0, 0, .203), (.5, .22, .006), 'black')                               # lid seam
    M.box((0, 0, .25), (.26, .02, .02), 'black')
    for x in (-.12, .12):
        M.box((x, 0, .225), (.02, .02, .045), 'black')
    M.box((.2, .112, .15), (.04, .006, .03), 'steel')                           # latch


def hammer(M):
    M.box((-.03, 0, .016), (.3, .028, .03), 'oak')                              # handle
    M.box((-.17, 0, .016), (.07, .032, .034), 'black')                           # grip
    M.box((.13, 0, .022), (.032, .11, .044), 'steel')                            # head
    M.box((.13, -.07, .022), (.024, .04, .02), 'steel')                          # claw


def mallet(M):
    M.box((-.04, 0, .016), (.28, .026, .028), 'oak')
    M.cylinder((.12, 0, .04), .04, .13, 'black', seg=16, axis='y')


def wet_sign(M):
    """An A-frame 'caution' sign, 0.62 m tall, legs 0.3 m apart."""
    h, half, w = .62, .15, .3
    for s in (-1, 1):
        a, b = (s * half, -w / 2, 0), (s * half, w / 2, 0)
        c, d = (s * .012, w / 2, h), (s * .012, -w / 2, h)
        f = M.quad([a, b, c, d] if s < 0 else [b, a, d, c], 'gold')
        f2 = M.quad([d, c, b, a] if s < 0 else [c, d, a, b], 'gold')
        mark = [(p[0] + s * .003, p[1], p[2]) for p in ((s * (half * .62), -.1, .2), (s * (half * .62), .1, .2),
                                                       (s * .05, .1, .4), (s * .05, -.1, .4))]
        M.quad(mark, 'black'); M.quad(mark[::-1], 'black')
    M.box((0, 0, h - .005), (.04, w + .01, .02), 'black')


PROPS = {  # asset: (builder, kg)
    'SM_AP_P66Mug': (lambda M: mug(M, 'cream'), .35), 'SM_AP_P66MugTeal': (lambda M: mug(M, 'teal'), .35),
    'SM_AP_P66TakeawayCup': (takeaway, .3),
    'SM_AP_P66BookNavy': (lambda M: book(M, 'navy'), .6), 'SM_AP_P66BookClay': (lambda M: book(M, 'clay', .15, .026, .22), .5),
    'SM_AP_P66BookSage': (lambda M: book(M, 'sage', .17, .04, .24), .7),
    'SM_AP_P66Magazine': (lambda M: magazine(M, 'teal'), .25), 'SM_AP_P66MagazineGold': (lambda M: magazine(M, 'gold'), .25),
    'SM_AP_P66Cushion': (lambda M: cushion(M, 'fabric'), .5), 'SM_AP_P66CushionGold': (lambda M: cushion(M, 'gold'), .5),
    'SM_AP_P66CushionTeal': (lambda M: cushion(M, 'teal'), .5),
    'SM_AP_P66Plant': (potted, 1.6), 'SM_AP_P66ToyPlane': (toy_plane, .8),
    'SM_AP_P66Ball': (lambda M: ball(M, 'clay'), .3), 'SM_AP_P66BallTeal': (lambda M: ball(M, 'teal'), .3),
    'SM_AP_P66Toolbox': (toolbox, 6.0), 'SM_AP_P66Hammer': (hammer, .7), 'SM_AP_P66Mallet': (mallet, .6),
    'SM_AP_P66WetSign': (wet_sign, 1.2)}


def c07(x):
    return 7.55 + .7 * math.sin(2 * math.pi * (x + 22) / 7)


def a07_tables():
    out = []
    for x, side in ((-19.3, -1), (-16.75, 1)):
        rot = math.atan2(c07(x + 1e-3) - c07(x - 1e-3), 2e-3)
        nx, ny = -math.sin(rot) * side, math.cos(rot) * side
        out.append((x + nx * 1.05, c07(x) + ny * 1.05))
    return out


def placements():
    """(asset, x, y, surface top z, yaw deg) in source coordinates."""
    P = []
    j = lambda: R.uniform(-25, 25)
    # cafe window bar (top 1.065, y 33.55, x -40.6..-34.25)
    for x, a in ((-40.0, 'SM_AP_P66TakeawayCup'), (-38.75, 'SM_AP_P66Mug'), (-37.9, 'SM_AP_P66Magazine'),
                 (-36.3, 'SM_AP_P66MugTeal'), (-34.9, 'SM_AP_P66TakeawayCup')):
        P.append((a, x, 33.5, 1.065, j()))
    # cafe round tables by the library banquette (top .755)
    P += [('SM_AP_P66Mug', -33.2, 17.6, .755, 30), ('SM_AP_P66BookClay', -33.0, 17.85, .755, 75),
          ('SM_AP_P66TakeawayCup', -33.1, 19.95, .755, 0), ('SM_AP_P66MugTeal', -33.25, 19.75, .755, 140)]
    # library banquette seat cushions (seat top ~.51): throw cushions
    P += [('SM_AP_P66CushionGold', -32.3, 18.9, .51, 0), ('SM_AP_P66Cushion', -32.3, 22.6, .51, 0),
          ('SM_AP_P66CushionTeal', -32.3, 28.2, .51, 0), ('SM_AP_P66BookNavy', -32.35, 24.0, .51, 10)]
    # cafe lounge: coffee table (-45.4, 27.3, top .42), side table (-47.75, 27.3, top .535), sofa (-43.05, 27.3)
    P += [('SM_AP_P66MagazineGold', -45.6, 27.1, .42, 20), ('SM_AP_P66BookSage', -45.0, 27.45, .42, -70),
          ('SM_AP_P66Mug', -45.85, 27.5, .42, 0), ('SM_AP_P66Plant', -47.75, 27.3, .535, 0),
          ('SM_AP_P66CushionGold', -43.0, 26.6, .55, 0), ('SM_AP_P66CushionTeal', -43.0, 28.0, .55, 0)]
    # gallery (deck 3.17): sunset bar (x -48.62, y 27.3..30.4, top +1.045), coffee table (-43.45, 28.42, top +.42)
    P += [('SM_AP_P66TakeawayCup', -48.55, 27.9, DECK + 1.045, 0), ('SM_AP_P66Mug', -48.6, 29.6, DECK + 1.045, 50),
          ('SM_AP_P66BookNavy', -43.6, 28.2, DECK + .42, 15), ('SM_AP_P66MugTeal', -43.2, 28.7, DECK + .42, 0)]
    # A08: work bar (x -24.42, y 21..29.6, top 1.065)
    P += [('SM_AP_P66Mug', -24.45, 22.4, 1.065, 0), ('SM_AP_P66TakeawayCup', -24.4, 24.9, 1.065, 0),
          ('SM_AP_P66Magazine', -24.45, 26.4, 1.065, 85), ('SM_AP_P66MugTeal', -24.4, 28.3, 1.065, 0)]
    # A08 terrace tiers: cushions (tier fronts x -29.15 / -30.05 / -30.95, tops .45 / .90 / 1.35 + pads)
    # (in the gaps between the seated passengers: tier 0 has people at y 23.4/24.3/27.5/29.9, tier 1 at 25.6/28.7/30.6)
    P += [('SM_AP_P66CushionTeal', -29.75, 26.1, .62, 0), ('SM_AP_P66CushionGold', -29.75, 31.0, .62, 0),
          ('SM_AP_P66Cushion', -30.65, 27.2, 1.07, 0), ('SM_AP_P66CushionGold', -31.55, 28.9, 1.52, 0),
          ('SM_AP_P66BookClay', -29.6, 28.7, .62, 30)]
    # A08 armchair corner side table (-27.4, 30.6, top .535) and the kids' corner (-26.4, 32.85)
    P += [('SM_AP_P66BookSage', -27.4, 30.6, .535, 40), ('SM_AP_P66ToyPlane', -26.9, 32.6, .02, 200),
          ('SM_AP_P66Ball', -25.8, 33.1, .02, 0), ('SM_AP_P66BallTeal', -26.2, 32.2, .02, 0)]
    # A07 wave-bench side tables (top .535)
    (ta, tb) = a07_tables()
    P += [('SM_AP_P66TakeawayCup', ta[0] + .08, ta[1], .535, 0), ('SM_AP_P66Magazine', ta[0] - .06, ta[1] + .04, .535, 25),
          ('SM_AP_P66Mug', tb[0], tb[1] - .05, .535, 0), ('SM_AP_P66Plant', tb[0] + .02, tb[1] + .12, .535, 0)]
    # concourse 'renovation corner' by the departures display (east wall x -26.14, y 11.9)
    P += [('SM_AP_P66Toolbox', -26.75, 6.4, 0, 90), ('SM_AP_P66Hammer', -26.95, 7.05, 0, 35),
          ('SM_AP_P66Mallet', -26.6, 7.3, 0, 160), ('SM_AP_P66WetSign', -27.6, 5.6, 0, 20)]
    return P


def main():
    out = HERE / 'Loose66Build'; out.mkdir(exist_ok=True)
    items = []
    for name, (fn, kg) in PROPS.items():
        probe = Mesh(MATS); fn(probe)                                   # which slots does this prop use?
        used = {f.material_index for f in probe.bm.faces}; probe.bm.free()
        M = Mesh({k: v for i, (k, v) in enumerate(MATS.items()) if i in used})
        fn(M)
        obj = M.finish(name)
        fbx = out / (name + '.fbx')
        export(obj, fbx)
        items.append(dict(asset=name, fbx=str(fbx.resolve()), materials=[m.name for m in obj.data.materials], kg=kg,
                          polygons=len(obj.data.polygons), dims=[round(v, 3) for v in obj.dimensions]))
        bpy.data.objects.remove(obj)
    rep = dict(status='SUCCESS', items=items, placements=[[a, round(x, 3), round(y, 3), round(z, 3), round(yaw, 1)]
                                                           for a, x, y, z, yaw in placements()])
    (HERE / 'Loose66Build.json').write_text(json.dumps(rep, indent=1), encoding='utf-8')
    print('LOOSE66', len(items), len(rep['placements']))


main()
