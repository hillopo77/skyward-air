"""Pass46 / P46-006: rooftop plant for the terminal roof.

The roof is a 774-solid stepped union with nothing on it; seen from the flight
mode it reads as an unfinished model. A real terminal roof carries the
building's services, so this adds them, in one restrained steel-and-graphite
language:

  ahu        air-handling unit on steel dunnage and rubber pads, end louvre
             bank, panel battens, lifting lugs and a supply duct dropping
             through a curb into the roof below
  condenser  packaged condenser on rails with two guarded fans on top
  exhaust    mushroom exhaust fan on a curb (WC and cafe kitchen extract)
  gooseneck  vent pipe with a return bend
  hatch      roof access hatch on a curb with a three-sided safety rail
  walkway    rubber paver path from the hatch to the plant it serves
  tray       cable tray on rubber pedestals between units

Every unit is placed by plan_roof46.py on roof the survey measured as flat
under its whole footprint plus a margin, so nothing overhangs a step or edge.

Built in world (source) coordinates as one mesh and exported at the origin,
exactly like the project's other union meshes, so the importer's Y flip puts
it where v() would. Headless, factory-empty: the 614 MB master is not opened.

Usage: blender -b --factory-startup -P build_roof46.py -- <spec.json> <out_dir> <report.json>
"""
import bpy, bmesh, json, math, sys
from pathlib import Path

ARGS = sys.argv[sys.argv.index('--') + 1:]
SPEC, OUTDIR, REPORT = Path(ARGS[0]), Path(ARGS[1]), Path(ARGS[2])

MATS = {
    'MI_AP_P38BSteel': ((0.62, 0.64, 0.66, 1), 0.38, 0.55),
    'MI_AP_DarkSteel_001': ((0.10, 0.11, 0.12, 1), 0.45, 0.50),
    'MI_AP_P38ARubber': ((0.05, 0.05, 0.05, 1), 0.85, 0.0),
    'MI_AP_P38AHousing': ((0.80, 0.80, 0.78, 1), 0.50, 0.10),
}
ORDER = list(MATS)


def material(name):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    col, rough, metal = MATS[name]
    bsdf.inputs['Base Color'].default_value = col
    bsdf.inputs['Roughness'].default_value = rough
    if 'Metallic' in bsdf.inputs:
        bsdf.inputs['Metallic'].default_value = metal
    return m


class Builder:
    """Accumulates world-space parts into one bmesh, one slot per material."""

    def __init__(self):
        self.bm = bmesh.new()
        self.parts = 0

    def _xf(self, p, o):
        # local (x,y,z) about the unit origin, rotated by yaw, placed at o
        c, s = math.cos(o['yaw']), math.sin(o['yaw'])
        return (o['x'] + p[0] * c - p[1] * s, o['y'] + p[0] * s + p[1] * c,
                o['z'] + p[2])

    def box(self, o, centre, size, mat):
        hx, hy, hz = size[0] / 2, size[1] / 2, size[2] / 2
        vs = [self.bm.verts.new(self._xf((centre[0] + sx * hx, centre[1] + sy * hy,
                                          centre[2] + sz * hz), o))
              for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
        for q in [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1),
                  (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]:
            f = self.bm.faces.new([vs[i] for i in q])
            f.material_index = ORDER.index(mat)
        self.parts += 1

    def cyl(self, o, centre, r, h, mat, seg=20, axis='z'):
        ring0, ring1 = [], []
        for i in range(seg):
            a = 2 * math.pi * i / seg
            u, w = r * math.cos(a), r * math.sin(a)
            if axis == 'z':
                p0 = (centre[0] + u, centre[1] + w, centre[2] - h / 2)
                p1 = (centre[0] + u, centre[1] + w, centre[2] + h / 2)
            elif axis == 'x':
                p0 = (centre[0] - h / 2, centre[1] + u, centre[2] + w)
                p1 = (centre[0] + h / 2, centre[1] + u, centre[2] + w)
            else:
                p0 = (centre[0] + u, centre[1] - h / 2, centre[2] + w)
                p1 = (centre[0] + u, centre[1] + h / 2, centre[2] + w)
            ring0.append(self.bm.verts.new(self._xf(p0, o)))
            ring1.append(self.bm.verts.new(self._xf(p1, o)))
        idx = ORDER.index(mat)
        for i in range(seg):
            j = (i + 1) % seg
            self.bm.faces.new([ring0[i], ring0[j], ring1[j], ring1[i]]).material_index = idx
        self.bm.faces.new(list(reversed(ring0))).material_index = idx
        self.bm.faces.new(ring1).material_index = idx
        self.parts += 1

    def ring(self, o, centre, r_out, r_in, h, mat, seg=24):
        """A flat annulus - a fan guard rim."""
        idx = ORDER.index(mat)
        rings = []
        for rr in (r_out, r_in):
            for zz in (centre[2] - h / 2, centre[2] + h / 2):
                rings.append([self.bm.verts.new(self._xf(
                    (centre[0] + rr * math.cos(2 * math.pi * i / seg),
                     centre[1] + rr * math.sin(2 * math.pi * i / seg), zz), o))
                    for i in range(seg)])
        ob, ot, ib, it = rings
        for i in range(seg):
            j = (i + 1) % seg
            for a, b in ((ob, ot), (it, ib), (ot, it), (ib, ob)):
                self.bm.faces.new([a[i], a[j], b[j], b[i]]).material_index = idx
        self.parts += 1


# ---------------------------------------------------------------- unit types

def ahu(b, o):
    L, W, H = o.get('length', 3.6), o.get('width', 1.5), 1.35
    # Dunnage: two steel beams on rubber pads, carrying the unit clear of the
    # membrane, as plant is never set directly on a roof.
    for y in (-0.52, 0.52):
        b.box(o, (0, y, 0.12), (L + 0.5, 0.12, 0.16), 'MI_AP_DarkSteel_001')
        for x in (-(L + 0.3) / 2, 0, (L + 0.3) / 2):
            b.box(o, (x, y, 0.02), (0.26, 0.26, 0.04), 'MI_AP_P38ARubber')
    base = 0.20
    b.box(o, (0, 0, base + H / 2), (L, W, H), 'MI_AP_P38BSteel')
    b.box(o, (0, 0, base + H + 0.03), (L + 0.06, W + 0.06, 0.06), 'MI_AP_P38BSteel')
    # Panel battens on both long faces.
    n = max(2, int(L / 0.9))
    for i in range(1, n):
        x = -L / 2 + i * L / n
        for y in (-W / 2 - 0.012, W / 2 + 0.012):
            b.box(o, (x, y, base + H / 2), (0.05, 0.024, H - 0.06), 'MI_AP_DarkSteel_001')
    # Door handles on the service side.
    for i in range(n):
        x = -L / 2 + (i + 0.5) * L / n
        b.box(o, (x, -W / 2 - 0.03, base + H * 0.55), (0.14, 0.03, 0.03), 'MI_AP_DarkSteel_001')
    # Intake louvre bank on the +x end.
    b.box(o, (L / 2 + 0.03, 0, base + H / 2), (0.06, W - 0.1, H - 0.12), 'MI_AP_DarkSteel_001')
    for k in range(9):
        z = base + 0.12 + k * (H - 0.24) / 8
        b.box(o, (L / 2 + 0.085, 0, z), (0.07, W - 0.16, 0.025), 'MI_AP_P38BSteel')
    # Lifting lugs.
    for x in (-L / 2 + 0.25, L / 2 - 0.25):
        b.box(o, (x, 0, base + H + 0.10), (0.04, 0.16, 0.10), 'MI_AP_DarkSteel_001')
    # Supply duct off the -x end, turning down through a curb into the roof.
    b.box(o, (-L / 2 - 0.35, 0, base + H * 0.62), (0.70, 0.80, 0.50), 'MI_AP_P38BSteel')
    b.box(o, (-L / 2 - 0.55, 0, (base + H * 0.62 + 0.25 + 0.30) / 2),
          (0.50, 0.80, base + H * 0.62 + 0.25 - 0.30), 'MI_AP_P38BSteel')
    b.box(o, (-L / 2 - 0.55, 0, 0.15), (0.75, 1.05, 0.30), 'MI_AP_P38AHousing')
    for z in (0.62, base + H * 0.62):
        b.box(o, (-L / 2 - 0.55, 0, z), (0.54, 0.84, 0.035), 'MI_AP_DarkSteel_001')


def condenser(b, o):
    L, W, H = 2.2, 1.1, 0.95
    for y in (-0.42, 0.42):
        b.box(o, (0, y, 0.08), (L + 0.3, 0.10, 0.10), 'MI_AP_DarkSteel_001')
        for x in (-(L + 0.1) / 2, (L + 0.1) / 2):
            b.box(o, (x, y, 0.015), (0.2, 0.2, 0.03), 'MI_AP_P38ARubber')
    base = 0.13
    b.box(o, (0, 0, base + H / 2), (L, W, H), 'MI_AP_P38AHousing')
    # Coil faces: darker inset panels on the long sides.
    for y in (-W / 2 - 0.01, W / 2 + 0.01):
        b.box(o, (0, y, base + H * 0.45), (L - 0.2, 0.02, H * 0.7), 'MI_AP_DarkSteel_001')
    # Two fans on top: shroud, guard ring and cross bars.
    for x in (-L / 4, L / 4):
        b.cyl(o, (x, 0, base + H + 0.06), 0.42, 0.12, 'MI_AP_DarkSteel_001', seg=28)
        b.ring(o, (x, 0, base + H + 0.13), 0.42, 0.36, 0.02, 'MI_AP_P38BSteel')
        for a in (0, math.pi / 2):
            b.box(dict(o, x=o['x'], y=o['y'], yaw=o['yaw']),
                  (x, 0, base + H + 0.135), (0.80 if a == 0 else 0.02, 0.02 if a == 0 else 0.80, 0.02),
                  'MI_AP_P38BSteel')
        b.cyl(o, (x, 0, base + H + 0.14), 0.07, 0.03, 'MI_AP_P38BSteel', seg=12)


def exhaust(b, o):
    b.box(o, (0, 0, 0.16), (0.62, 0.62, 0.32), 'MI_AP_P38AHousing')
    b.cyl(o, (0, 0, 0.47), 0.21, 0.30, 'MI_AP_P38BSteel', seg=20)
    b.cyl(o, (0, 0, 0.66), 0.36, 0.10, 'MI_AP_P38BSteel', seg=24)
    b.cyl(o, (0, 0, 0.73), 0.30, 0.05, 'MI_AP_P38BSteel', seg=24)
    b.cyl(o, (0, 0, 0.60), 0.33, 0.04, 'MI_AP_DarkSteel_001', seg=24)


def gooseneck(b, o):
    b.cyl(o, (0, 0, 0.06), 0.16, 0.12, 'MI_AP_P38ARubber', seg=16)
    b.cyl(o, (0, 0, 0.37), 0.07, 0.62, 'MI_AP_P38BSteel', seg=14)
    # Return bend: round pipe across and a short downturn with a bird mesh.
    b.cyl(o, (0.15, 0, 0.68), 0.07, 0.44, 'MI_AP_P38BSteel', seg=14, axis='x')
    b.cyl(o, (0.30, 0, 0.58), 0.07, 0.20, 'MI_AP_P38BSteel', seg=14)
    b.cyl(o, (0.30, 0, 0.47), 0.075, 0.02, 'MI_AP_DarkSteel_001', seg=14)


def hatch(b, o):
    b.box(o, (0, 0, 0.18), (1.0, 1.0, 0.36), 'MI_AP_P38AHousing')
    b.box(o, (0, 0, 0.385), (1.06, 1.06, 0.05), 'MI_AP_P38BSteel')
    b.box(o, (0.47, 0, 0.42), (0.04, 0.6, 0.03), 'MI_AP_DarkSteel_001')
    # Safety rail round three sides, open on the walkway side (-y). The posts
    # stand outside the curb, so they rise from the roof on base plates.
    posts = [(-0.75, -0.55), (-0.75, 0.75), (0.75, 0.75), (0.75, -0.55)]
    for x, y in posts:
        b.cyl(o, (x, y, 0.56), 0.024, 1.10, 'MI_AP_P38BSteel', seg=10)
        b.box(o, (x, y, 0.01), (0.14, 0.14, 0.02), 'MI_AP_P38BSteel')
    for z in (0.55, 1.08):
        b.box(o, (-0.75, 0.10, z), (0.04, 1.30, 0.04), 'MI_AP_P38BSteel')
        b.box(o, (0.75, 0.10, z), (0.04, 1.30, 0.04), 'MI_AP_P38BSteel')
        b.box(o, (0, 0.75, z), (1.54, 0.04, 0.04), 'MI_AP_P38BSteel')


def walkway(b, z, points):
    """Rubber pavers along a polyline: 0.6 m tiles with 50 mm joints."""
    for k, ((x0, y0), (x1, y1)) in enumerate(zip(points, points[1:])):
        L = math.hypot(x1 - x0, y1 - y0)
        # Round up so the run has no gaps, then size each paver to its own
        # spacing less a 50 mm joint so neighbours never overlap and z-fight.
        # A segment's first paver after the first segment would sit on the
        # previous one's last, so it is skipped.
        n = max(1, math.ceil(L / 0.65))
        pitch = L / n
        o = dict(x=0.0, y=0.0, z=z, yaw=math.atan2(y1 - y0, x1 - x0))
        c, s = math.cos(o['yaw']), math.sin(o['yaw'])
        for i in range(0 if k == 0 else 1, n + 1):
            t = i / n
            px, py = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            # Builder rotates local coordinates by yaw; pass the world point
            # back through the inverse rotation so the paver lands on it.
            lx, ly = px * c + py * s, -px * s + py * c
            b.box(o, (lx, ly, 0.015), (max(0.3, pitch - 0.05), 0.6, 0.03),
                  'MI_AP_P38ARubber')


def tray(b, z, points):
    """Cable tray on rubber pedestals, 300 mm wide, every 1.5 m."""
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        yaw = math.atan2(y1 - y0, x1 - x0)
        o = dict(x=(x0 + x1) / 2, y=(y0 + y1) / 2, z=z, yaw=yaw)
        b.box(o, (0, 0, 0.215), (L, 0.30, 0.01), 'MI_AP_P38BSteel')
        for y in (-0.15, 0.15):
            b.box(o, (0, y, 0.25), (L, 0.01, 0.08), 'MI_AP_P38BSteel')
        n = max(1, int(L / 1.5))
        for i in range(n + 1):
            x = -L / 2 + i * L / n
            b.box(o, (x, 0, 0.05), (0.26, 0.26, 0.10), 'MI_AP_P38ARubber')
            b.box(o, (x, 0, 0.155), (0.04, 0.04, 0.11), 'MI_AP_DarkSteel_001')


UNITS = dict(ahu=ahu, condenser=condenser, exhaust=exhaust, gooseneck=gooseneck,
             hatch=hatch)


def main():
    spec = json.loads(SPEC.read_text(encoding='utf-8'))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = 'METRIC'
    bpy.context.scene.unit_settings.scale_length = 1.0
    OUTDIR.mkdir(parents=True, exist_ok=True)
    b = Builder()
    counts = {}
    for q in spec['units']:
        o = dict(q, yaw=math.radians(q.get('yaw', 0.0)))
        UNITS[q['type']](b, o)
        counts[q['type']] = counts.get(q['type'], 0) + 1
    for w in spec.get('walkways', []):
        walkway(b, w['z'], w['points'])
    for t in spec.get('trays', []):
        tray(b, t['z'], t['points'])
    name = 'SM_AP_P46RooftopPlant'
    mesh = bpy.data.meshes.new(name)
    b.bm.normal_update()
    b.bm.to_mesh(mesh)
    b.bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    for m in ORDER:
        obj.data.materials.append(material(m))
    for p in mesh.polygons:
        p.use_smooth = False
    bev = obj.modifiers.new('Bevel', 'BEVEL')
    bev.width = 0.004
    bev.segments = 1
    bev.limit_method = 'ANGLE'
    bev.angle_limit = math.radians(60)
    obj.location = (0, 0, 0)
    obj.rotation_euler = (0, 0, 0)
    for o in bpy.context.scene.objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    fbx = OUTDIR / (name + '.fbx')
    bpy.ops.export_scene.fbx(
        filepath=str(fbx), use_selection=True, apply_unit_scale=True,
        global_scale=1.0, apply_scale_options='FBX_SCALE_NONE',
        object_types={'MESH'}, use_mesh_modifiers=True,
        mesh_smooth_type='FACE', bake_space_transform=False,
        axis_forward='Y', axis_up='Z')
    dg = bpy.context.evaluated_depsgraph_get()
    tris = sum(len(p.vertices) - 2 for p in obj.evaluated_get(dg).data.polygons)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTDIR / 'rooftop_plant46.blend'))
    REPORT.write_text(json.dumps(dict(
        status='SUCCESS', blender=bpy.app.version_string, asset=name,
        fbx=str(fbx.resolve()), materials=ORDER, units=counts,
        walkways=len(spec.get('walkways', [])), trays=len(spec.get('trays', [])),
        parts=b.parts, triangles=tris), indent=1), encoding='utf-8')
    print('ROOF46 BUILD SUCCESS', counts, tris)


main()
