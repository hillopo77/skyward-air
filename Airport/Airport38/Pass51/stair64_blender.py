"""Pass64: the cafe's gallery stair, turned to face the room (headless).

The old stair ran along the west glass from the south wall up to the gallery,
so it showed the cafe its side. This one is an L: the first flight faces into
the cafe (foot at x -42.9, rising west), a landing beside the glass, and a
second flight rising north onto the gallery at the old arrival point (x
-47.7..-45.3, y 25), so the gallery's balustrade opening still fits.
18 risers of 176 mm, 300 mm treads, 2.4 m wide; steel stringers, glass
balustrades with a steel handrail, a gold nosing strip at the foot, two posts
under the landing. Complex collision. World source metres, exported at the origin.
Usage: blender -b --factory-startup -P stair64_blender.py
"""
import bpy, json, sys
from mathutils import Vector
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'Pass48'))
from mesh48 import Mesh, export

MATS = dict(tread=('MI_AP_P34Cream', (.8, .75, .6)), steel=('MI_AP_P27Steel', (.5, .52, .54)),
            glass=('MI_AP_Glass39_Terminal', (.6, .7, .75)), gold=('MI_AP_Gold', (.72, .48, .11)),
            oak=('MI_AP_P43TOak', (.5, .31, .15)))
TOP = 3.17
N = 18
RISE = TOP / N
RUN = .3
W = 2.4
F1_FOOT, Y0, Y1 = -42.9, 20.2, 22.6            # flight 1: x from -42.9 west to -45.3, y 20.2..22.6
LX0, LX1 = -47.7, -45.3                        # landing and flight 2 x span


def bar(M, a, b, w, h, mat):
    """A straight bar of section w x h from point a to point b (any slope)."""
    a, b = Vector(a), Vector(b)
    d = (b - a).normalized()
    side = d.cross(Vector((0, 0, 1)))
    if side.length < 1e-6:
        side = Vector((1, 0, 0))
    side.normalize()
    up = side.cross(d).normalized()
    c = [a + side * sx * w / 2 + up * sz * h / 2 for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    e = [p + (b - a) for p in c]
    for i in range(4):
        j = (i + 1) % 4
        M.quad([tuple(c[i]), tuple(c[j]), tuple(e[j]), tuple(e[i])], mat)
    M.quad([tuple(p) for p in reversed(c)], mat); M.quad([tuple(p) for p in e], mat)


def pane(M, p0, p1, h, mat='glass'):
    """A sloped glass panel standing h above the line p0-p1 (both faces)."""
    a, b = Vector(p0), Vector(p1)
    q = [a, b, b + Vector((0, 0, h)), a + Vector((0, 0, h))]
    M.quad([tuple(v) for v in q], mat); M.quad([tuple(v) for v in reversed(q)], mat)


def rail(M, p0, p1, h=.95):
    pane(M, (p0[0], p0[1], p0[2] + .1), (p1[0], p1[1], p1[2] + .1), h - .15)
    bar(M, (p0[0], p0[1], p0[2] + h), (p1[0], p1[1], p1[2] + h), .05, .05, 'steel')


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    M = Mesh(MATS)
    # flight 1: faces the room, rises west to the landing
    for k in range(1, 9):
        x = F1_FOOT - (k - .5) * RUN
        M.box((x, (Y0 + Y1) / 2, k * RISE - .03), (RUN + .02, W, .06), 'tread')
        M.box((x + RUN / 2 - .01, (Y0 + Y1) / 2, k * RISE - RISE / 2), (.02, W - .04, RISE), 'tread')   # riser
    hl = 9 * RISE                                                                # landing height
    M.box(((LX0 + LX1) / 2, (Y0 + Y1) / 2, hl - .08), (LX1 - LX0, Y1 - Y0, .16), 'tread')
    M.box((LX1 + .01, (Y0 + Y1) / 2, hl - RISE / 2), (.02, W - .04, RISE), 'tread')
    # flight 2: rises north onto the gallery
    for k in range(1, 9):
        y = Y1 + (k - .5) * RUN
        M.box(((LX0 + LX1) / 2, y, hl + k * RISE - .03), (W, RUN + .02, .06), 'tread')
        M.box(((LX0 + LX1) / 2, y - RUN / 2 + .01, hl + k * RISE - RISE / 2), (W - .04, .02, RISE), 'tread')
    M.box(((LX0 + LX1) / 2, 25.0 - .01, TOP - RISE / 2), (W - .04, .02, RISE), 'tread')            # last riser
    # stringers
    for y in (Y0 + .03, Y1 - .03):
        bar(M, (F1_FOOT, y, -.05), (LX1, y, hl - .05), .04, .3, 'steel')
    for x in (LX0 + .03, LX1 - .03):
        bar(M, (x, Y1, hl - .05), (x, 25.0, TOP - .05), .04, .3, 'steel')
    # posts under the landing
    for x, y in ((LX0 + .15, Y0 + .15), (LX1 - .15, Y0 + .15), (LX0 + .15, Y1 - .15)):
        M.cylinder((x, y, hl / 2 - .08), .05, hl - .16, 'steel', seg=14)
    # balustrades
    rail(M, (F1_FOOT, Y0, 0), (LX1, Y0, hl))                        # flight 1, south side
    rail(M, (F1_FOOT, Y1, 0), (LX1, Y1, hl))                        # flight 1, north side
    rail(M, (LX1, Y0, hl), (LX0, Y0, hl))                           # landing, south
    rail(M, (LX0, Y0, hl), (LX0, Y1, hl))                           # landing, west (glass side)
    rail(M, (LX0, Y1, hl), (LX0, 25.0, TOP))                        # flight 2, west
    rail(M, (LX1, Y1, hl), (LX1, 25.0, TOP))                        # flight 2, east
    M.box((F1_FOOT + .12, (Y0 + Y1) / 2, .006), (.2, W, .012), 'gold')   # nosing strip at the foot
    obj = M.finish('SM_AP_P64CafeStair')
    out = HERE / 'StairBuild'; out.mkdir(exist_ok=True)
    fbx = out / 'SM_AP_P64CafeStair.fbx'
    export(obj, fbx)
    rep = dict(status='SUCCESS', asset=obj.name, fbx=str(fbx.resolve()), materials=[m.name for m in obj.data.materials],
               polygons=len(obj.data.polygons))
    (HERE / 'Stair64Build.json').write_text(json.dumps(rep, indent=1), encoding='utf-8')
    print('STAIR64', rep['polygons'])


main()
