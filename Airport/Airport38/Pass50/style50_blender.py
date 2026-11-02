"""Pass50: polished stylised tree and car, to replace the lollipop trees and box cars.

The characters are soft and rounded; the old trees (one blob on a stick)
and the car-park cars (stacked boxes) were the crudest models left in view.
  SM_AP_P50Tree        6.8 m tree: tapered trunk that forks into three
                       limbs, canopy of eleven soft foliage masses (smooth
                       shaded, gently lumpy) in two greens, lighter on top
  SM_AP_P50Car_<paint> 4.3 m hatchback: one rounded body (bevelled side
                       profile), tinted glasshouse, painted roof, bumpers,
                       lamps, wheels with hubs; one mesh per paint colour
All built at the origin (car nose +x, wheels on z 0; tree on z 0) and placed
as actors by Pass48/import_mesh48.py. Each mesh writes a build report in
StyleBuild/ for the importer. Headless.
Usage: blender -b --factory-startup -P style50_blender.py
"""
import bpy, bmesh, json, math, random
from mathutils import Vector, noise
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / 'StyleBuild'
R = random.Random(50)
PAINTS = dict(ivory='MI_AP_Ivory', steel='MI_AP_Steel', navy='MI_AP_P38ANavy', red='MI_AP_P36Terracotta',
              dark='MI_AP_DarkSteel', teal='MI_AP_Teal', yellow='MI_AP_Gold')


def obj_from(bm, name, mats):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m in mats:
        me.materials.append(bpy.data.materials.get(m) or bpy.data.materials.new(m))
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    return o


def prism(bm, profile, y0, y1, mat, bevel, segs=3):
    """Extrude a side profile [(x, z), ...] across y0..y1, bevel every edge, smooth."""
    pre = set(bm.faces)
    a = [bm.verts.new((x, y0, z)) for x, z in profile]
    b = [bm.verts.new((x, y1, z)) for x, z in profile]
    n = len(profile)
    faces = [bm.faces.new(a), bm.faces.new(list(reversed(b)))]
    for i in range(n):
        j = (i + 1) % n
        faces.append(bm.faces.new([a[i], a[j], b[j], b[i]]))
    bmesh.ops.recalc_face_normals(bm, faces=faces)
    edges = list({e for f in faces for e in f.edges})
    res = bmesh.ops.bevel(bm, geom=edges + list({v for f in faces for v in f.verts}), offset=bevel, segments=segs,
                          profile=.5, affect='EDGES', clamp_overlap=True)
    for f in bm.faces:                         # bevel rebuilds faces: tag everything this prism added
        if f not in pre:
            f.material_index = mat; f.smooth = True


def cyl(bm, c, r, w, mat, seg=20, axis_y=True, smooth=True):
    ring = []
    for s in (-1, 1):
        ring.append([bm.verts.new((c[0] + r * math.cos(2 * math.pi * k / seg), c[1] + s * w / 2, c[2] + r * math.sin(2 * math.pi * k / seg)))
                     for k in range(seg)])
    fs = [bm.faces.new([ring[0][k], ring[0][(k + 1) % seg], ring[1][(k + 1) % seg], ring[1][k]]) for k in range(seg)]
    for f in fs:
        f.smooth = smooth
    fs += [bm.faces.new(list(reversed(ring[0]))), bm.faces.new(ring[1])]
    for f in fs:
        f.material_index = mat
    bmesh.ops.recalc_face_normals(bm, faces=fs)


def box(bm, c, s, mat):
    r = bmesh.ops.create_cube(bm, size=1.0)
    for v in r['verts']:
        v.co = Vector((c[0] + v.co.x * s[0], c[1] + v.co.y * s[1], c[2] + v.co.z * s[2]))
    for f in {f for v in r['verts'] for f in v.link_faces}:
        f.material_index = mat


def car(paint):
    mats = [PAINTS[paint], 'MI_AP_P43TInk', 'MI_AP_Rubber', 'MI_AP_Steel', 'MI_AP_WhiteLED', 'MI_AP_RedLED', 'MI_AP_DarkSteel']
    bm = bmesh.new()
    body = [(-2.15, .24), (2.12, .24), (2.15, .6), (1.95, .78), (1.15, .9), (-1.8, .94), (-2.15, .84)]
    prism(bm, body, -.89, .89, 0, .1)
    glass = [(1.1, .88), (.32, 1.36), (-1.25, 1.36), (-1.88, .92)]
    prism(bm, glass, -.8, .8, 1, .05, segs=2)
    roof = [(.3, 1.34), (-1.22, 1.34), (-1.24, 1.43), (.26, 1.43)]
    prism(bm, roof, -.79, .79, 0, .03, segs=2)
    for bx in (2.12, -2.12):                                   # bumpers
        box(bm, (bx, 0, .34), (.14, 1.78, .16), 6)
    for ly in (.6, -.6):
        box(bm, (2.13, ly, .66), (.06, .32, .1), 4)            # head lamps
        box(bm, (-2.14, ly, .76), (.06, .28, .1), 5)           # tail lamps
    for wx in (1.38, -1.35):
        for wy in (.8, -.8):
            cyl(bm, (wx, wy, .32), .32, .22, 2)
            cyl(bm, (wx, wy + (.01 if wy > 0 else -.01), .32), .19, .22, 3, seg=16)
    return obj_from(bm, 'SM_AP_P50Car_' + paint.capitalize(), mats)


def tree():
    mats = ['MI_AP_Bark', 'MI_AP_Leaf', 'MI_AP_LightLeaf']
    bm = bmesh.new()

    def limb(p0, p1, r0, r1, seg=10):
        d = (p1 - p0)
        axis = d.normalized()
        side = axis.cross(Vector((0, 0, 1)) if abs(axis.z) < .95 else Vector((1, 0, 0))).normalized()
        up = side.cross(axis)
        rings = []
        for t, r in ((0, r0), (1, r1)):
            c = p0 + d * t
            rings.append([bm.verts.new(c + (side * math.cos(2 * math.pi * k / seg) + up * math.sin(2 * math.pi * k / seg)) * r)
                          for k in range(seg)])
        for k in range(seg):
            f = bm.faces.new([rings[0][k], rings[0][(k + 1) % seg], rings[1][(k + 1) % seg], rings[1][k]])
            f.material_index = 0; f.smooth = True
    base, fork = Vector((0, 0, -.05)), Vector((.08, .05, 2.5))
    limb(base, fork, .2, .13)
    tips = []
    for k in range(3):
        a = 2 * math.pi * k / 3 + .4
        tip = Vector((1.25 * math.cos(a), 1.25 * math.sin(a), 4.1 + .3 * k))
        limb(fork, tip, .12, .05)
        tips.append(tip)
    # Canopy: soft lumpy masses around a dome, lighter ones on top.
    masses = [(Vector((0, 0, 5.0)), 1.7, 2)] + [(t + Vector((0, 0, .4)), 1.25, 1) for t in tips]
    for k in range(7):
        a = 2 * math.pi * k / 7 + R.uniform(-.2, .2)
        rr = R.uniform(1.4, 1.9)
        masses.append((Vector((rr * math.cos(a), rr * math.sin(a), R.uniform(3.9, 4.8))), R.uniform(.95, 1.25), 1))
    for c, r, mat in masses:
        res = bmesh.ops.create_icosphere(bm, subdivisions=3, radius=r)
        vs = res['verts']
        for v in vs:
            n = v.co.normalized()
            lump = 1 + .13 * noise.noise(n * 1.8 + c * .37) + .05 * noise.noise(n * 5.0 + c)
            v.co = c + v.co * lump * Vector((1, 1, .8))
        top = c.z > 4.7
        for f in {f for v in vs for f in v.link_faces}:
            f.material_index = 2 if (top or f.calc_center_median().z > c.z + .35 * r) else 1
            f.smooth = True
    return obj_from(bm, 'SM_AP_P50Tree', mats)


def export(o):
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
    fbx = OUT / (o.name + '.fbx')
    bpy.ops.export_scene.fbx(filepath=str(fbx), use_selection=True, apply_unit_scale=True, global_scale=1.0,
                             apply_scale_options='FBX_SCALE_NONE', object_types={'MESH'}, use_mesh_modifiers=True,
                             mesh_smooth_type='FACE', bake_space_transform=False, axis_forward='Y', axis_up='Z')
    rep = dict(status='SUCCESS', asset=o.name, fbx=str(fbx.resolve()), materials=[m.name for m in o.data.materials],
               polygons=len(o.data.polygons))
    (OUT / (o.name + '.json')).write_text(json.dumps(rep, indent=1), encoding='utf-8')
    return rep


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    out = [export(tree())]
    for p in PAINTS:
        out.append(export(car(p)))
    print('STYLE50', [(r['asset'], r['polygons']) for r in out])


main()
