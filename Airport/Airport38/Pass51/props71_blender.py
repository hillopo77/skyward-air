"""Pass71: fire extinguishers and their cabinets, done properly (headless).

Player feedback on Pass70: the extinguishers and their stands were poorly placed and
poorly modelled; change everything about them. So: a wall-mounted cabinet (no more
floor stands in the middle of rooms) and a properly detailed extinguisher.

  SM_AP_P71Extinguisher   6 kg powder extinguisher, 0.6 m: smooth 48-segment body with
                          rounded shoulders and base, a cream label (red band, text
                          lines, three fire-class tiles), brass neck collar, rounded
                          valve head with a gauge (white face, green arc, red needle),
                          a shaped squeeze lever and carry handle, a yellow safety pin
                          ring, and a hose that curves down the right side as a smooth
                          chain to a horn nozzle clipped to the body
  SM_AP_P71ExtCabinet     wall-mounted, open-fronted (you can still grab it): red frame
                          on a cream back plate, lit interior, a low lip and a shelf at
                          0.48 m, and a red FIRE EXTINGUISHER sign above it with a flame
                          and extinguisher pictogram
Origins: both at floor level on the wall face, base centre; FRONT IS -Y (Blender), the
back (+Y) is flush with the wall. props71_editor.py mounts them on wall faces measured
in the game (Pass48/walls71_probe.py).
Usage: blender -b --factory-startup -P props71_blender.py
"""
import bpy, json, math, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'Pass48'))
import mesh48
from mesh48 import Mesh, export
exec(compile(open(HERE / 'cafe60_blender.py', encoding='utf-8').read().split('\ndef main():')[0], 'cafe60', 'exec'))
MATS = dict(red=('MI_AP_Red', (.72, .05, .04)), cream=('MI_AP_P34Cream', (.82, .78, .7)), black=('MI_AP_P36Black', (.03, .03, .03)),
            steel=('MI_AP_P27Steel', (.55, .57, .6)), rubber=('MI_AP_Rubber', (.05, .05, .05)), white=('MI_AP_WhiteMark', (.92, .92, .92)),
            gold=('MI_AP_P38AGold', (.72, .48, .11)), green=('MI_AP_P38ASage', (.3, .55, .3)), glow=('MI_AP_P51SignGlow', (1, .9, .7)),
            navy=('MI_AP_P38ANavy', (.02, .05, .06)), ink=('MI_AP_P38AText', (.9, .8, .5)))
SHELF = .48                                                         # the extinguisher stands on the cabinet shelf


def _catmull(pts, n=10):
    def cr(p0, p1, p2, p3, t):
        return tuple(.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t * t +
                           (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t ** 3) for k in range(3))
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        for j in range(n):
            out.append(cr(P[i - 1], P[i], P[i + 1], P[i + 2], j / n))
    out.append(pts[-1])
    return out


def tube(M, pts, r, mat, seg=14):
    """A real swept tube: a ring of verts carried along a smooth curve, joined by quads, capped."""
    from mathutils import Vector
    C = [Vector(q) for q in _catmull(pts)]
    rings, ref = [], Vector((0, 0, 1))
    for i, c in enumerate(C):
        t = (C[min(i + 1, len(C) - 1)] - C[max(i - 1, 0)]).normalized()
        if abs(t.dot(ref)) > .95:
            ref = Vector((1, 0, 0))
        u = t.cross(ref).normalized(); v = t.cross(u).normalized(); ref = v
        rings.append([M.bm.verts.new(c + (u * math.cos(2 * math.pi * k / seg) + v * math.sin(2 * math.pi * k / seg)) * r)
                      for k in range(seg)])
    for a, b in zip(rings, rings[1:]):
        for k in range(seg):
            M._face([a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]], mat)
    M._face(list(reversed(rings[0])), mat); M._face(rings[-1], mat)


def obox(M, c, s, rx=0.0, ry=0.0, rz=0.0, mat='steel'):
    """A box rotated about x, then y, then z (radians), centred at c."""
    from mathutils import Euler, Vector
    R = Euler((rx, ry, rz), 'XYZ').to_matrix()
    vs = [M.bm.verts.new(Vector(c) + R @ Vector((sx * s[0] / 2, sy * s[1] / 2, sz * s[2] / 2)))
          for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
    for f in [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]:
        M._face([vs[i] for i in f], mat)


def extinguisher(M):
    r, z0 = .078, 0.0
    M.cylinder((0, 0, z0 + .012), r - .006, .024, 'rubber', seg=48)                     # foot ring
    M.blob((0, 0, z0 + .05), r, 'red', squash=.45, subdiv=3)                             # rounded base
    M.cylinder((0, 0, z0 + .24), r, .38, 'red', seg=48, cap_top=False, cap_bottom=False) # body
    M.blob((0, 0, z0 + .43), r, 'red', squash=.6, subdiv=3)                              # domed shoulder
    M.cylinder((0, 0, z0 + .225), r + .0012, .15, 'cream', seg=48, cap_top=False, cap_bottom=False)   # label
    M.cylinder((0, 0, z0 + .292), r + .0016, .018, 'red', seg=48, cap_top=False, cap_bottom=False)    # label band
    for k, zz in enumerate((.262, .248, .236)):                                          # text lines, front
        M.box((0, -(r + .002), z0 + zz), (.07 - k * .015, .003, .006), 'black')
    for k, m in enumerate(('green', 'navy', 'gold')):                                    # fire-class tiles A B C
        M.box((-.03 + k * .03, -(r + .002), z0 + .195), (.022, .003, .022), m)
    M.cylinder((0, 0, z0 + .49), .026, .035, 'gold', seg=24)                             # brass collar
    M.cylinder((0, 0, z0 + .52), .03, .03, 'black', seg=24)                              # valve body
    M.blob((0, 0, z0 + .545), .034, 'black', squash=.7, subdiv=2)
    M.cylinder((0, -.04, z0 + .53), .024, .012, 'steel', seg=24, axis='y')               # gauge rim (front)
    M.cylinder((0, -.047, z0 + .53), .02, .004, 'white', seg=24, axis='y')               # gauge face
    M.box((.008, -.05, z0 + .536), (.014, .002, .004), 'green')                          # green zone
    M.box((-.004, -.051, z0 + .531), (.003, .002, .016), 'red')                          # needle
    obox(M, (0, .055, z0 + .575), (.032, .13, .012), rx=math.radians(14), mat='steel')     # squeeze lever, rising to the back
    obox(M, (0, .05, z0 + .552), (.028, .12, .01), rx=math.radians(4), mat='black')       # carry handle under it
    obox(M, (0, .112, z0 + .59), (.032, .012, .02), mat='steel')                          # lever tip
    M.cylinder((-.03, -.012, z0 + .57), .012, .004, 'gold', seg=16, axis='x')            # pin ring
    M.cylinder((-.02, -.012, z0 + .57), .003, .03, 'steel', seg=6, axis='x')             # pin
    tube(M, [(.028, 0, z0 + .525), (.07, 0, z0 + .51), (.096, -.004, z0 + .44), (.097, -.008, z0 + .32), (.094, -.01, z0 + .21)], .0105, 'black')
    for k, rr in enumerate((.013, .016, .019, .022)):                                    # horn nozzle
        M.cylinder((.094, -.01, z0 + .18 - k * .02), rr, .02, 'black', seg=16)
    M.box((.084, -.005, z0 + .2), (.016, .02, .03), 'steel')                             # nozzle clip


def cabinet(M):
    W, D, H, zb = .46, .26, .8, .42                                                      # outer box, bottom at 0.42 m
    zc = zb + H / 2
    M.box((0, -.006, zc + .12), (W + .12, .012, H + .5), 'cream')                         # back plate (flush to the wall)
    M.box((0, -.02, zc), (W, .02, H), 'white')                                            # interior back
    for sx in (-1, 1):                                                                    # red sides
        M.box((sx * (W / 2 - .015), -D / 2, zc), (.03, D, H), 'red')
    M.box((0, -D / 2, zb + H - .015), (W, D, .03), 'red')                                 # top
    M.box((0, -D / 2, zb + .015), (W, D, .03), 'red')                                     # bottom
    M.box((0, -D / 2, SHELF - .006), (W - .06, D - .02, .012), 'steel')                   # shelf the extinguisher stands on
    M.box((0, -D + .01, SHELF + .03), (W - .06, .012, .06), 'red')                        # low front lip
    M.box((0, -.05, zb + H - .045), (W - .08, .02, .015), 'glow')                         # light inside the top
    zs = zb + H + .12                                                                     # the sign above
    M.box((0, -.02, zs + .11), (W + .04, .025, .22), 'red')
    M.box((-.12, -.034, zs + .12), (.07, .004, .13), 'white')                             # extinguisher pictogram
    M.box((-.12, -.035, zs + .2), (.03, .004, .025), 'white')
    M.box((.02, -.034, zs + .1), (.05, .004, .07), 'white')                               # flame: three tongues
    M.box((.002, -.034, zs + .155), (.022, .004, .05), 'white'); M.box((.04, -.034, zs + .16), (.02, .004, .06), 'white')
    text('FIRE', (.13, -.034, zs + .155), -math.pi / 2, .05, 'white', depth=.002)
    text('EXTINGUISHER', (.07, -.034, zs + .04), -math.pi / 2, .03, 'white', depth=.002)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    out = HERE / 'Props71Build'; out.mkdir(exist_ok=True)
    items = []
    for name, fn, kg in (('SM_AP_P71Extinguisher', extinguisher, 6.0), ('SM_AP_P71ExtCabinet', cabinet, 0)):
        WORDS.clear()
        for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
        M = Mesh(MATS); fn(M)
        r = finish(M, name, out, list(WORDS))
        r['kg'] = kg; items.append(r)
    (HERE / 'Props71Build.json').write_text(json.dumps(dict(status='SUCCESS', items=items), indent=1), encoding='utf-8')
    print('PROPS71', [(i['asset'], i['polygons']) for i in items])


if __name__ == '__main__':
    main()
