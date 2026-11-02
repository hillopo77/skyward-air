"""Pass70: security, the WC passage and the washrooms, redesigned (headless).

Player brief: a 50 million budget to redesign the bag screening area, the toilets
and the area outside the toilets. Built around everything that works: the two
screening lanes (tray stations, belts, scanners and curtains, portals, receiving
stations), the stanchion queue, the operator console, the staff door, the WC
cubicles, doors and releases, the vanity, the benches and the safety stations
all stay. Every opening stays clear (security: entry x -43.2..-40.8 on the south
wall, exit y 5.3..7.7 on the east wall, staff door x -46.5..-45.5; passage:
concourse y -3.9..-2.1, washrooms y -9.4..-7.6). Wall faces sit 0.09 m inside the
layout wall lines; fittings stand 0.02 m proud of them.

  SM_AP_P70Rooms       fit-out, complex collision
    security  (Pass71, rebuilt) pale stone cladding in a jointed grid with oak fins
              and a luminous reglet; a cool backlit feature wall 'SECURITY' with
              five navy roundels, white-lit pictograms and captions; lit lane blades
              with a green OPEN; slate lane zoning with light lines and brass
              footprints in each portal; white divest benches with a lit reveal and
              instruction panel; a recompose bench under a backlit mirror; planters;
              a backlit 'SECURITY' header over the entry (corridor side)
    passage   'gallery passage': three backlit landscape artworks with picture
              lights; a projecting lit WC blade sign with pictograms at the
              washroom entry; a bottle-refill station; a living green wall; an
              end-wall mural
    washrooms (Pass71, rebuilt) fluted walnut cubicle fronts floor to ceiling with
              brass portals, lit sign boxes and occupancy bars; a 5.8 m stone
              vanity with a fluted fascia, a glow cove, four vessel basins and
              brass goosenecks under four backlit mirrors and slim sconces, a
              slatted ceiling raft; a stone dryer bay, a baby-change unit; a backlit
              onyx feature wall; a bordered terrazzo floor; tiled cubicle backs with
              a lit shelf, grab rail and roll holder
  SM_AP_P70RoomsSoft   upholstery (recompose bench, passage cushions), complex collision
  SM_AP_P70RoomsFloor  passage runner, washroom tile floor, security lane inlays (no collision)
World source metres. Usage: blender -b --factory-startup -P rooms70_blender.py
"""
import bpy, json, math, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'Pass48'))
import mesh48
from mesh48 import Mesh, export

exec(compile(open(HERE / 'cafe60_blender.py', encoding='utf-8').read().split('\ndef main():')[0], 'cafe60', 'exec'))
MATS = dict(MATS, redglow=('MI_AP_P72GlowRed', (1, .1, .06)), porcelain=('MI_AP_P71Porcelain', (.95, .95, .94)), mirror=('MI_AP_P71Mirror', (.8, .84, .88)), tile=('MI_AP_P38ASage', (.4, .5, .4)), stone=('MI_AP_P34Cream', (.85, .8, .7)),
            white=('MI_AP_WhiteMark', (.92, .92, .92)), red=('MI_AP_Red', (.7, .05, .04)))
FLOOR_MATS70 = dict(rug=('MI_AP_P27Teal', (.05, .3, .3)), tile=('MI_AP_P34Cream', (.82, .78, .7)), grout=('MI_AP_P27Walnut', (.25, .13, .06)),
                    brass=('MI_AP_P38AGold', (.72, .48, .11)))
IN = .09                                                                 # wall face inside the layout line
MATS.update(secstone=('MI_AP_P71SecStone', (.2, .31, .29)), secopal=('MI_AP_P71SecOpal', (.92, .96, 1.0)),
            secgreen=('MI_AP_P71SecGreen', (.25, 1.0, .4)), secshell=('MI_AP_P71SecShell', (.86, .88, .9)))
FLOOR_MATS70.update(lane=('MI_AP_P71SecLaneFloor', (.18, .26, .34)), opal=('MI_AP_P71SecOpal', (.92, .96, 1.0)))
_ROOMS71 = HERE.parent / 'Pass48' / 'Rooms71.json'
ROOMS71 = json.loads(_ROOMS71.read_text(encoding='utf-8')) if _ROOMS71.exists() else {}
ROOMRECT = {'security': (-49, -36, -4, 10), 'wc_passage': (-26, -23, -12, -1), 'wc': (-23, -14, -12, -3)}
FACES = {}


def face(room, key, along=None):
    """Pass71: how far the real wall face stands inside the layout line, measured in the game
    (Pass48/rooms71_probe.py: the median of the 1.4 m and 2.2 m traces that met a wall within 0.6 m, over
    the stretch 'along' the fittings use; the 2.9 m traces are above the washroom ceiling).
    Before a measurement exists, 0.09 m: what Pass48/walls71_probe.py found on the perimeter walls."""
    rows = ROOMS71.get('rooms', {}).get(room, {}).get('walls', {}).get(key, [])
    ins = sorted(r[2] for r in rows if r[2] is not None and r[1] in (1.4, 2.2) and -.2 <= r[2] <= .6
                 and (along is None or along[0] <= r[0] <= along[1]))
    f = ins[len(ins) // 2] if len(ins) >= 4 else .09
    FACES['%s %s' % (room, key)] = [round(f, 3), len(ins)]
    return f


def wall(room, key, along=None):
    """The wall tuple wall_box() takes, placed so a fitting at proud=OFF stands 2 cm off the real face."""
    x0, x1, y0, y1 = ROOMRECT[room]
    line, ax, sgn = dict(S=(y0, 'y', 1), N=(y1, 'y', -1), W=(x0, 'x', 1), E=(x1, 'x', -1))[key]
    return (ax, line + sgn * (face(room, key, along) - .09), sgn)
OFF = .11                                                                # fittings: 2 cm proud of the face


# ---------------------------------------------------------------- helpers
def wall_box(M, wall, a, b, z0, z1, d, mat, proud=OFF):
    """A panel on a wall: wall = ('x', k, +1/-1) or ('y', k, +1/-1) (axis, line, inward sign);
    a..b along the wall, z0..z1, d thick, its back 'proud' inside the line."""
    ax, k, s = wall
    c = k + s * (proud + d / 2)
    if ax == 'x':
        M.box((c, (a + b) / 2, (z0 + z1) / 2), (d, b - a, z1 - z0), mat)
    else:
        M.box(((a + b) / 2, c, (z0 + z1) / 2), (b - a, d, z1 - z0), mat)


def wall_text(wall, along, z, body, size, mat, depth=.006, proud=OFF + .02):
    ax, k, s = wall
    if ax == 'x':
        text(body, (k + s * proud, along, z), 0.0 if s > 0 else math.pi, size, mat, depth=depth)
    else:
        text(body, (along, k + s * proud, z), math.pi / 2 if s > 0 else -math.pi / 2, size, mat, depth=depth)


def spans(a, b, gaps):
    """[a, b] minus the (g0, g1) gaps."""
    out, x = [], a
    for g0, g1 in sorted(gaps):
        if g0 > x:
            out.append((x, min(g0, b)))
        x = max(x, g1)
    if x < b:
        out.append((x, b))
    return [(p, q) for p, q in out if q - p > .15]


def acoustic(M, wall, a, b, gaps, z0=1.22, z1=3.02, bay=1.2):
    """Sage fabric panels in bays with dark reveals, above the existing wainscot."""
    for p, q in spans(a, b, gaps):
        wall_box(M, wall, p, q, z0 - .02, z1 + .02, .012, 'black')        # reveal backing
        n = max(1, round((q - p) / bay))
        for i in range(n):
            pa = p + (q - p) * i / n + .015; pb = p + (q - p) * (i + 1) / n - .015
            wall_box(M, wall, pa, pb, z0, z1, .028, 'sage', proud=OFF + .012)
        wall_box(M, wall, p, q, z1 + .02, z1 + .06, .03, 'gold', proud=OFF + .01)     # brass capping


def pictogram(M, wall, along, z, kind, s=.11, mat='navy', proud=OFF + .045):
    """Simple bold pictograms: liquids, laptop, belt, coat, phone; man, woman, access, baby."""
    def b(du, dz, w, h):
        wall_box(M, wall, along + du - w / 2, along + du + w / 2, z + dz - h / 2, z + dz + h / 2, .008, mat, proud=proud)
    if kind == 'liquids':
        b(0, -.02, s * .7, s * 1.0); b(0, s * .6, s * .3, s * .25)
    elif kind == 'laptop':
        b(0, s * .15, s * 1.2, s * .75); b(0, -s * .4, s * 1.5, s * .12)
    elif kind == 'belt':
        b(0, 0, s * 1.5, s * .25); b(s * .55, 0, s * .3, s * .45)
    elif kind == 'coat':
        b(0, -s * .1, s * .9, s * 1.1); b(0, s * .6, s * .4, s * .2)
    elif kind == 'phone':
        b(0, 0, s * .55, s * 1.05)
    elif kind in ('man', 'woman'):
        b(0, s * .75, s * .38, s * .38)                                     # head
        b(0, s * .05, s * .62, s * .85) if kind == 'man' else b(0, s * .05, s * .9, s * .85)
        b(-s * .14, -s * .65, s * .2, s * .55); b(s * .14, -s * .65, s * .2, s * .55)
    elif kind == 'access':
        b(0, s * .75, s * .34, s * .34); b(-s * .05, s * .15, s * .22, s * .7); b(s * .15, -s * .2, s * .6, s * .18)
        b(-s * .1, -s * .45, s * .9, s * .12)
    elif kind == 'baby':
        b(0, s * .2, s * 1.1, s * .5); b(-s * .35, s * .6, s * .32, s * .32)


def lightbox(M, wall, a, b, z0, z1):
    wall_box(M, wall, a - .04, b + .04, z0 - .04, z1 + .04, .05, 'walnut')
    wall_box(M, wall, a, b, z0, z1, .012, 'shade', proud=OFF + .05)


# ---------------------------------------------------------------- security (x -49..-36, y -4..10)
# Pass71: rebuilt (the player: no effort in the textures and materials, and hard to see in there). Bright and
# legible: pale stone cladding in a jointed grid with oak fins and a luminous reglet, a cool backlit feature
# wall with white-lit divest roundels and captions, lit lane blades with a green OPEN, lane zoning on the floor
# with light lines and footprints in each portal, white divest benches with a lit reveal. The machines get
# their new materials and the room its lights in Pass51/security71_editor.py.
PORTALS = (-45.5, -40.4)
BELTS = (-43.15, -38.05)


PANEL = .12                                                              # covers the hall's wall panels (no collision, depth unknown)


def clad(M, wall_, a, b, gaps, z0=1.22, z1=3.3, bay=1.2):
    """Large-format stone panels: two rows of bays with fine dark joints, an oak fin every second joint,
    and a luminous reglet line at 2.86 m. The hall's beige wall panels have no collision and stand about 5 cm
    in front of the face the probe measures, so the cladding sits PANEL further out to cover them."""
    for p, q in spans(a, b, gaps):
        wall_box(M, wall_, p, q, z0, z1, PANEL + .02, 'secstone', proud=OFF)              # a solid slab off the wall
        n = max(1, round((q - p) / bay))
        for i in range(1, n):
            u0 = p + (q - p) * i / n
            if i % 2 == 0:
                wall_box(M, wall_, u0 - .025, u0 + .025, z0, 2.82, .1, 'oak', proud=OFF + PANEL + .02)
            else:
                wall_box(M, wall_, u0 - .004, u0 + .004, z0, z1, .004, 'black', proud=OFF + PANEL + .02)
        wall_box(M, wall_, p, q, 2.04, 2.048, .004, 'black', proud=OFF + PANEL + .02)
        wall_box(M, wall_, p, q, 2.82, 2.9, .03, 'navy', proud=OFF + PANEL + .02)
        wall_box(M, wall_, p + .02, q - .02, 2.85, 2.87, .006, 'secopal', proud=OFF + PANEL + .05)
        wall_box(M, wall_, p, q, z0 - .02, z0 + .02, .04, 'gold', proud=OFF + PANEL)


def security(M, S, F):
    W, Sth, N, E = (wall('security', k) for k in ('W', 'S', 'N', 'E'))
    clad(M, W, -3.8, 9.8, [(-.3, 6.2), (6.75, 8.45)])                      # feature wall; the operator console
    clad(M, Sth, -48.8, -36.2, [(-43.3, -40.7)])                         # entry
    clad(M, N, -48.8, -36.2, [(-46.6, -45.4), (-45.0, -38.5)])           # staff door; the recompose mirror
    clad(M, E, -3.8, 9.8, [(5.2, 7.8)])                                  # exit
    # feature wall: a cool backlit light wall, 'SECURITY', five navy roundels with white-lit pictograms and captions
    wall_box(M, W, -.3, 6.2, 1.2, 3.02, .07, 'navy')
    wall_box(M, W, -.2, 6.1, 1.28, 2.94, .012, 'secopal', proud=OFF + .07)
    wall_text(W, 2.95, 2.58, 'SECURITY', .46, 'navy', depth=.014, proud=OFF + .082)
    wall_text(W, 2.95, 2.24, 'SAFE  TRAVELS  START  HERE', .12, 'navy', depth=.008, proud=OFF + .082)
    wx = W[1] + W[2] * (OFF + .09)
    for i, (k, cap) in enumerate((('liquids', 'LIQUIDS 100 ML'), ('laptop', 'LAPTOPS OUT'), ('coat', 'COATS OFF'),
                                   ('belt', 'BELTS OFF'), ('phone', 'PHONES IN TRAY'))):
        y = .55 + i * 1.2
        M.cylinder((wx, y, 1.78), .27, .012, 'navy', seg=40, axis='x')
        pictogram(M, W, y, 1.78, k, s=.16, mat='secopal', proud=OFF + .096)
        wall_text(W, y, 1.42, cap, .09, 'navy', depth=.006, proud=OFF + .082)
    # lane blades over each lane entrance: 'LANE n' lit white and a green OPEN, both faces
    for lane, (px, bx) in enumerate(zip(PORTALS, BELTS), 1):
        cx, yb = (px + bx) / 2, -.3
        M.box((cx, yb, 2.57), (3.0, .09, .36), 'navy')
        for sg in (-1, 1):
            rx = 1 if sg < 0 else -1                                             # the reader's right along x
            text('LANE  %d' % lane, (cx - rx * .55, yb + sg * .046, 2.57), -math.pi / 2 if sg < 0 else math.pi / 2, .2, 'secopal', depth=.006)
            M.box((cx + rx * .9, yb + sg * .047, 2.57), (.62, .006, .2), 'secgreen')
            text('OPEN', (cx + rx * .9, yb + sg * .052, 2.57), -math.pi / 2 if sg < 0 else math.pi / 2, .11, 'navy', depth=.004)
        for dx in (-1.3, 1.3):
            M.cylinder((cx + dx, yb, 3.1), .008, .7, 'steel', seg=8)
    # floor: a slate lane for each walk-through path with light lines at its edges, footprints in the portal
    for px in PORTALS:
        F.box((px, 2.85, .004), (1.4, 6.3, .006), 'lane')
        for dx in (-.72, .72):
            F.box((px + dx, 2.85, .006), (.035, 6.3, .004), 'opal')
        for dx in (-.13, .13):
            F.box((px + dx, 3.0, .0075), (.1, .24, .002), 'brass')
            F.cylinder((px + dx, 3.12, .0075), .05, .002, 'brass', seg=16)
            F.cylinder((px + dx, 2.88, .0075), .045, .002, 'brass', seg=16)
    # divest benches: white solid surface, a rubber mat, a lit reveal under the lip, a lit instruction panel
    for x in (-44.25, -36.95):
        y0, y1 = -2.2, -.45
        M.box((x, (y0 + y1) / 2, .43), (.52, y1 - y0 - .1, .8), 'secshell')
        M.box((x, (y0 + y1) / 2, .86), (.64, y1 - y0, .05), 'white')
        M.box((x, (y0 + y1) / 2, .888), (.58, y1 - y0 - .06, .006), 'black')
        for sx in (-1, 1):
            M.box((x + sx * .27, (y0 + y1) / 2, .825), (.012, y1 - y0 - .14, .012), 'secopal')
        M.box((x, y1 - .04, 1.35), (.52, .06, .66), 'navy')
        M.box((x, y1 - .072, 1.35), (.46, .006, .58), 'secshell')
        for i, k in enumerate(('liquids', 'laptop', 'coat', 'phone')):
            zz = 1.52 - (i // 2) * .28; xx = x - .11 + (i % 2) * .22
            pictogram(M, ('y', y1 - .075, -1), xx, zz, k, s=.075, mat='navy', proud=0.0)
        text('1 TRAY PER ITEM', (x, y1 - .078, 1.1), -math.pi / 2, .045, 'navy', depth=.003)
    # recompose bench along the north wall, a backlit mirror strip and a tray ledge above
    xb0, xb1 = -44.9, -38.6
    yb = N[1] - (OFF + .3)
    M.box(((xb0 + xb1) / 2, yb, .21), (xb1 - xb0, .5, .42), 'oak')
    S.box(((xb0 + xb1) / 2, yb + .02, .47), (xb1 - xb0 - .06, .48, .1), 'teal')
    for x in (xb0 + 1.5, (xb0 + xb1) / 2, xb1 - 1.5):
        S.box((x, yb + .22, .78), (1.2, .12, .5), 'cushion')
    wall_box(M, N, xb0, xb1, 1.08, 1.12, .2, 'oak')
    wall_box(M, N, xb0 + .3, xb1 - .3, 1.3, 2.2, PANEL + .03, 'secopal', proud=OFF)
    wall_box(M, N, xb0 + .36, xb1 - .36, 1.36, 2.14, .006, 'mirror', proud=OFF + PANEL + .03)
    clad(M, N, xb0, xb1, [], z0=2.2)
    for x, y in ((-45.25, N[1] - .7), (-38.25, N[1] - .7)):
        planter(M, x, y, .32, .55)
        for dx, dy, r, m in ((0, 0, .3, 'leaf'), (.12, .1, .22, 'leaf2'), (-.12, -.08, .2, 'leaf')):
            M.blob((x + dx, y + dy, .78 + r * .5), r, m, squash=.9, subdiv=2)
    # entry header on the corridor side of the south wall, backlit
    hdr = ('y', -4 - IN, -1)
    wall_box(M, hdr, -44.0, -40.0, 2.62, 3.2, .06, 'navy')
    wall_box(M, hdr, -43.92, -40.08, 2.68, 3.14, .006, 'secopal', proud=OFF + .06)
    wall_text(hdr, -42.0, 2.91, 'SECURITY', .3, 'navy', depth=.01, proud=OFF + .07)


# ---------------------------------------------------------------- WC passage (x -26..-23, y -12..-1)
def passage(M, S, F):
    W, E, Sth = (wall('wc_passage', k) for k in ('W', 'E', 'S'))
    for i, y in enumerate((-10.1, -8.0)):                                  # backlit landscapes (above the bench run)
        a, b = y - .7, y + .7
        lightbox(M, W, a, b, 1.45, 2.45)
        for mat, top in (('sage', 1.98), ('fabric', 1.82), ('teal', 1.7), ('navy', 1.6)):
            wall_box(M, W, a + .02, b - .02, 1.47, top + .04 * math.sin(i + top * 7), .004, mat, proud=OFF + .065)
        M.cylinder((W[1] + .16, y, 2.56), .015, .9, 'gold', seg=10, axis='y')   # picture light
    a, b = -6.9, -5.5
    lightbox(M, W, a, b, 1.45, 2.45)
    for mat, top in (('fabric', 2.1), ('clay', 1.85), ('gold', 1.72), ('walnut', 1.58)):
        wall_box(M, W, a + .02, b - .02, 1.47, top, .004, mat, proud=OFF + .065)
    M.cylinder((W[1] + .16, -6.2, 2.56), .015, .9, 'gold', seg=10, axis='y')
    # projecting WC blade sign at the washroom entry (double-sided, perpendicular to the wall)
    x0 = E[1] - .05
    M.box((x0 - .35, -8.5, 2.62), (.7, .06, .5), 'navy')
    for sgn in (-1, 1):
        M.box((x0 - .35, -8.5 + sgn * .032, 2.62), (.64, .006, .44), 'shade')
        side = ('y', -8.5 + sgn * .035, sgn)
        for j, k in enumerate(('man', 'woman', 'access', 'baby')):
            pictogram(M, side, x0 - .62 + j * .18, 2.66, k, s=.07, proud=0.0)
    M.box((x0 - .02, -8.5, 2.62), (.04, .1, .3), 'steel')
    # bottle refill station
    wall_box(M, E, -5.9, -5.1, .35, 1.75, .06, 'oak')
    wall_box(M, E, -5.82, -5.18, .5, 1.6, .02, 'steel', proud=OFF + .06)
    wall_box(M, E, -5.6, -5.4, 1.2, 1.25, .12, 'steel', proud=OFF + .08)        # spout
    wall_box(M, E, -5.82, -5.18, 1.62, 1.66, .02, 'glow', proud=OFF + .065)
    wall_text(E, -5.5, 1.71, 'REFILL', .07, 'navy', depth=.004, proud=OFF + .065)
    # living green wall at the south end of the east side
    wall_box(M, E, -11.85, -9.55, .35, 2.55, .05, 'black')
    import random as _r
    rr = _r.Random(70)
    for i in range(46):
        y = rr.uniform(-11.7, -9.7); z = rr.uniform(.5, 2.4); r = rr.uniform(.12, .2)
        M.blob((E[1] - OFF - .08, y, z), r, 'leaf' if i % 3 else 'leaf2', squash=.7, subdiv=1)
    # end-wall mural: a sunrise over the coast
    a, b = -25.2, -23.8
    wall_box(M, Sth, a - .05, b + .05, 1.25, 2.75, .04, 'walnut')
    for mat, z1 in (('cream', 2.7), ('gold', 2.0), ('sage', 1.75), ('teal', 1.55), ('navy', 1.42)):
        wall_box(M, Sth, a, b, 1.3, z1, .004, mat, proud=OFF + .04)
    M.cylinder((-24.5, Sth[1] + OFF + .045, 2.15), .22, .006, 'gold', seg=28, axis='y')
    # teal runner down the passage
    F.box((-24.45, -6.5, .004), (1.3, 10.0, .008), 'rug')


# ---------------------------------------------------------------- washrooms (x -23..-14, y -12..-3)
# Pass71: rebuilt from scratch (the player called Pass70's version lazy). The open washroom lies south of the
# cubicle front (face y -7.294); cubicle doors at x -21.58..-20.46 and -17.68..-16.56; the passage opens on the
# west wall at y -9.4..-7.6; toilets at (-21.0, -4.23) and (-17.1, -4.23) against the north wall.
FRONT = -7.294
DOORS = [(-21.58, -20.46), (-17.68, -16.56)]
FAKE = [(-19.72, 2), (-18.42, 3), (-15.935, 5)]                                # stalls drawn closed (centre, number)
STALL_EDGES = [-22.53, -20.37, -19.0, -17.77, -16.47, -15.4]                # stall 1 (accessible) .. stall 5
BASINS = [-20.875, -19.425, -17.975, -16.525]
CX0, CX1 = -21.6, -15.8                                                    # the vanity counter


def flutes(M, wall, a, b, z0, z1, pitch=.065, r=.028):
    """Floor-to-ceiling fluted panelling: half-round walnut flutes on a dark backing."""
    ax, k, sgn = wall
    wall_box(M, wall, a, b, z0, z1, .012, 'black', proud=0.0)
    n = int((b - a) / pitch)
    for i in range(n):
        u0 = a + (b - a) * (i + .5) / n
        c = k + sgn * (.014 + r * .6)
        if ax == 'y':
            M.cylinder((u0, c, (z0 + z1) / 2), r, z1 - z0, 'walnut', seg=10)
        else:
            M.cylinder((c, u0, (z0 + z1) / 2), r, z1 - z0, 'walnut', seg=10)


def tiles(M, wall, a, b, z0, z1, mat='tile', grid=.2, proud=OFF, grout='cream'):
    wall_box(M, wall, a, b, z0, z1, .012, mat, proud=proud)
    for zz in [z0 + grid * k for k in range(1, int((z1 - z0) / grid) + 1)]:
        if zz < z1 - .01:
            wall_box(M, wall, a, b, zz - .003, zz + .003, .003, grout, proud=proud + .012)
    n = max(1, int((b - a) / grid))
    for k in range(1, n):
        u0 = a + (b - a) * k / n
        wall_box(M, wall, u0 - .003, u0 + .003, z0, z1, .003, grout, proud=proud + .012)


def joinery(M, wall, p, q, top=2.6, skirt=.12, rows=((.124, 1.146), (1.154, 2.256), (2.264, 2.596)), proud=0.0, bay=.6):
    """Pass71b: the washroom's joinery: a stone skirting, walnut panels set out on an even module in rows, every
    panel separated by a fine brass reveal (cubicle fronts, cubicle side walls, the amenity wall)."""
    wall_box(M, wall, p, q, 0.0, skirt, .035, 'stone', proud=proud)
    wall_box(M, wall, p, q, skirt, top, .008, 'gold', proud=proud)
    n = max(1, round((q - p) / bay))
    for k in range(n):
        pa = p + (q - p) * k / n + .004; pb = p + (q - p) * (k + 1) / n - .004
        for z0, z1 in rows:
            z1 = min(z1, top - .004)
            if z1 > z0 + .02:
                wall_box(M, wall, pa, pb, z0, z1, .022, 'walnut', proud=proud + .008)


def loft(M, rings, mat, seg=48):
    """A smooth closed solid through rounded-rectangle rings [(z, cx, cy, half_w, half_l, exponent)]."""
    bm = M.bm
    vs = []
    for z, cx, cy, hw, hl, ex in rings:
        ring = []
        for k in range(seg):
            a = 2 * math.pi * k / seg
            c, s_ = math.cos(a), math.sin(a)
            ring.append(bm.verts.new((cx + hw * math.copysign(abs(c) ** (2 / ex), c), cy + hl * math.copysign(abs(s_) ** (2 / ex), s_), z)))
        vs.append(ring)
    fs = []
    for r0, r1 in zip(vs, vs[1:]):
        for k in range(seg):
            fs.append(M._face([r0[k], r0[(k + 1) % seg], r1[(k + 1) % seg], r1[k]], mat))
    fs.append(M._face(list(reversed(vs[0])), mat)); fs.append(M._face(vs[-1], mat))
    M.solid += fs


def toilet(M, x, wall_y):
    """A wall-hung toilet (white porcelain, lid down) on a concealed-cistern ledge whose front face is at wall_y."""
    cy = wall_y - .3                                                     # bowl centre; its front at wall_y - .57
    loft(M, [(.24, x, cy + .02, .13, .2, 2.4), (.28, x, cy, .165, .25, 2.6), (.36, x, cy - .005, .185, .27, 2.8),
             (.395, x, cy - .005, .188, .272, 2.8)], 'porcelain')
    M.box((x, wall_y - .03, .31), (.3, .06, .16), 'porcelain')           # the neck into the ledge
    loft(M, [(.397, x, cy - .01, .182, .268, 2.8), (.418, x, cy - .01, .18, .266, 2.8)], 'porcelain')   # seat
    loft(M, [(.42, x, cy - .012, .176, .262, 2.8), (.445, x, cy - .016, .17, .255, 2.8)], 'porcelain')  # lid
    M.cylinder((x, wall_y - .045, .425), .012, .26, 'gold', seg=12, axis='x')                          # hinge bar


def washrooms(M, S, F):
    Sth, E, N = (wall('wc', k) for k in ('S', 'E', 'N'))
    W = wall('wc', 'W', along=(-12, -7.4))                                 # the open washroom, not the cubicle side walls
    front = ('y', FRONT, -1)
    sy = Sth[1] + 11.91                                                       # the vanity wall as measured
    # floor: cream terrazzo slabs, a sage border band with a brass inlay
    x0, x1, y0, y1 = -22.86, -14.14, -11.86, -7.34
    F.box(((x0 + x1) / 2, (y0 + y1) / 2, .003), (x1 - x0, y1 - y0, .006), 'tile')
    for k in range(1, int((x1 - x0) / .6) + 1):
        F.box((x0 + k * .6, (y0 + y1) / 2, .0062), (.006, y1 - y0 - .4, .002), 'grout')
    for k in range(1, int((y1 - y0) / .6) + 1):
        F.box(((x0 + x1) / 2, y0 + k * .6, .0062), (x1 - x0 - .4, .006, .002), 'grout')
    for (cx, cy, bw, bd) in (((x0 + x1) / 2, y0 + .1, x1 - x0, .2), ((x0 + x1) / 2, y1 - .1, x1 - x0, .2),
                             (x0 + .1, (y0 + y1) / 2, .2, y1 - y0), (x1 - .1, (y0 + y1) / 2, .2, y1 - y0)):
        F.box((cx, cy, .0064), (bw, bd, .002), 'rug')
    for (cx, cy, bw, bd) in (((x0 + x1) / 2, y0 + .2, x1 - x0 - .4, .012), ((x0 + x1) / 2, y1 - .2, x1 - x0 - .4, .012),
                             (x0 + .2, (y0 + y1) / 2, .012, y1 - y0 - .4), (x1 - .2, (y0 + y1) / 2, .012, y1 - y0 - .4)):
        F.box((cx, cy, .0066), (bw, bd, .002), 'brass')
    # cubicle fronts (Pass71b: the player found the full-height flutes raw, 'large uncut pieces of wood'): neat
    # joinery instead. A stone skirting; walnut panels on a module set out from the doors, two rows, every
    # panel separated by a fine brass reveal; a transom band at door-head height with the sign boxes; a
    # navy cornice at the ceiling with a light line under it; brass door architraves with a lit occupancy line
    TOP, HEAD, SKIRT = 2.79, 2.26, .12
    # Pass71c (the player: the toilets are too big, make more stalls): five stalls 1.3 m on centres, set out from
    # the two real doors (stall 1, accessible, behind door 0; stall 4 behind door 1). Stalls 2, 3 and 5 are behind
    # the building's own front wall, so their doors are drawn closed with a red OCCUPIED light
    openings = [(d0 - .07, d1 + .07) for d0, d1 in DOORS] + [(c - .57, c + .57) for c, n in FAKE]
    for p, q in spans(-22.86, -14.14, sorted(openings)):
        joinery(M, front, p, q)
    wall_box(M, front, -22.86, -14.14, 2.6, 2.63, .02, 'glow', proud=.0)                     # light line under the cornice
    wall_box(M, front, -22.86, -14.14, 2.63, TOP, .05, 'navy', proud=0.0)                    # cornice
    wall_box(M, front, -22.86, -14.14, 2.63, 2.645, .06, 'gold', proud=0.0)
    doors = [((d0 + d1) / 2, d0, d1, n, True) for (d0, d1), n in zip(DOORS, (1, 4))] + [(c, c - .5, c + .5, n, False) for c, n in FAKE]
    for cx, d0, d1, n, real in doors:
        for xj in (d0 - .045, d1 + .045):                                                     # architraves
            wall_box(M, front, xj - .025, xj + .025, 0.0, HEAD, .045, 'gold', proud=0.0)
        wall_box(M, front, d0 - .07, d1 + .07, HEAD - .05, HEAD, .045, 'gold', proud=0.0)
        wall_box(M, front, d0 + .05, d1 - .05, HEAD - .035, HEAD - .015, .006, 'glow' if real else 'redglow', proud=.045)
        wall_box(M, front, d0 - .07, d1 + .07, HEAD, 2.6, .03, 'walnut', proud=0.0)          # transom over the door
        wall_box(M, front, cx - .3, cx + .3, HEAD + .05, 2.55, .03, 'gold', proud=.03)        # sign box, brass frame
        wall_box(M, front, cx - .28, cx + .28, HEAD + .07, 2.53, .006, 'shade', proud=.06)
        wall_text(front, cx - .17, 2.4, str(n), .17, 'navy', depth=.008, proud=.066)
        for j, kd in enumerate(('access', 'baby') if n == 1 else ('man', 'woman')):
            pictogram(M, front, cx + .04 + j * .16, 2.41, kd, s=.06, proud=.066)
        if not real:                                                                          # the closed door
            wall_box(M, front, d0, d1, .1, HEAD - .05, .04, 'walnut', proud=0.0)
            for z0, z1 in ((.3, 1.0), (1.2, 2.0)):
                wall_box(M, front, d0 + .1, d1 - .1, z0, z1, .006, 'gold', proud=.04)
                wall_box(M, front, d0 + .106, d1 - .106, z0 + .006, z1 - .006, .007, 'walnut', proud=.04)
            wall_box(M, front, d1 - .2, d1 - .07, 1.0, 1.03, .05, 'gold', proud=.04)          # lever handle
            wall_box(M, front, d1 - .13, d1 - .07, .92, 1.1, .02, 'black', proud=.04)        # lock indicator
            wall_box(M, front, d1 - .12, d1 - .08, 1.04, 1.08, .004, 'redglow', proud=.06)
            wall_text(front, cx, 1.62, 'OCCUPIED', .045, 'gold', depth=.003, proud=.046)
    # the vanity wall: stone counter, fluted fascia, a glow cove under it, four vessel basins, brass taps
    cy0, cy1 = Sth[1] + OFF, -11.33 + sy
    M.box(((CX0 + CX1) / 2, (cy0 + cy1) / 2, .88), (CX1 - CX0, cy1 - cy0, .06), 'stone')
    for k in range(int((CX1 - CX0) / .028)):                                                  # fine reeded fascia
        xf = CX0 + .014 + k * .028
        M.cylinder((xf, cy1 - .012, .73), .011, .24, 'walnut', seg=8)
    M.box(((CX0 + CX1) / 2, cy1 - .03, .73), (CX1 - CX0, .03, .24), 'black')
    M.box(((CX0 + CX1) / 2, cy1 - .06, .605), (CX1 - CX0 - .1, .03, .012), 'glow')          # cove: lights the floor
    for k, bx in enumerate(BASINS):
        M.cylinder((bx, -11.6 + sy, .975), .19, .13, 'white', seg=40)
        M.cylinder((bx, -11.6 + sy, 1.036), .165, .012, 'stone', seg=40)
        M.cylinder((bx, -11.84 + sy, 1.06), .016, .3, 'gold', seg=16)                             # gooseneck tap
        M.cylinder((bx, -11.76 + sy, 1.2), .014, .17, 'gold', seg=16, axis='y')
        M.cylinder((bx, -11.68 + sy, 1.18), .012, .04, 'gold', seg=12)
        if k < 3:
            M.cylinder((bx + .725, -11.8 + sy, .97), .032, .12, 'black', seg=16)                  # soap dispenser
            M.cylinder((bx + .725, -11.8 + sy, 1.045), .01, .03, 'gold', seg=10)
    wall_box(M, Sth, CX0, CX1, .91, 1.15, .02, 'stone')                                       # splashback
    my = Sth[1] + OFF                                                                        # arched, backlit mirrors
    for k, bx in enumerate(BASINS):
        for r, mat, pr, d in ((.5, 'glow', .02, .02), (.46, 'mirror', .045, .012)):
            wall_box(M, Sth, bx - r, bx + r, 1.2 + .5 - r, 1.86, d, mat, proud=OFF + pr)
            M.cylinder((bx, my + pr + d / 2, 1.86), r, d, mat, seg=48, axis='y')
    for xs in [BASINS[0] - .725] + [b + .725 for b in BASINS]:                                # slim sconces between them
        M.cylinder((xs, Sth[1] + OFF + .07, 1.72), .028, .5, 'shade', seg=20)
        M.cylinder((xs, Sth[1] + OFF + .07, 1.45), .034, .02, 'gold', seg=20)
        M.cylinder((xs, Sth[1] + OFF + .07, 1.99), .034, .02, 'gold', seg=20)
    rx0, rx1, ry0, ry1, rz = CX0 - .2, CX1 + .2, -11.88 + sy, -10.55 + sy, 2.52                         # ceiling raft over the vanity
    for k in range(int((rx1 - rx0) / .09)):
        M.box((rx0 + .045 + k * .09, (ry0 + ry1) / 2, rz), (.05, ry1 - ry0, .06), 'walnut')
    M.box(((rx0 + rx1) / 2, ry1 + .02, rz - .035), (rx1 - rx0, .03, .012), 'glow')
    for xr in (rx0 + .3, rx1 - .3):
        M.cylinder((xr, (ry0 + ry1) / 2, (rz + 2.8) / 2), .008, 2.8 - rz, 'steel', seg=8)
    # east wall (Pass71b, the player: improve this): one built-in amenity wall 0.28 m deep, in the cubicle-front
    # joinery: two lit stone niches with blade hand dryers and flush brass waste slots below, a recessed
    # baby-change unit with a brass sign, a light line under a navy cornice. It also covers the building's old dryer
    ea, eb, D = -11.0, -7.45, .28
    face_ = OFF + D - .02                                                                 # its face, from the wall line
    NICHES = [(-10.5, 'dry', .3), (-9.7, 'dry', .3), (-8.2, 'baby', .55)]
    cuts = [(c - h, c + h) for c, k, h in NICHES]
    for p, q in spans(ea, eb, cuts):                                                     # the carcass, around the niches
        wall_box(M, E, p, q, 0.0, 2.45, D - .02, 'black', proud=OFF - .02)
    for a0, a1 in cuts:
        wall_box(M, E, a0, a1, 0.0, .86, D - .02, 'black', proud=OFF - .02)
        wall_box(M, E, a0, a1, 1.66, 2.45, D - .02, 'black', proud=OFF - .02)
    for p, q in spans(ea, eb, cuts):
        joinery(M, E, p, q, top=2.36, proud=face_)
    pa, pb = cuts[1][1], cuts[2][0]                                                     # between the dryers and the baby
    wall_box(M, E, pa, pb, 0.0, 2.36, .3, 'walnut', proud=face_)                         # change: a deep pilaster that
    for u0 in (pa, pb - .016):                                                            # covers the building's old dryer
        wall_box(M, E, u0, u0 + .016, 0.0, 2.36, .3, 'gold', proud=face_ + .002)
    wall_box(M, E, (pa + pb) / 2 - .01, (pa + pb) / 2 + .01, .3, 2.2, .01, 'glow', proud=face_ + .3)
    for (c, kind, h), (a0, a1) in zip(NICHES, cuts):
        joinery(M, E, a0, a1, top=.86, proud=face_)                                     # below the niche
        wall_box(M, E, a0, a1, 1.66, 2.36, .03, 'walnut', proud=face_)                  # above it
        for u0, u1, z0, z1 in ((a0 - .004, a0 + .012, .86, 1.66), (a1 - .012, a1 + .004, .86, 1.66),
                               (a0, a1, .86, .876), (a0, a1, 1.644, 1.66)):
            wall_box(M, E, u0, u1, z0, z1, face_ + .03 - (OFF + .1), 'gold', proud=OFF + .1)   # brass-lined niche sides
        wall_box(M, E, a0 + .012, a1 - .012, .876, 1.644, .012, 'stone', proud=OFF + .1)   # niche back, 0.16 deep
        wall_box(M, E, a0 + .03, a1 - .03, 1.615, 1.635, .02, 'glow', proud=OFF + .14)     # a light along its top
        if kind == 'dry':
            wall_box(M, E, c - .15, c + .15, 1.12, 1.5, .12, 'white', proud=OFF + .112)    # blade dryer
            wall_box(M, E, c - .13, c + .13, 1.08, 1.12, .1, 'steel', proud=OFF + .112)
            wall_box(M, E, c - .11, c + .11, 1.42, 1.44, .004, 'black', proud=OFF + .232)  # its blade slot
            wall_box(M, E, c - .16, c + .16, .46, .58, .006, 'navy', proud=face_ + .022)   # flush waste slot
            wall_box(M, E, c - .14, c + .14, .49, .55, .004, 'black', proud=face_ + .028)
            wall_box(M, E, c - .16, c + .16, .58, .59, .008, 'gold', proud=face_ + .022)
        else:
            wall_box(M, E, c - .45, c + .45, .9, 1.56, .03, 'walnut', proud=OFF + .112)    # fold-down table, closed
            wall_box(M, E, c - .2, c + .2, 1.5, 1.52, .02, 'gold', proud=OFF + .142)       # its brass pull
            pictogram(M, E, c, 1.25, 'baby', s=.13, mat='gold', proud=OFF + .142)
            text('BABY CHANGE', (E[1] - (OFF + .145), c, 1.03), math.pi, .05, 'gold', depth=.003)
    wall_box(M, E, ea, eb, 2.36, 2.38, .02, 'glow', proud=face_ - .02)
    wall_box(M, E, ea, eb, 2.38, 2.48, D + .02, 'navy', proud=OFF - .02)                 # cornice
    # west wall: a deep teal feature panel with brass inlays in a walnut frame, a tall plant in the corner
    wall_box(M, W, -11.75, -9.6, .25, 2.55, .05, 'walnut')
    wall_box(M, W, -11.68, -9.67, .32, 2.48, .012, 'teal', proud=OFF + .05)
    for zz in (.9, 1.45, 2.0):                                                               # onyx veining
        wall_box(M, W, -11.6, -9.75, zz, zz + .012, .004, 'gold', proud=OFF + .062)
    planter(M, -22.4, -11.4 + sy, .3, .62)
    for dx, dy, r, m in ((0, 0, .32, 'leaf'), (.12, .1, .25, 'leaf2'), (-.12, -.08, .22, 'leaf'), (.05, -.12, .2, 'leaf2')):
        M.blob((-22.4 + dx, -11.4 + sy + dy, .95 + r * .7), r, m, squash=.9, subdiv=2)
    # inside the stalls (Pass71c): 1.9 m deep, full-height walnut partitions, a teal tiled back wall over a
    # concealed-cistern ledge with a lit stone top and a brass flush plate, a wall-hung white toilet, a brass roll
    # holder and hook; the accessible stall 1 has its toilet by the side wall with grab rails. A stone floor over
    # the old mosaic. Behind the new back wall (to the building's wall at y -3.37) is a closed service void
    BACK = FRONT + 1.9                                                                   # the stalls' back face
    bwall = ('y', BACK, -1)                                                              # its stall-side face
    wall_box(M, bwall, -22.53, -15.4, 0.0, 2.79, .1, 'walnut', proud=-.1)                  # the back partition
    for xp in STALL_EDGES[1:-1]:
        M.box((xp, (FRONT + BACK) / 2 - .02, 1.395), (.05, BACK - FRONT - .04, 2.79), 'walnut')   # partitions to the ceiling
    for n, s0, s1, tx, access in ((1, -22.53, -20.37, -21.95, True), (4, -17.77, -16.47, -17.12, False)):
        a0, a1 = s0 + (.025 if n != 1 else 0), s1 - .025
        tiles(M, bwall, a0, a1, 1.12, 2.6, mat='teal', grid=.3, proud=0.0, grout='navy')
        wall_box(M, bwall, a0, a1, 0.0, 1.06, .2, 'teal', proud=0.0)                    # concealed-cistern ledge
        for zz in (.35, .7):
            wall_box(M, bwall, a0, a1, zz - .002, zz + .002, .003, 'navy', proud=.2)
        wall_box(M, bwall, a0, a1, 1.06, 1.12, .23, 'stone', proud=0.0)                 # stone top
        wall_box(M, bwall, a0 + .05, a1 - .05, 1.04, 1.055, .01, 'glow', proud=.19)
        wall_box(M, bwall, tx - .12, tx + .12, .78, .95, .01, 'gold', proud=.2)         # flush plate
        for bx in (tx - .055, tx + .055):
            wall_box(M, bwall, bx - .045, bx + .045, .8, .93, .006, 'steel', proud=.21)
        ledge = BACK - .2
        toilet(M, tx, ledge)
        sides = ((s0, 1), (s1 - .025, -1)) if n == 1 else ((s0 + .025, 1), (s1 - .025, -1))
        for xf, sg in sides:
            joinery(M, ('x', xf, sg), FRONT + .05, BACK, top=2.6, bay=.62)
        wall_box(M, bwall, a0, a1, 2.6, 2.79, .05, 'navy', proud=0.0)                  # cornice
        hx = s0 + (.025 if n != 1 else 0)
        M.cylinder((tx + .32, ledge - .06, .62), .055, .11, 'gold', seg=20, axis='x')  # roll holder
        M.cylinder((tx + .32, ledge - .03, .62), .01, .06, 'gold', seg=8, axis='y')
        M.cylinder((s1 - .045, FRONT + .5, 1.7), .012, .06, 'gold', seg=8, axis='x')   # coat hook
        if access:                                                                       # grab rails, accessible stall
            M.cylinder((hx + .06, ledge - .45, .8), .016, .6, 'gold', seg=12, axis='y')
            for ey in (ledge - .2, ledge - .7):
                M.cylinder((hx + .03, ey, .8), .012, .06, 'gold', seg=10, axis='x')
            M.cylinder((tx + .32, ledge - .4, .78), .016, .7, 'gold', seg=12, axis='y')    # drop-down rail
        fy0, fy1 = FRONT + .05, BACK
        F.box(((s0 + s1) / 2, (fy0 + fy1) / 2, .006), (s1 - s0, fy1 - fy0, .006), 'tile')   # floor over the mosaic
        for k in range(1, 4):
            F.box((s0 + (s1 - s0) * k / 4, (fy0 + fy1) / 2, .0095), (.006, fy1 - fy0, .002), 'grout')
            F.box(((s0 + s1) / 2, fy0 + (fy1 - fy0) * k / 4, .0095), (s1 - s0, .006, .002), 'grout')

def main():
    global SOFT
    out = HERE / 'Rooms70Build'; out.mkdir(exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    M = Mesh(MATS); SOFT = Mesh(SOFT_MATS); F = Mesh(FLOOR_MATS70)
    globals()['SOFT'] = SOFT
    security(M, SOFT, F); passage(M, SOFT, F); washrooms(M, SOFT, F)
    reps = {'hard': finish(M, 'SM_AP_P70Rooms', out, WORDS)}
    for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
    reps['soft'] = finish(SOFT, 'SM_AP_P70RoomsSoft', out, [])
    reps['floor'] = finish(F, 'SM_AP_P70RoomsFloor', out, [])
    for k, r in reps.items():
        (HERE / ('Rooms70%sBuild.json' % k.capitalize())).write_text(json.dumps(r, indent=1), encoding='utf-8')
    (HERE / 'Rooms71Faces.json').write_text(json.dumps(FACES, indent=1), encoding='utf-8')
    print('ROOMS70', {k: r['polygons'] for k, r in reps.items()}, FACES)


main()
