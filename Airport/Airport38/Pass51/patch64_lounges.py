"""Pass64 patch: replace a08()/a07() in lounges62_blender.py with the Viewing
Terrace and the Wave; record where every waiting passenger sits."""
import ast
from pathlib import Path

p = Path(__file__).resolve().parent / 'lounges62_blender.py'
s = p.read_text(encoding='utf-8')
i = s.index('def a08(M, F):')
j = s.index('\nDECK = 3.17\n')
new = '''SEATS = {}          # Pass64: passenger -> [x, y, z, rotation_degrees, seat label]


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
    for k, top in enumerate((.45, .90, 1.35)):
        xf = -29.15 - k * .9                                           # front edge of tier k
        M.box((xf - .45, yc, top / 2), (.9, L, top), 'oak')
        M.box((xf - .02, yc, top - .03), (.04, L, .02), 'glow')        # light strip under the nosing
        SOFT.box((xf - .32, yc, top + .045), (.6, L - .1, .09), 'teal')
    SOFT.box((xw + .1, yc, 1.35 + .35), (.16, L - .1, .5), 'teal')    # back cushion against the wall
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
    px, py = -26.3, 32.85
    M.cylinder((px, py, .55), .32, 2.2, 'cream', seg=24, axis='x')    # fuselage
    M.cylinder((px - 1.11, py, .55), .3, .02, 'teal', seg=24, axis='x')
    M.box((px + .1, py, .5), (.7, 2.4, .06), 'oak')                   # wings
    M.box((px + 1.0, py, .95), (.4, .06, .6), 'oak')                  # fin
    M.box((px + 1.0, py, .62), (.3, .9, .05), 'oak')                  # tailplane
    for dy in (-.6, .6):
        M.cylinder((px + .1, py + dy, .15), .08, .3, 'black', seg=12)
    M.box((px - .35, py - .45, .2), (.4, .3, .4), 'oak')              # step
    armchair(M, -25.0, 30.55, math.pi / 2)                            # parents watch the kids
    armchair(M, -26.3, 30.55, math.pi / 2)
    side_table(M, -27.4, 30.6)
    TREES.extend([(-31.15, 33.2, .58, .4)])
    planter(M, -31.15, 33.2, .48, .58)


def a07(M, F):
    """A07 'The Wave'. One sinuous oak bench curving through the room like the
    wave ceiling: seats both sides of an upholstered spine, the north side
    facing the apron window and the aircraft, the south side the gate. The
    boarding route (y 0.6..4.5) and the desk stay clear; the window stays open."""
    gate_sign((-18.5, 9.8, 4.05), (0, -1), 'A07', 'AZURE BAY  ·  BOARDING')
    rug(F, -22.5, -14.6, 5.4, 9.7)

    def c(x):
        return 7.55 + .7 * math.sin(2 * math.pi * (x + 22.0) / 7.0)
    x0, x1, n = -21.7, -15.3, 32
    pts = [(x0 + (x1 - x0) * k / n, c(x0 + (x1 - x0) * k / n)) for k in range(n + 1)]
    for k in range(n):
        (xa, ya), (xb, yb) = pts[k], pts[k + 1]
        mx, my = (xa + xb) / 2, (ya + yb) / 2
        seg = math.hypot(xb - xa, yb - ya) + .015
        rot = math.atan2(yb - ya, xb - xa)
        M.box((mx, my, .2), (seg, 1.1, .4), 'oak', rot=rot)             # plinth
        M.box((mx, my, .7), (seg, .18, .6), 'oak', rot=rot)             # spine
        nx, ny = -math.sin(rot), math.cos(rot)
        for side in (1, -1):
            SOFT.box((mx + nx * side * .33, my + ny * side * .33, .45), (seg + .01, .44, .1), 'teal', rot=rot)
            SOFT.box((mx + nx * side * .13, my + ny * side * .13, .78), (seg + .01, .1, .42), 'cushion', rot=rot)
    for (xe, ye) in (pts[0], pts[-1]):                                  # rounded ends
        M.cylinder((xe, ye, .2), .55, .4, 'oak', seg=28)
        SOFT.cylinder((xe, ye, .45), .5, .1, 'teal', seg=28)
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

'''
s = s[:i] + new + s[j:]
s = s.replace("FLOOR_MATS2 = dict(rug=('MI_AP_P38ASage', (.4, .5, .4)),",
              "FLOOR_MATS2 = dict(mat=('MI_AP_P27Teal', (.05, .3, .3)), rug=('MI_AP_P38ASage', (.4, .5, .4)),")
s = s.replace("    (HERE / 'Lounge62Trees.json').write_text(json.dumps(TREES), encoding='utf-8')",
              "    (HERE / 'Lounge62Trees.json').write_text(json.dumps(TREES), encoding='utf-8')\n"
              "    (HERE / 'Lounge64Seats.json').write_text(json.dumps(SEATS, indent=1), encoding='utf-8')")
ast.parse(s)
p.write_text(s, encoding='utf-8')
print('patched', 'mat=' in s, 'Lounge64Seats' in s)
