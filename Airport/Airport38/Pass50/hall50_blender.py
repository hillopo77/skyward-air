"""Pass50: open the landside into one tall hall (headless Blender).

Foyer, check-in and the landside corridor were three low rooms (3.4-3.8 m)
behind two partitions. This turns them into one 23 x 14 m hall, 6.6 m high,
lit by a band of clerestory glazing on all four sides above the
neighbouring roofs.

From the live shell meshes (export50_editor.py -> Current/*.fbx):
  remove   every face of the two partitions (x -43 and y -8) and of what was
           mounted on them (wayfinding, attachments, door/arch trims,
           retained craft, wall finish panels); the ceilings and roofs over
           the hall
  lift     the rooftop plant units that stood on the old hall roofs onto the
           new roof
And a new mesh, SM_AP_P50Hall:
  upper walls 3.25 m to the 7.25 m parapet on all four sides, 50 mm proud
  of the old wall faces (their finish panels rise to 3.7 m) with an oak
  datum band over the join; clerestory glazing 4.4-6.2 m in 1.6 m bays; the
  new ceiling at 6.6 m and roof slab over it; oak pilasters where the
  partitions met the outer walls; steel rods carrying the check-in headers
  up to the new ceiling.
Everything is written in source metres; the FBX round trip is mapped by
TO_SRC/FROM_SRC (UE exports centimetres with y mirrored).
Usage: blender -b --factory-startup -P hall50_blender.py
"""
import bpy, bmesh, json, math, os, sys
from mathutils import Matrix, Vector
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'Pass48'))
from mesh48 import Mesh, export

CUR, OUT = HERE / 'Current', HERE / 'Rebuilt'
SPEC = json.loads((HERE / 'Hall50.json').read_text(encoding='utf-8'))
REP = dict(status='RUNNING', meshes={})


def inside(p, box):
    return box[0] <= p.x <= box[1] and box[2] <= p.y <= box[3] and box[4] <= p.z <= box[5]


def load(name):
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.import_scene.fbx(filepath=str(CUR / (name + '.fbx')))
    objs = [o for o in bpy.data.objects if o.type == 'MESH']
    assert len(objs) == 1, (name, [o.name for o in objs])
    o = objs[0]
    # Bake the importer's transform, then map to source metres.
    o.data.transform(o.matrix_world); o.matrix_world = Matrix.Identity(4)
    o.data.transform(Matrix(SPEC['to_src']))
    return o


def save(o, name):
    o.data.transform(Matrix(SPEC['to_src']).inverted())
    o.name = name; o.data.name = name
    OUT.mkdir(parents=True, exist_ok=True)
    export(o, OUT / (name + '.fbx'))


def cut(name, boxes, lifts=(), stretch=(), split=False):
    o = load(name)
    bm = bmesh.new(); bm.from_mesh(o.data)
    n0 = len(bm.faces)
    if split:
        # Slabs that run on over a neighbouring room are cut at the box sides first,
        # so only the part inside the box goes.
        for b in boxes:
            for co, no in (((b[0], 0, 0), (1, 0, 0)), ((b[1], 0, 0), (1, 0, 0)), ((0, b[2], 0), (0, 1, 0)), ((0, b[3], 0), (0, 1, 0))):
                bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), dist=1e-4,
                                       plane_co=co, plane_no=no)
    dead = [f for f in bm.faces if any(inside(f.calc_center_median(), b) for b in boxes)]
    by_mat = {}
    for f in dead:
        k = o.data.materials[f.material_index].name if f.material_index < len(o.data.materials) else '?'
        by_mat[k] = by_mat.get(k, 0) + 1
    bmesh.ops.delete(bm, geom=dead, context='FACES')
    lifted = stretched = 0
    for x0, x1, y0, y1, c, to in stretch:
        # Hung pieces (rods, ceiling plates) that reached the old ceiling reach the new one.
        for v in bm.verts:
            if x0 < v.co.x < x1 and y0 < v.co.y < y1 and abs(v.co.z - c) < .05:
                v.co.z += to - c; stretched += 1
    if lifts:
        # Whole connected units standing in the box move up by their own floor-to-roof step.
        bm.faces.ensure_lookup_table()
        seen = set()
        for f in bm.faces:
            if f.index in seen:
                continue
            comp, stack = set(), [f]
            while stack:
                g = stack.pop()
                if g.index in comp:
                    continue
                comp.add(g.index)
                for e in g.edges:
                    stack += [h for h in e.link_faces if h.index not in comp]
            seen |= comp
            faces = [bm.faces[i] for i in comp]
            vs = {v for g in faces for v in g.verts}
            c = sum((v.co for v in vs), Vector()) / len(vs)
            for lift in lifts:
                if inside(c, lift['box']):
                    dz = lift['to'] - min(v.co.z for v in vs)
                    for v in vs:
                        v.co.z += dz
                    lifted += 1
                    break
    bm.to_mesh(o.data); bm.free()
    REP['meshes'][name] = dict(faces_before=n0, removed=len(dead), removed_by_material=by_mat, lifted_units=lifted,
                               stretched_verts=stretched)
    save(o, name)


def hall(M, H):
    """One tall room: upper walls with clerestory, ceiling, roof, trims (H: one entry of Hall50.json 'halls')."""
    HX0, HX1, HY0, HY1 = H['hall']                   # wall centre lines
    HC, ROOF, PARAPET = H['ceiling'], H['roof_top'], H['parapet']
    t, proud = .20, .07                              # wall thickness, skin offset from the old faces (Pass64: .05 -> .07, it z-fought the old finish panels)
    bay = SPEC['bay']
    sides = [  # (axis along, fixed coord, inward sign, span)
        ('x', HY0, +1, (HX0, HX1)), ('x', HY1, -1, (HX0, HX1)),
        ('y', HX0, +1, (HY0, HY1)), ('y', HX1, -1, (HY0, HY1))]
    for along, c, inward, (s, e) in sides:
        side = {('x', HY0): 'S', ('x', HY1): 'N', ('y', HX0): 'W', ('y', HX1): 'E'}[(along, c)]
        z0 = H.get('wall_from_side', {}).get(side, H['wall_from'])   # glazed sides: above the glazing
        db = H.get('datum_side', {}).get(side, [z0 - .1, z0 + .05] if side in H.get('wall_from_side', {}) else H['datum'])
        sill, head = H.get('clerestory_side', {}).get(side, H['clerestory'])   # above the neighbour's roof
        inner = c + inward * (.09 + proud)               # old inner face is 0.09 from the centre line
        outer = c - inward * (.09 + .03)                 # 30 mm proud of the old outer face (no z-fight at range)
        mid, thick = (inner + outer) / 2, abs(inner - outer)
        L = e - s + .2
        cen = (s + e) / 2

        def wall_box(z_a, z_b, a0=None, a1=None, mat='clad'):
            a0, a1 = (s - .1, e + .1) if a0 is None else (a0, a1)
            ln, ca = a1 - a0, (a0 + a1) / 2
            if along == 'x':
                M.box((ca, mid, (z_a + z_b) / 2), (ln, thick, z_b - z_a), mat)
                M.box((ca, inner - inward * .006, (z_a + z_b) / 2), (ln - .02, .012, z_b - z_a), 'plaster')
            else:
                M.box((mid, ca, (z_a + z_b) / 2), (thick, ln, z_b - z_a), mat)
                M.box((inner - inward * .006, ca, (z_a + z_b) / 2), (.012, ln - .02, z_b - z_a), 'plaster')
        wall_box(z0, sill)
        wall_box(head, PARAPET)
        # Clerestory: piers at bay ends, glass between, frames round each light.
        n = max(1, int(round((e - s) / bay)))
        step = (e - s) / n
        for k in range(n + 1):
            a = s + k * step
            wall_box(sill, head, a - .12, a + .12)
            # Oak fin on the pier, outside, like the fins on the facades below.
            fo = outer - inward * .175
            fz0, fz1 = z0 + .1, PARAPET + .05
            if along == 'x':
                M.box((a, fo, (fz0 + fz1) / 2), (.1, .35, fz1 - fz0), 'oak')
            else:
                M.box((fo, a, (fz0 + fz1) / 2), (.35, .1, fz1 - fz0), 'oak')
        for k in range(n):
            a0, a1 = s + k * step + .12, s + (k + 1) * step - .12
            ca, ln = (a0 + a1) / 2, a1 - a0
            gz = (sill + head) / 2
            if along == 'x':
                M.box((ca, c, gz), (ln, .02, head - sill), 'glass')
                for zz in (sill + .03, head - .03):
                    M.box((ca, c, zz), (ln, .1, .06), 'frame')
                M.box((ca, c, gz), (.05, .1, head - sill), 'frame')
            else:
                M.box((c, ca, gz), (.02, ln, head - sill), 'glass')
                for zz in (sill + .03, head - .03):
                    M.box((c, ca, zz), (.1, ln, .06), 'frame')
                M.box((c, ca, gz), (.1, .05, head - sill), 'frame')
        # Oak datum band over the join with the old walls.
        if along == 'x':
            M.box((cen, inner - inward * .045, (db[0] + db[1]) / 2), (e - s - .2, .07, db[1] - db[0]), 'oak')
        else:
            M.box((inner - inward * .045, cen, (db[0] + db[1]) / 2), (.07, e - s - .2, db[1] - db[0]), 'oak')
    # Ceiling (faces down) and roof slab over it.
    ix0, ix1, iy0, iy1 = HX0 + .09 + proud, HX1 - .09 - proud, HY0 + .09 + proud, HY1 - .09 - proud
    M.quad([(ix0, iy0, HC), (ix0, iy1, HC), (ix1, iy1, HC), (ix1, iy0, HC)], 'ceiling')
    M.box(((HX0 + HX1) / 2, (HY0 + HY1) / 2, (HC + .02 + ROOF) / 2), (HX1 - HX0 - .2, HY1 - HY0 - .2, ROOF - HC - .02), 'roof')  # between the walls
    # Pilasters where the partitions met the outer walls.
    zp = H['wall_from']
    for x, y, ax in H.get('pilasters', []):
        if ax == 'y':                                      # on a wall running along x
            M.box((x, y, zp / 2), (.36, .1, zp), 'oak')
        else:
            M.box((x, y, zp / 2), (.1, .36, zp), 'oak')
    # Terrazzo infill where the partitions stood (the floor stopped at their faces).
    for x0, x1, y0, y1 in H.get('floor_strips', []):
        M.quad([(x0, y0, .001), (x1, y0, .001), (x1, y1, .001), (x0, y1, .001)], 'floor')
    # Header rods to the new ceiling.
    for x, y, z in H.get('rods', []):
        M.box((x, y, (z + HC) / 2), (.014, .014, HC - z), 'steel')
        M.cylinder((x, y, HC - .01), .05, .02, 'steel', seg=12)


def halls():
    M = Mesh({k: (v, (.5, .5, .5)) for k, v in SPEC['materials'].items()})
    for H in SPEC['halls']:
        hall(M, H)
    for e in SPEC.get('extras', []):                  # freestanding pieces (signs that lost their wall)
        M.box(e['c'], e['s'], e['mat'])
    o = M.finish('SM_AP_P50Hall')
    HB = HERE / 'HallBuild'; HB.mkdir(exist_ok=True)
    fbx = HB / 'SM_AP_P50Hall.fbx'
    export(o, fbx)
    REP['hall'] = dict(status='SUCCESS', asset=o.name, fbx=str(fbx.resolve()),
                       materials=list(SPEC['materials'].values()), polygons=len(o.data.polygons))
    (HERE / 'Hall50Build.json').write_text(json.dumps(REP['hall'], indent=1), encoding='utf-8')


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for name, job in ([] if os.environ.get('HALL50_ONLY') else SPEC['cuts'].items()):   # Pass51: hall mesh only
        cut(name, job['boxes'], job.get('lifts', []), job.get('stretch', []), job.get('split', False))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    halls()
    REP['status'] = 'SUCCESS'


try:
    main()
except Exception:
    import traceback
    REP['status'] = 'ERROR'; REP['error'] = traceback.format_exc()
(HERE / 'Hall50Report.json').write_text(json.dumps(REP, indent=1), encoding='utf-8')
print('HALL50', REP['status'])
