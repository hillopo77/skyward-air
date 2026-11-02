"""Pass54: sun shafts through the clerestory windows (headless).

This renderer (DirectX 11, no Lumen) shows volumetric fog only as an even
haze, not as beams, so the shafts are built: for every clerestory band the sun
actually shines through (the wall faces the sun), each 1.6 m bay gets the
four side faces of the window opening swept along the real sun direction
("Airport daylight", pitch -40, yaw -40) down to the floor, with the additive
M_AP_P54SunShaft (raymat54_editor.py), fading from the glass to nothing before
the floor. They line up with the sun patches the same sun throws on the floor.
Usage: blender -b --factory-startup -P rays54_blender.py
"""
import bpy, json, math, sys
from mathutils import Vector
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'Pass48'))
from mesh48 import Mesh, export

SPEC = json.loads((HERE.parent / 'Pass50' / 'Hall50.json').read_text(encoding='utf-8'))
P, Y = math.radians(-40), math.radians(-40)                 # sun actor rotation (UE)
SUN = Vector((math.cos(P) * math.cos(Y), -math.cos(P) * math.sin(Y), math.sin(P)))   # travel, source frame
GLASS = .6                                                    # clear opening inside each 1.6 m bay
INSET = .3                                                    # start just inside the glass
REACH = .9                                                    # stop at 90 % of the way to the floor


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    M = Mesh(dict(ray=('M_AP_P54SunShaft', (1, .8, .5))))
    n = 0
    for H in SPEC['halls']:
        x0, x1, y0, y1 = H['hall']
        for side, inward in (('W', Vector((1, 0, 0))), ('E', Vector((-1, 0, 0))), ('S', Vector((0, 1, 0))), ('N', Vector((0, -1, 0)))):
            if inward.dot(SUN) <= .05:
                continue                                       # this wall faces away from the sun
            z0, z1 = H.get('clerestory_side', {}).get(side, H['clerestory'])
            along = Vector((0, 1, 0)) if side in 'WE' else Vector((1, 0, 0))
            a0, a1 = (y0, y1) if side in 'WE' else (x0, x1)
            wall = {'W': x0, 'E': x1, 'S': y0, 'N': y1}[side]
            bays = int((a1 - a0) // SPEC['bay'])
            for k in range(bays):
                c = a0 + (a1 - a0) * (k + .5) / bays
                if min(c - a0, a1 - c) < .9:
                    continue                                   # corner bays: the sweep would hit the side wall
                base = (Vector((wall, c, 0)) if side in 'WE' else Vector((c, wall, 0))) + inward * INSET
                corners = [base + along * s * GLASS / 2 + Vector((0, 0, z)) for s, z in ((-1, z0 + .1), (1, z0 + .1), (1, z1 - .1), (-1, z1 - .1))]
                t = REACH * (z0 + .1) / -SUN.z                 # sweep length: lowest edge to near the floor
                far = [p + SUN * t for p in corners]
                for i in range(4):
                    j = (i + 1) % 4
                    M.quad_uv([tuple(corners[i]), tuple(corners[j]), tuple(far[j]), tuple(far[i])],
                              [(0, 0), (1, 0), (1, 1), (0, 1)], 'ray')
                n += 1
    obj = M.finish('SM_AP_P54SunShafts')
    for p in obj.data.polygons:
        p.use_smooth = False
    out = HERE / 'RayBuild'; out.mkdir(exist_ok=True)
    fbx = out / 'SM_AP_P54SunShafts.fbx'
    export(obj, fbx)
    rep = dict(status='SUCCESS', asset=obj.name, fbx=str(fbx.resolve()), materials=['M_AP_P54SunShaft'],
               polygons=len(obj.data.polygons), shafts=n, sun=[round(v, 3) for v in SUN])
    (HERE / 'Rays54Build.json').write_text(json.dumps(rep, indent=1), encoding='utf-8')
    print('RAYS54', n)


main()
