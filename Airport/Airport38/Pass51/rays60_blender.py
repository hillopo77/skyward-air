"""Pass60: sun shafts through the cafe's west glass (headless).

Volumetric fog on this renderer (DirectX 11) shows only as an even haze, never
as beams (re-tested in the cafe in Pass60 at finer fog resolution). So the
shafts are built, but only where sunlight really enters: the cafe's west glass
(x -49, y 16-34, glazed 1.0-6.66 m). The glass is cut into 1.25 m bands with
gaps for the frame; each band is swept along the real sun direction ('Airport
daylight', pitch -40, yaw -40) until it reaches the floor, or the gallery deck
top (z 3.17) for bands above the deck, so every shaft ends on the patch the
same sun bakes onto that surface; (Pass62) each ray stops at the first
surface it meets: floor, gallery deck top, north glass or east wall. M_AP_P60SunShaft (raymat60_editor.py) fades
in at the glass, out at the far end, softly at the sides and wherever a shaft
meets a surface.
Usage: blender -b --factory-startup -P rays60_blender.py
"""
import bpy, json, math, sys
from mathutils import Vector
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'Pass48'))
from mesh48 import Mesh, export

_SUN = json.loads((HERE / 'Bake55.json').read_text(encoding='utf-8'))['sun'].get('rotation', [-40, -40])
P, Y = math.radians(_SUN[0]), math.radians(_SUN[1])   # pitch, yaw of 'Airport daylight' (Pass62: golden hour)
SUN = Vector((math.cos(P) * math.cos(Y), -math.cos(P) * math.sin(Y), math.sin(P)))
GLASS_X, Y0, Y1 = -48.9, 16.2, 33.8
DECK = dict(x=(-49, -41), y=(25.0, 34.0), under=2.87, top=3.17)
BAND, GAP = 1.25, .3


def land(p, floor_z):
    """Distance along the sun from p to the first surface it meets: the floor
    (floor_z), the gallery deck top, the north glass or the east wall."""
    ts = [(p.z - floor_z) / -SUN.z]
    t = (p.z - DECK['top']) / -SUN.z                    # the deck top, if the ray is over it there
    q = p + SUN * t
    if t > 0 and DECK['x'][0] <= q.x <= DECK['x'][1] and DECK['y'][0] <= q.y <= DECK['y'][1]:
        ts.append(t)
    if SUN.y > 0:
        ts.append((33.9 - p.y) / SUN.y)
    if SUN.x > 0:
        ts.append((-32.1 - p.x) / SUN.x)
    return max(.1, min(ts))


def sweep(M, y0, y1, z0, z1, floor_z):
    corners = [Vector((GLASS_X, y0, z0)), Vector((GLASS_X, y1, z0)), Vector((GLASS_X, y1, z1)), Vector((GLASS_X, y0, z1))]
    far = [p + SUN * land(p, floor_z) for p in corners]   # each corner ends on what it hits
    for i in range(4):
        j = (i + 1) % 4
        M.quad_uv([tuple(corners[i]), tuple(corners[j]), tuple(far[j]), tuple(far[i])], [(0, 0), (1, 0), (1, 1), (0, 1)], 'ray')


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    M = Mesh(dict(ray=('M_AP_P60SunShaft', (1, .8, .5))))
    n = 0
    y = Y0
    while y + BAND <= Y1 + 1e-6:
        y0, y1 = y, y + BAND
        if y1 <= DECK['y'][0]:
            sweep(M, y0, y1, 1.1, 6.55, 0.0); n += 1                      # open floor
        elif y0 >= DECK['y'][0]:
            sweep(M, y0, y1, 1.1, DECK['under'] - .1, 0.0); n += 1        # under the deck
            sweep(M, y0, y1, DECK['top'] + .9, 6.55, DECK['top']); n += 1  # over the gallery (above the rail)
        y += BAND + GAP
    obj = M.finish('SM_AP_P60SunShafts')
    for p in obj.data.polygons:
        p.use_smooth = False
    out = HERE / 'RayBuild'; out.mkdir(exist_ok=True)
    fbx = out / 'SM_AP_P60SunShafts.fbx'
    export(obj, fbx)
    rep = dict(status='SUCCESS', asset=obj.name, fbx=str(fbx.resolve()), materials=['M_AP_P60SunShaft'],
               polygons=len(obj.data.polygons), shafts=n, sun=[round(v, 3) for v in SUN])
    (HERE / 'Rays60Build.json').write_text(json.dumps(rep, indent=1), encoding='utf-8')
    print('RAYS60', n)


main()
