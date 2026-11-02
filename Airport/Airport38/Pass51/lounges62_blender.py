"""Pass62: the gate lounges A07 and A08, redesigned (headless).

Both are 6.4 m halls with clerestories. Their benches stay where they are
(the seated passengers are fitted to them), and so do the gate desks, boarding
door, bridge control, luggage pickups, safety stations and every walking route;
everything else is replaced. Builds, from the cafe's furniture vocabulary
(cafe60_blender.py):

  SM_AP_P62Lounges      hard furniture and feature walls, complex collision
  SM_AP_P62LoungeSoft   upholstery, rounded at 4.5 cm, complex collision
  SM_AP_P62LoungeFloor  rugs and oak floor zones, no collision

  A08 'North Coast'  (x -31.9..-24.1, y 14.1..33.9)
    gate wall    oak slat wall behind the desk with 'A08' in 1 m gold numerals
                 and 'NORTH COAST' under them
    rug          one big sage rug under the west and north bench groups
    green island a long oak planter with low greenery and cushioned seat edges,
                 between the benches, clear of the luggage pickup
    work bar     an oak counter with power and six stools along the east wall,
                 under the flight display
    corner       two armchairs and a side table in the north-east corner
  A07 'Azure Bay'  (x -22.9..-14.1, y -2.9..9.9)
    sign         'A07' in gold and 'AZURE BAY' on the plaster band above the
                 north glass, which stays clear: it looks onto the apron
    rug          a sage rug under both benches
    window seats two armchairs and a side table facing the glass and the
                 aircraft; side tables with power at the bench ends
    The boarding route (y 0.6..4.5) and the desk stay clear.
  Gallery (Pass63, deck x -49..-41, y 25..34 at 3.17 m) 'SM_AP_P63Gallery*':
    an open sunset bar with stools along the west glass, a screen of planted
    trees along the north glass behind the bench, a conversation group
    facing the east bench, a rug, lamps; the benches, travel shop and stair landing stay as they are
Trees in terracotta planters are placed separately (ImportJobs48 'actors').
World source metres. Usage: blender -b --factory-startup -P lounges62_blender.py
"""
import bpy, json, math, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'Pass48'))
import mesh48
from mesh48 import Mesh, export

exec(compile(open(HERE / 'cafe60_blender.py', encoding='utf-8').read().split('\ndef main():')[0], 'cafe60', 'exec'))
FLOOR_MATS2 = dict(mat=('MI_AP_P27Teal', (.05, .3, .3)), rug=('MI_AP_P38ASage', (.4, .5, .4)), plank=('MI_AP_P27Oak', (.55, .35, .18)),
                   edge=('MI_AP_P43TOak', (.5, .31, .15)))
TREES = []


def slat_wall(M, x0, x1, y0, y1, z0, z1, facing, pitch=.12, w=.05):
    """Vertical oak slats on a dark backing, on a wall; facing = inward normal (dx, dy)."""
    fx, fy = facing
    along_x = fx == 0
    L = (x1 - x0) if along_x else (y1 - y0)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    # Pass70: the backing sat exactly on the wall plane and z-fought the room's cream band (the A08 sign 'jitter');
    # now a thin sheet 1.2-1.8 cm proud of the wall, just behind the slats
    bx, by = (cx, cy + fy * .015) if along_x else (cx + fx * .015, cy)
    M.box((bx, by, (z0 + z1) / 2), ((L, .006, z1 - z0) if along_x else (.006, L, z1 - z0)), 'black')
    n = int(L / pitch)
    for k in range(n + 1):
        t = -L / 2 + k * L / n
        px, py = (cx + t, cy + fy * .03) if along_x else (cx + fx * .03, cy + t)
        M.box((px, py, (z0 + z1) / 2), ((w, .04, z1 - z0) if along_x else (.04, w, z1 - z0)), 'oak')


def gate_sign(at, facing, code, place):
    yaw = math.atan2(facing[1], facing[0])
    text(code, (at[0], at[1], at[2]), yaw, 1.0, 'gold', depth=.06)
    text(place, (at[0], at[1], at[2] - .75), yaw, .22, 'glow', depth=.01)


def rug(F, x0, x1, y0, y1):
    F.box(((x0 + x1) / 2, (y0 + y1) / 2, .006), (x1 - x0, y1 - y0, .012), 'rug')


SEATS = {}          # Pass64: passenger -> [x, y, z, rotation_degrees, seat label]


def facing_deg(fx, fy):
    """Layout rotation_degrees for a passenger facing (fx, fy) (layout: facing = (sin r, -cos r))."""
    return round(math.degrees(math.atan2(fx, -fy)), 1)


def a08(M, F):
    """A08 'The Viewing Terrace'. A long hall whose whole east side is glass onto
    the apron, so the seating faces the aircraft: a three-tier oak terrace along
    the west wall (seat tops .45 / .90 / 1.35 m), teal cushions, a warm light
    under every nosing, steps at the north end; the window bar runs along the
    glass; a kids' corner with a timber play-plane in the north-east."""
    slat_wall(M, -31.85, -31.85, 17.6, 22.4, .9, 4.6, (1, 0))
    gate_sign((-31.79, 20.0, 3.6), (1, 0), 'A08', 'NORTH COAST  ·  10:55')
    xw, y0, y1 = -31.85, 22.5, 31.3
    L, yc = y1 - y0, (y0 + y1) / 2
    plant_slots = {1: [(22.5, 23.15)], 2: [(22.5, 23.15), (26.6, 27.6)]}   # tier -> planter spans (y)
    for k, top in enumerate((.45, .90, 1.35)):
        xf = -29.15 - k * .9                                           # front edge of tier k
        M.box((xf - .45, yc, top / 2), (.9, L, top), 'oak')
        M.box((xf + .006, yc, top - .045), (.035, L, .02), 'glow')     # light strip under the nosing (Pass70: 2.5 cm proud -
                                                                       # flush with the tier front it z-fought and jittered)
        spans, ya = [], y0 + .05
        for a, b in plant_slots.get(k, []) + [(y1 - .05, y1)]:
            if b > ya:
                spans.append((ya, a))
            ya = b
        for a, b in spans:                                             # cushion pads, ~2 m, with gaps
            n = max(1, round((b - a) / 2.0))
            for i in range(n):
                pa = a + (b - a) * i / n + .06
                pb = a + (b - a) * (i + 1) / n - .06
                SOFT.box((xf - .33, (pa + pb) / 2, top + .05), (.58, pb - pa, .1), 'teal')
                if k < 2:                                              # lean cushion against the riser behind
                    SOFT.box((xf - .8, (pa + pb) / 2, top + .26), (.13, pb - pa, .36), 'cushion')
                if i % 2 == 0 and pb - pa > 1.2:
                    SOFT.box((xf - .74, pa + .45, top + .3), (.1, .32, .28), 'accent')
        for a, b in plant_slots.get(k, []):                            # planter boxes built into the tier
            yy = (a + b) / 2
            M.box((xf - .45, yy, top + .2), (.86, b - a, .4), 'oak')
            M.box((xf - .45, yy, top + .405), (.76, b - a - .1, .02), 'black')
            for dx, dy, r, m in ((-.2, -.15, .24, 'leaf'), (.18, .12, .22, 'leaf2'), (0, 0, .3, 'leaf'), (-.12, .2, .18, 'leaf2'), (.2, -.2, .17, 'leaf')):
                M.blob((xf - .45 + dx, yy + dy * (b - a) / .65, top + .5 + r * .6), r, m, squash=.85, subdiv=2)
    SOFT.box((xw + .16, yc, 1.35 + .35), (.16, L - .1, .5), 'teal')    # back cushion against the wall
    slat_wall(M, -31.83, -31.83, y0, y1, 1.42, 3.12, (1, 0))           # oak slats behind the terrace
    # 'North Coast' artwork above the datum
    xa, za0, za1, ya0, ya1 = -31.8, 3.5, 4.85, 23.2, 30.6
    M.box((xa - .02, (ya0 + ya1) / 2, (za0 + za1) / 2), (.05, ya1 - ya0 + .12, za1 - za0 + .12), 'oak')
    M.box((xa + .01, (ya0 + ya1) / 2, (za0 + za1) / 2), (.01, ya1 - ya0, za1 - za0), 'cream')      # sky

    def band(mat, z_of, dx):
        """A filled band on the artwork: from the bottom edge up to z_of(y) (a wavy top)."""
        n = 48
        pts = [(xa + dx, ya0 + (ya1 - ya0) * i / n, za0 + .02) for i in range(n + 1)]
        top = [(xa + dx, ya0 + (ya1 - ya0) * i / n, min(za1 - .02, z_of(ya0 + (ya1 - ya0) * i / n))) for i in range(n + 1)]
        for i in range(n):
            q = [pts[i], pts[i + 1], top[i + 1], top[i]]
            M.quad(q, mat); M.quad(list(reversed(q)), mat)
    band('sage', lambda y: 4.05 + .32 * math.sin((y - ya0) * .55) + .12 * math.sin((y - ya0) * 1.7), .02)   # far hills
    band('fabric', lambda y: 3.85 + .1 * math.sin((y - ya0) * .9 + 1.0), .03)                              # dunes
    band('teal', lambda y: 3.72 + .03 * math.sin((y - ya0) * 3.0), .04)                                    # shallows
    band('navy', lambda y: 3.62 + .02 * math.sin((y - ya0) * 4.0 + .5), .05)                               # sea
    M.cylinder((xa + .06, 28.9, 4.45), .26, .02, 'gold', seg=32, axis='x')                               # sun
    text('NORTH  COAST', (xa + .07, 25.2, 4.55), 0.0, .3, 'navy')
    for k in range(6):                                                 # steps up the north end
        h = .225 * (k + 1)
        M.box((-29.15 - .45 * k - .225, y1 + .4, h / 2), (.45, .8, h), 'oak')
    rows = [('CH12 Waiting passenger 6', 1, 23.4), ('CH12 Additional waiting passenger 0', 1, 24.3),
            ('CH12 Additional waiting passenger 1', 1, 27.5), ('CH12 Additional waiting passenger 3', 1, 29.9),
            ('CH12 Additional waiting passenger 4', 2, 25.6), ('CH12 Additional waiting passenger 5', 2, 28.7),
            ('CH12 Additional waiting passenger 2', 2, 30.6)]
    for actor, tier, y in rows:
        x = -29.15 - (tier - 1) * .9 - .38
        SEATS[actor] = [round(x, 2), y, round((tier - 1) * .45, 2), facing_deg(1, 0), 'A08 viewing terrace tier %d' % tier]
    yb0, yb1 = 21.0, 29.6                                              # window bar along the apron glass
    M.box((-24.42, (yb0 + yb1) / 2, 1.04), (.56, yb1 - yb0, .05), 'oak')
    for y in (yb0 + .1, (yb0 + yb1) / 2, yb1 - .1):
        M.box((-24.25, y, .52), (.06, .3, 1.0), 'black')
    for k in range(4):
        M.box((-24.32, yb0 + .5 + k * (yb1 - yb0 - 1) / 3, 1.09), (.08, .12, .05), 'steel')
    for k in range(10):
        y = yb0 + (yb1 - yb0) * (k + .5) / 10
        M.cylinder((-24.95, y, .76), .2, .05, 'oak', seg=20)
        M.cylinder((-24.95, y, .38), .025, .72, 'black', seg=10)
        M.cylinder((-24.95, y, .01), .2, .02, 'black', seg=20)
    F.box((-26.4, 32.85, .01), (3.9, 1.9, .02), 'mat')                 # kids' corner
    # Pass70: the kit's play-plane (a plain cylinder with flat oak wings: 'the big green cylinder') is gone;
    # props70 puts a proper play plane (SM_AP_P70PlayPlane) on the mat as its own actor
    armchair(M, -25.0, 30.55, math.pi / 2)                            # parents watch the kids
    armchair(M, -26.3, 30.55, math.pi / 2)
    side_table(M, -27.4, 30.6)
    TREES.extend([(-31.15, 33.2, .58, .4)])
    planter(M, -31.15, 33.2, .48, .58)


def loft(M, pts, profile, mat, cap=True):
    """Sweep a closed 2-D profile [(n, z), ...] along a polyline pts [(x, y), ...]
    (n = offset along the horizontal normal). Smooth, continuous surfaces."""
    import math as _m
    rings = []
    for i, (x, y) in enumerate(pts):
        a = pts[max(i - 1, 0)]; b = pts[min(i + 1, len(pts) - 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]; L = _m.hypot(tx, ty) or 1
        nx, ny = -ty / L, tx / L
        rings.append([(x + nx * n, y + ny * n, z) for n, z in profile])
    k = len(profile)
    for i in range(len(rings) - 1):
        r0, r1 = rings[i], rings[i + 1]
        for j in range(k):
            jj = (j + 1) % k
            M.quad([r0[j], r0[jj], r1[jj], r1[j]], mat)
    if cap:
        M.quad(list(reversed(rings[0])), mat); M.quad(list(rings[-1]), mat)


def rounded(n0, n1, z0, z1, r, seg=4):
    """Rounded-rectangle profile, counter-clockwise in (n, z)."""
    import math as _m
    out = []
    for cn, cz, a0 in ((n1 - r, z0 + r, -90), (n1 - r, z1 - r, 0), (n0 + r, z1 - r, 90), (n0 + r, z0 + r, 180)):
        for t in range(seg + 1):
            a = _m.radians(a0 + 90 * t / seg)
            out.append((cn + r * _m.cos(a), cz + r * _m.sin(a)))
    return out


def a07(M, F):
    """A07 'The Wave'. One sinuous oak bench curving through the room like the
    wave ceiling: seats both sides of an upholstered spine, the north side
    facing the apron window and the aircraft, the south side the gate. The
    boarding route (y 0.6..4.5) and the desk stay clear; the window stays open."""
    gate_sign((-18.5, 9.8, 4.05), (0, -1), 'A07', 'AZURE BAY  ·  BOARDING')
    rug(F, -22.5, -14.6, 5.4, 9.7)

    def c(x):
        return 7.55 + .7 * math.sin(2 * math.pi * (x + 22.0) / 7.0)
    x0, x1, n = -21.7, -15.3, 64
    pts = [(x0 + (x1 - x0) * k / n, c(x0 + (x1 - x0) * k / n)) for k in range(n + 1)]
    loft(M, pts, rounded(-.55, .55, 0, .4, .06), 'oak')                  # plinth
    loft(M, pts, rounded(-.09, .09, .4, 1.02, .08), 'oak')               # spine
    for side in (1, -1):
        lo, hi = (.1, .56) if side > 0 else (-.56, -.1)
        loft(SOFT, pts, rounded(lo, hi, .4, .52, .05), 'teal')            # seat cushion
        bl, bh = (.09, .2) if side > 0 else (-.2, -.09)
        loft(SOFT, pts, rounded(bl, bh, .55, .98, .05), 'cushion')       # back cushion
    for (xe, ye) in (pts[0], pts[-1]):                                    # rounded ends
        M.cylinder((xe, ye, .2), .55, .4, 'oak', seg=28)
        SOFT.cylinder((xe, ye, .46), .5, .12, 'teal', seg=28)
    names = ['CH12 Waiting passenger 0', 'CH12 Waiting passenger 1', 'CH12 Waiting passenger 2',
             'CH12 Waiting passenger 3', 'CH12 Waiting passenger 4', 'CH12 Waiting passenger 5']
    spots = [(-20.9, 1), (-18.6, 1), (-16.2, 1), (-20.0, -1), (-17.5, -1), (-15.9, -1)]
    for name, (x, side) in zip(names, spots):
        rot = math.atan2(c(x + 1e-3) - c(x - 1e-3), 2e-3)
        nx, ny = -math.sin(rot) * side, math.cos(rot) * side
        SEATS[name] = [round(x + nx * .36, 2), round(c(x) + ny * .36, 2), 0.0, facing_deg(nx, ny), 'A07 wave bench']
    for x, side in ((-19.3, -1), (-16.75, 1)):                         # small tables in the curve's bays
        rot = math.atan2(c(x + 1e-3) - c(x - 1e-3), 2e-3)
        nx, ny = -math.sin(rot) * side, math.cos(rot) * side
        side_table(M, x + nx * 1.05, c(x) + ny * 1.05)
    floor_lamp(M, -22.45, 5.6)
    TREES.extend([(-22.35, 9.35, .58, .4), (-14.75, 9.35, .58, .4)])
    planter(M, -22.35, 9.35, .45, .58); planter(M, -14.75, 9.35, .45, .58)


def concourse(M):
    """Departures display on the concourse east wall (face x -26.13), facing the
    concourse, where the information totem stood. A navy screen in a slim oak
    frame, gold header, the two departures, and the way to A08."""
    xf, yc, zc, w, h = -26.14, 11.9, 1.85, 2.2, 1.2
    M.box((xf - .03, yc, zc), (.06, w + .08, h + .08), 'oak')              # frame
    M.box((xf - .065, yc, zc), (.01, w, h), 'navy')                        # screen
    face = math.pi                                                          # text faces -x, into the concourse
    x = xf - .07
    text('DEPARTURES', (x, yc, zc + .42), face, .17, 'gold')
    M.box((x - .002, yc, zc + .28), (.004, w - .3, .01), 'gold')
    rows = (('SA107', 'AZURE BAY', 'A07', 'BOARDING'), ('SA208', 'NORTH COAST', 'A08', '10:55'))
    for k, (flt, dest, gate, status) in enumerate(rows):
        z = zc + .1 - k * .26
        for dy, word, mat in ((.82, flt, 'glow'), (.25, dest, 'glow'), (-.3, gate, 'gold'), (-.75, status, 'gold' if k == 0 else 'glow')):
            text(word, (x, yc + dy, z), face, .1, mat)
    text('<   A08  NORTH LOUNGE', (x, yc, zc - .45), face, .09, 'glow')


DECK = 3.17


def gallery(M):
    """The gallery over the cafe (deck x -49..-41, y 25..34, top 3.17 m), as an
    upper lounge. Built at floor level and lifted onto the deck on export.
    Kept: both benches and their passengers, the travel shop shelving, the bins
    and the stair landing (x -48.2..-44.8, y 25..27 stays clear)."""
    # sunset bar along the west glass
    y0, y1 = 27.3, 30.4
    M.box((-48.62, (y0 + y1) / 2, 1.02), (.5, y1 - y0, .05), 'oak')        # open counter: the glass stays clear
    M.box((-48.62, (y0 + y1) / 2, .965), (.42, y1 - y0 - .1, .06), 'walnut')
    for y in (y0 + .15, (y0 + y1) / 2, y1 - .15):
        M.box((-48.7, y, .5), (.05, .05, .94), 'black')
    M.box((-48.45, (y0 + y1) / 2, .22), (.03, y1 - y0 - .2, .03), 'steel')        # foot rail
    for k in range(5):
        y = y0 + (y1 - y0) * (k + .5) / 5
        M.cylinder((-48.05, y, .76), .2, .05, 'oak', seg=20)
        M.cylinder((-48.05, y, .38), .025, .72, 'black', seg=10)
        M.cylinder((-48.05, y, .01), .2, .02, 'black', seg=20)
    # a green screen of planters along the north glass, behind the bench
    for x in (-48.3, -46.8, -45.3):
        planter(M, x, 33.35, .38, .55)
        GTREES.append((x, 33.35, DECK + .55, .28))
    # conversation group facing the east bench and its passenger
    armchair(M, -44.55, 27.75, 0.0); armchair(M, -44.55, 29.1, 0.0)
    coffee_table(M, -43.45, 28.42, .55, 1.0)
    floor_lamp(M, -48.55, 31.25); floor_lamp(M, -41.55, 30.6)
    planter(M, -41.75, 33.3, .42, .55)
    GTREES.append((-41.75, 33.3, DECK + .55, .32))


def gallery_rug(F):
    rug(F, -47.65, -42.75, 27.0, 30.45)


GTREES = []


def main():
    global SOFT
    out = HERE / 'LoungeBuild'; out.mkdir(exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    M = Mesh(MATS); SOFT = Mesh(SOFT_MATS); F = Mesh(FLOOR_MATS2)
    globals()['SOFT'] = SOFT
    a08(M, F); a07(M, F); concourse(M)
    reps = {}
    reps['hard'] = finish(M, 'SM_AP_P62Lounges', out, WORDS)
    for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
    w0, s0 = mesh48.SOFT_WIDTH, mesh48.SOFT_SEGMENTS
    mesh48.SOFT_WIDTH, mesh48.SOFT_SEGMENTS = .045, 4
    reps['soft'] = finish(SOFT, 'SM_AP_P62LoungeSoft', out, [])
    mesh48.SOFT_WIDTH, mesh48.SOFT_SEGMENTS = w0, s0
    reps['floor'] = finish(F, 'SM_AP_P62LoungeFloor', out, [])
    # the gallery: built at floor level, lifted onto the deck
    from mathutils import Matrix
    G = Mesh(MATS); GS = Mesh(SOFT_MATS); GF = Mesh(FLOOR_MATS2)
    globals()['SOFT'] = GS
    gallery(G); gallery_rug(GF)
    for key, mesh, name, soft in (('gallery', G, 'SM_AP_P63Gallery', False), ('gallerysoft', GS, 'SM_AP_P63GallerySoft', True),
                                  ('galleryfloor', GF, 'SM_AP_P63GalleryFloor', False)):
        for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
        if soft:
            mesh48.SOFT_WIDTH, mesh48.SOFT_SEGMENTS = .045, 4
        obj = mesh.finish(name)
        mesh48.SOFT_WIDTH, mesh48.SOFT_SEGMENTS = w0, s0
        obj.data.transform(Matrix.Translation((0, 0, DECK)))
        fbx = out / (name + '.fbx'); export(obj, fbx)
        reps[key] = dict(status='SUCCESS', asset=name, fbx=str(fbx.resolve()), materials=[m.name for m in obj.data.materials],
                         polygons=len(obj.data.polygons))
    TREES.extend(GTREES)
    for k, r in reps.items():
        (HERE / ('Lounge62%sBuild.json' % k.capitalize())).write_text(json.dumps(r, indent=1), encoding='utf-8')
    (HERE / 'Lounge62Trees.json').write_text(json.dumps(TREES), encoding='utf-8')
    (HERE / 'Lounge64Seats.json').write_text(json.dumps(SEATS, indent=1), encoding='utf-8')
    print('LOUNGES62', {k: r['polygons'] for k, r in reps.items()}, len(TREES))


main()
