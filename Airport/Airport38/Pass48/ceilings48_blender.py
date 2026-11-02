"""Pass48 makeover: oak baffle ceilings and a new lighting scheme.

Every public room gets a field of oak baffles under its ceiling (45 mm x
150 mm, 250 mm pitch, along the room's long axis), the warm-timber ceiling of
a modern terminal. The rows where the room's lights stand become continuous
light channels: a dark housing with an opal strip, so the existing rect
lights now sit in visible linear fittings. Each baffle runs only over the
free intervals the survey traced along its own line (Survey48.json), so none
touches a wall, partition, sign or rod.

The old fittings (one merged mesh, hidden by the level script) are replaced
everywhere else too:
  cafe        light channels in its 4.4 m and 6.8 m ceilings, three large
              oak drum pendants over the tables, a round downlight under the
              gallery
  service     flush linear lights (washrooms, staff, baggage, exit link)
  forecourt   flush linear lights in the canopy soffit

Pass49: rooms with a 'wave' in Ceilings48.json get wave baffles instead of
flat ones: each baffle's underside follows a long, soft swell (crests curve
gently from line to line), so the ceiling reads as a rolling timber surface
rather than hard parallel stripes. The swell fades to the flat 150 mm baffle
at every room edge, every span end, beside every light channel and wherever
the survey's deeper traces ('bands') found anything at that height. Rooms
meet with flat baffles, and straight-baffle corridors blend into wave rooms
with no step.

The bottom of every flat baffle sits above the light actors (ceiling -
0.169); wave baffles only deepen 0.25 m or more away from a light row. World source coordinates, exported at the origin.
Headless. Usage:
  blender -b --factory-startup -P ceilings48_blender.py -- <out_dir> <report.json>
"""
import bpy, bmesh, json, math, sys
from pathlib import Path

ARGS = sys.argv[sys.argv.index('--') + 1:]
OUT, REPORT = Path(ARGS[0]), Path(ARGS[1])
HERE = Path(__file__).resolve().parent
LAYOUT = HERE.parent / 'Exports' / 'airport_layout.json'
W, DEPTH = 0.05, 0.15
MATS = dict(oak='MI_AP_P43TOak', housing='MI_AP_P38AHousing', opal='MI_AP_P38AOpal', frame='MI_AP_P38AFrame',
            navy='MI_AP_P38ANavy', gold='MI_AP_P38AGold')
COL = dict(oak=(.66, .46, .27), housing=(.05, .1, .1), opal=(1, .82, .55), frame=(.13, .18, .17), navy=(.02, .05, .06),
           gold=(.72, .48, .11))


class Mesh:
    """One bmesh, metre UVs by face orientation, material per face."""

    def __init__(self):
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new('UVMap')
        self.mat_index = {k: i for i, k in enumerate(MATS)}
        self.faces = 0

    def box(self, c, s, mat):
        bm = self.bm
        vs = [bm.verts.new((c[0] + sx * s[0] / 2, c[1] + sy * s[1] / 2, c[2] + sz * s[2] / 2))
              for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
        long_ax = max(range(3), key=lambda k: s[k])
        for f in [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]:
            face = bm.faces.new([vs[i] for i in f])
            face.material_index = self.mat_index[mat]
            face.smooth = False
            face.normal_update()
            n_ax = max(range(3), key=lambda k: abs(face.normal[k]))
            if n_ax != long_ax:
                ua, va = next(k for k in range(3) if k not in (n_ax, long_ax)), long_ax
            else:                                   # end grain
                ua, va = (long_ax + 1) % 3, (long_ax + 2) % 3
            for l in face.loops:
                l[self.uv].uv = (l.vert.co[ua], l.vert.co[va])
            face.tag = True
            self.faces += 1

    def cylinder(self, c, r, h, mat, seg=24, cap_top=True, cap_bottom=True, mat_bottom=None):
        bm = self.bm
        z0, z1 = c[2] - h / 2, c[2] + h / 2
        lo = [bm.verts.new((c[0] + r * math.cos(2 * math.pi * k / seg), c[1] + r * math.sin(2 * math.pi * k / seg), z0)) for k in range(seg)]
        hi = [bm.verts.new((c[0] + r * math.cos(2 * math.pi * k / seg), c[1] + r * math.sin(2 * math.pi * k / seg), z1)) for k in range(seg)]
        for k in range(seg):
            f = bm.faces.new([lo[k], lo[(k + 1) % seg], hi[(k + 1) % seg], hi[k]]); f.material_index = self.mat_index[mat]
        if cap_top:
            f = bm.faces.new(hi); f.material_index = self.mat_index[mat]
        if cap_bottom:
            f = bm.faces.new(list(reversed(lo))); f.material_index = self.mat_index[mat_bottom or mat]

    def finish(self, name):
        bm = self.bm
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        for f in bm.faces:
            if f.tag:
                continue
            f.normal_update()
            n = f.normal
            for l in f.loops:
                p = l.vert.co
                if abs(n.z) > .7:
                    l[self.uv].uv = (p.x, p.y)
                elif abs(n.x) > abs(n.y):
                    l[self.uv].uv = (p.y, p.z)
                else:
                    l[self.uv].uv = (p.x, p.z)
        me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
        for k in MATS:
            m = bpy.data.materials.get(MATS[k]) or bpy.data.materials.new(MATS[k])
            m.diffuse_color = (*COL[k], 1); me.materials.append(m)
        o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
        return o


def baffles(M, room, srv, report):
    x0, x1, y0, y1 = room['rect']
    c = room['ceiling']
    axis = room['axis']
    # Only where the measured ceiling really is at c (the cafe has a 4.4 m
    # soffit inside its rectangle): sample the 0.5 m survey grid every 0.25 m.
    grid = {(round(g[0], 2), round(g[1], 2)): g[2] for g in srv['ceiling']}

    def at_c(a, b):
        x, y = (a, b) if axis == 'x' else (b, a)
        gx, gy = round(x0 + .25 + .5 * round((x - x0 - .25) / .5), 2), round(y0 + .25 + .5 * round((y - y0 - .25) / .5), 2)
        z = grid.get((gx, gy))
        return z is not None and abs(z - c) < .05

    def split(s, e, b):
        out, cur, t = [], None, s
        while t <= e + 1e-6:
            ok = at_c(t, b)
            if ok and cur is None:
                cur = t
            if not ok and cur is not None:
                out.append((cur, t - .125)); cur = None
            t += .25
        if cur is not None:
            out.append((cur, e))
        return out
    a0, a1 = (x0, x1) if axis == 'x' else (y0, y1)
    light_lines = set()
    for L in room.get('lights', []):
        light_lines.add(min(range(len(srv['lines'])), key=lambda i: abs(srv['lines'][i]['at'] - L)))
    n_b = n_l = n_w = 0
    wave = room.get('wave')
    b0_, b1_ = (y0, y1) if axis == 'x' else (x0, x1)
    light_at = [srv['lines'][i]['at'] for i in light_lines]
    deepest = 0.0
    for i, line in enumerate(srv['lines']):
        b = line['at']
        spans = []
        for s, e in line['free']:
            s, e = max(s, a0) + .03, min(e, a1) - .03
            if e - s >= .3:
                spans += split(s, e, b)
        for s, e in spans:
            if e - s < .3:
                continue
            mid, ln = (s + e) / 2, e - s
            if i in light_lines:
                # Light channel: housing + opal strip, the light's row.
                for (dz, wd, ht, mat) in ((-.04, .11, .08, 'housing'), (-.083, .07, .006, 'opal')):
                    cc = (mid, b, c + dz) if axis == 'x' else (b, mid, c + dz)
                    ss = (ln, wd, ht) if axis == 'x' else (wd, ln, ht)
                    M.box(cc, ss, mat)
                n_l += 1
            elif wave and line.get('bands'):
                amp, lam = wave['amp'], wave['length']
                # Points along this line where something stands within the
                # wave's depth: the swell fades out before reaching them.
                blocked = []
                for frees in line['bands'].values():
                    t = s
                    while t <= e + 1e-6:
                        if not any(f0 + .03 <= t <= f1 - .03 for f0, f1 in frees):
                            blocked.append(t)
                        t += .1
                eb = smooth(.3, 1.8, min(b - b0_, b1_ - b)) * (smooth(.25, 1.2, min(abs(b - la) for la in light_at)) if light_at else 1)
                phase = 1.3 * math.sin(2 * math.pi * b / (1.7 * lam))

                def depth_at(t, s=s, e=e, blocked=blocked, eb=eb, phase=phase, amp=amp, lam=lam):
                    env = eb * smooth(.3, 2.2, min(t - a0, a1 - t)) * smooth(.1, 1.2, min(t - s, e - t))
                    if blocked:
                        env *= smooth(.15, 1.3, min(abs(t - q) for q in blocked))
                    return DEPTH + amp * env * (.5 - .5 * math.cos(2 * math.pi * t / lam + phase))
                wave_baffle(M, axis, b, c, s, e, depth_at)
                deepest = max(deepest, max(depth_at(s + (e - s) * k / 40) for k in range(41)))
                n_w += 1
            else:
                dep = room.get('depth', DEPTH)
                cc = (mid, b, c - .003 - dep / 2) if axis == 'x' else (b, mid, c - .003 - dep / 2)
                ss = (ln, W, dep) if axis == 'x' else (W, ln, dep)
                M.box(cc, ss, 'oak')
                n_b += 1
    report.append(dict(room=room['name'], ceiling=c, baffles=n_b, wave_baffles=n_w, deepest=round(deepest, 3),
                       light_runs=n_l, light_lines=sorted(light_lines)))


def smooth(e0, e1, x):
    t = min(1.0, max(0.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def wave_baffle(M, axis, b, c, s, e, depth_at):
    """A baffle from a=s to a=e on line b whose underside is depth_at(a) below the ceiling."""
    bm = M.bm
    n = max(1, int(math.ceil((e - s) / .2)))
    ts = [s + (e - s) * k / n for k in range(n + 1)]
    top = c - .003

    def P(a, bb, z):
        return bm.verts.new((a, bb, z) if axis == 'x' else (bb, a, z))
    rows = []
    for t in ts:
        d = depth_at(t)
        rows.append([P(t, b - W / 2, top), P(t, b + W / 2, top), P(t, b + W / 2, top - d), P(t, b - W / 2, top - d)])

    def face(vs, uvf, smooth_it=False):
        f = bm.faces.new(vs)
        f.material_index = M.mat_index['oak']
        f.smooth = smooth_it
        for l in f.loops:
            l[M.uv].uv = uvf(l.vert.co)
        f.tag = True
        M.faces += 1
        return f
    along = lambda co: co[0] if axis == 'x' else co[1]
    across = lambda co: co[1] if axis == 'x' else co[0]
    for k in range(n):
        r0, r1 = rows[k], rows[k + 1]
        face([r0[0], r1[0], r1[3], r0[3]], lambda co: (co[2], along(co)))          # side -b
        face([r0[1], r0[2], r1[2], r1[1]], lambda co: (co[2], along(co)))          # side +b
        face([r0[3], r1[3], r1[2], r0[2]], lambda co: (across(co), along(co)), True)   # underside
        face([r0[0], r0[1], r1[1], r1[0]], lambda co: (across(co), along(co)))     # top
    face(list(rows[0]), lambda co: (across(co), co[2]))
    face(list(reversed(rows[-1])), lambda co: (across(co), co[2]))
    for k in range(n):                            # crisp arrises along the underside
        for i in (3, 2):
            for ed in rows[k][i].link_edges:
                if ed.other_vert(rows[k][i]) is rows[k + 1][i]:
                    ed.smooth = False


def pendant(M, x, y, z_light, ceiling, r=.42, h=.34, body='oak'):
    """Drum pendant: drum, opal diffuser under it, gold rims, steel cable to the ceiling."""
    zb = z_light - .02                       # diffuser just under the light actor
    M.cylinder((x, y, zb + h / 2), r, h, body, seg=32, mat_bottom='opal')
    if body != 'oak':
        for zr in (zb + .015, zb + h - .015):
            M.cylinder((x, y, zr), r + .008, .03, 'gold', seg=32, cap_top=False, cap_bottom=False)
    M.cylinder((x, y, zb + h + .01), .06, .02, 'frame', seg=12)
    top = zb + h + .02
    M.box((x, y, (top + ceiling) / 2), (.008, .008, ceiling - top), 'frame')
    M.cylinder((x, y, ceiling - .01), .07, .02, 'frame', seg=12)


def flush(M, x, y, ceiling, along, length=1.6, width=.14):
    s = (length, width, .03) if along == 'x' else (width, length, .03)
    M.box((x, y, ceiling - .015), s, 'housing')
    s2 = (length - .04, width - .04, .004) if along == 'x' else (width - .04, length - .04, .004)
    M.box((x, y, ceiling - .032), s2, 'opal')


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    OUT.mkdir(parents=True, exist_ok=True)
    spec = json.loads((HERE / 'Ceilings48.json').read_text(encoding='utf-8'))
    srv = {r['name']: r for r in json.loads((HERE / 'Survey48.json').read_text(encoding='utf-8'))['rooms']}
    lights = json.loads(LAYOUT.read_text(encoding='utf-8'))['lights']
    report = dict(rooms=[], pendants=0, flush=0)
    M = Mesh()
    for room in spec['rooms']:
        baffles(M, room, srv[room['name']], report['rooms'])
    baffle_rooms = {r['name'] for r in spec['rooms'] if r.get('lights')}   # rooms lit by channels
    baffle_rooms |= {z for r in spec['rooms'] for z in r.get('covers', [])}  # Pass50: old rooms inside the hall
    # Cafe: the 4.23 m and 6.63 m lights now sit in the cafe_low / cafe_high
    # channels; three large decorative drums hang over the dining tables
    # between the light rows, lit from inside, clear of every light actor.
    covered = baffle_rooms | {'cafe', 'forecourt'}
    for x, y, zb, ceiling in spec.get('feature_pendants', []):
        pendant(M, x, y, zb + .02, ceiling, r=.6, h=.42, body='navy'); report['pendants'] += 1
    for L in lights:
        z, fx = L.get('zone'), L.get('fixture')
        if fx != 'SM_AP_Fixtures38' or (z in covered and not (z == 'cafe' and L['position'][2] < 3.0)):
            continue
        x, y, lz = L['position']
        ceiling = lz + .169
        if z == 'cafe':
            if lz < 3.0:                                   # under the gallery deck
                M.cylinder((x, y, ceiling - .015), .22, .03, 'housing', mat_bottom='opal'); report['flush'] += 1
            elif spec.get('cafe_flush'):                   # Pass58: no hanging drums; flush on the ceiling
                flush(M, x, y, spec['cafe_flush'], 'y', length=2.4); report['flush'] += 1
            elif lz < 5:
                pendant(M, x, y, lz, 6.8); report['pendants'] += 1
            else:
                pendant(M, x, y, lz - .25, 6.8, r=.32, h=.26); report['pendants'] += 1
        elif z == 'forecourt':
            flush(M, x, y, ceiling, 'y', length=2.4); report['flush'] += 1
        else:
            flush(M, x, y, ceiling, 'x' if z in ('operations',) else 'y'); report['flush'] += 1
    obj = M.finish('SM_AP_P48Ceilings')
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active = obj
    fbx = OUT / 'SM_AP_P48Ceilings.fbx'
    bpy.ops.export_scene.fbx(filepath=str(fbx), use_selection=True, apply_unit_scale=True, global_scale=1.0,
                             apply_scale_options='FBX_SCALE_NONE', object_types={'MESH'}, use_mesh_modifiers=True,
                             mesh_smooth_type='FACE', bake_space_transform=False, axis_forward='Y', axis_up='Z')
    report.update(status='SUCCESS', asset=obj.name, fbx=str(fbx.resolve()), materials=list(MATS.values()),
                  polygons=len(obj.data.polygons))
    REPORT.write_text(json.dumps(report, indent=1), encoding='utf-8')
    print('CEILINGS48', report['polygons'], sum(r['baffles'] for r in report['rooms']),
          sum(r['wave_baffles'] for r in report['rooms']), report['pendants'], report['flush'])


main()
