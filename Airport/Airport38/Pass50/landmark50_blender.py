"""Pass50: landmarks for the approach (headless).

  rooftop sign   'SKYWARD AIR' in gold, ~1.1 m capitals standing on the landside
                 hall roof behind its west parapet, facing the road, on a steel
                 frame
  'Departure'    a 10 x 4 m reflecting pool in a stone coping on the south lawn,
                 with a 3.6 m gold paper plane climbing out of it on a raked
                 steel mast: the Flock from the hall, at landscape scale
Positions come from Landmarks50.json (the pool where Ground50.json found open,
level ground). World source coordinates, exported at the origin.
Usage: blender -b --factory-startup -P landmark50_blender.py
"""
import bpy, json, math, sys
from mathutils import Vector
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'Pass48'))
from mesh48 import Mesh, export

SPEC = json.loads((HERE / 'Landmarks50.json').read_text(encoding='utf-8'))
MATS = dict(gold=('MI_AP_P38AGold', (.72, .48, .11)), steel=('MI_AP_P27Steel', (.5, .52, .54)),
            stone=('MI_AP_P34Cream', (.72, .66, .53)), basin=('MI_AP_P38ANavy', (.02, .05, .06)),
            water=('MI_AP_Glass39_Terminal', (.2, .3, .35)), dark=('MI_AP_DarkSteel', (.1, .11, .12)))


def sign(M, words):
    s = SPEC['sign']
    x, y, z = s['x'], s['y'], s['z']
    cu = bpy.data.curves.new('sky', 'FONT'); cu.body = s['text']
    cu.font = bpy.data.fonts.load('C:/Windows/Fonts/segoeuib.ttf', check_existing=True)
    cu.size = s['size']; cu.align_x = 'CENTER'; cu.align_y = 'BOTTOM'; cu.extrude = .06; cu.space_character = 1.08
    o = bpy.data.objects.new('sky', cu); o.location = (x, y, z + .05)
    o.rotation_euler = (math.pi / 2, 0, -math.pi / 2)                 # faces -x (the road), reads toward -y
    cu.materials.append(bpy.data.materials.get(MATS['gold'][0]) or bpy.data.materials.new(MATS['gold'][0]))
    bpy.context.scene.collection.objects.link(o); words.append(o)
    bpy.context.view_layer.update()
    ys = [(o.matrix_world @ Vector(c)).y for c in o.bound_box]
    zs = [(o.matrix_world @ Vector(c)).z for c in o.bound_box]
    y0, y1, top = min(ys) - .3, max(ys) + .3, max(zs)                 # frame sized to the lettering
    # Pass51: a navy board behind the letters, so from inside the hall the sign
    # is not read back to front through the clerestory.
    M.box((x + .2, (y0 + y1) / 2, (z + top) / 2 + .05), (.04, y1 - y0, top - z + .3), 'basin')
    for zz in (z + .25, top - .15):                                    # rails behind the letters
        M.box((x + .12, (y0 + y1) / 2, zz), (.06, y1 - y0, .06), 'steel')
    for k in range(6):
        yy = y0 + k * (y1 - y0) / 5
        M.box((x + .12, yy, (z - .3 + top) / 2), (.06, .06, top - z + .3), 'steel')
        M.box((x + .4, yy, z - .3), (.6, .06, .06), 'steel')           # raking foot to the roof
    return y0, y1


def paper_plane(M, x, y, z, yaw, pitch, s, mat):
    c, sn, cp, sp = math.cos(yaw), math.sin(yaw), math.cos(pitch), math.sin(pitch)

    def P(lx, ly, lz):
        lx, lz = lx * cp - lz * sp, lx * sp + lz * cp                  # nose up by pitch
        return (x + s * (lx * c - ly * sn), y + s * (lx * sn + ly * c), z + s * lz)
    nose, tail = P(.5, 0, 0), P(-.5, 0, 0)
    for side in (1, -1):
        wing = [nose, P(-.5, .32 * side, .06), tail]
        M.quad(wing if side > 0 else list(reversed(wing)), mat)
        M.quad(list(reversed(wing)) if side > 0 else wing, mat)
    keel = [nose, tail, P(-.45, 0, -.12)]
    M.quad(keel, mat); M.quad(list(reversed(keel)), mat)


def pool(M):
    p = SPEC['pool']
    cx, cy, g, L, W = p['x'], p['y'], p['ground'], p['length'], p['width']
    h, cw = .45, .35
    # coping: four stone kerbs round the basin
    M.box((cx, cy - W / 2 - cw / 2, g + h / 2), (L + 2 * cw, cw, h), 'stone')
    M.box((cx, cy + W / 2 + cw / 2, g + h / 2), (L + 2 * cw, cw, h), 'stone')
    M.box((cx - L / 2 - cw / 2, cy, g + h / 2), (cw, W, h), 'stone')
    M.box((cx + L / 2 + cw / 2, cy, g + h / 2), (cw, W, h), 'stone')
    M.box((cx, cy, g + .05), (L, W, .1), 'basin')                     # dark basin floor
    M.quad([(cx - L / 2, cy - W / 2, g + .36), (cx + L / 2, cy - W / 2, g + .36),
            (cx + L / 2, cy + W / 2, g + .36), (cx - L / 2, cy + W / 2, g + .36)], 'water')
    # 'Departure': a raked mast from the water to a big gold paper plane.
    bx, by = cx + L * .18, cy
    tx, ty, tz = bx - 1.6, by, g + 4.6
    r = .05                                                          # raked square mast, base in the water
    b0 = [(bx - r, by - r, g + .3), (bx + r, by - r, g + .3), (bx + r, by + r, g + .3), (bx - r, by + r, g + .3)]
    b1 = [(tx - r, ty - r, tz), (tx + r, ty - r, tz), (tx + r, ty + r, tz), (tx - r, ty + r, tz)]
    for k in range(4):
        M.quad([b0[k], b0[(k + 1) % 4], b1[(k + 1) % 4], b1[k]], 'steel')
    M.quad(list(b1), 'steel')
    paper_plane(M, tx, ty, tz + .2, math.pi, math.radians(22), 3.6, 'gold')


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    M = Mesh(MATS)
    words = []
    sign(M, words)
    pool(M)
    obj = M.finish('SM_AP_P50Landmarks')
    bpy.ops.object.select_all(action='DESELECT')
    for o in words:
        o.select_set(True)
    bpy.context.view_layer.objects.active = words[0]
    bpy.ops.object.convert(target='MESH')
    for o in words + [obj]:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = obj.data.name = 'SM_AP_P50Landmarks'
    out = HERE / 'LandmarkBuild'; out.mkdir(exist_ok=True)
    fbx = out / 'SM_AP_P50Landmarks.fbx'
    export(obj, fbx)
    rep = dict(status='SUCCESS', asset=obj.name, fbx=str(fbx.resolve()), materials=[m.name for m in obj.data.materials],
               polygons=len(obj.data.polygons))
    (HERE / 'Landmarks50Build.json').write_text(json.dumps(rep, indent=1), encoding='utf-8')
    print('LANDMARK50', rep['polygons'])


main()
