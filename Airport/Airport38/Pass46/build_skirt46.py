"""Pass46 / P46-020: a ground skirt from the airfield's edge to the horizon.

The Flight39 graded airfield slab ends in a straight edge with the sky dome's
lower half showing beyond it. Edge46.json measured that edge in -game every
25 m: -0.08 m along the landside (west) edge, -3.78 m along the airside (east)
edge, grading between the two along north and south.

The skirt follows those heights exactly. Its inner rim runs 3 m inside the
slab at the measured height less 5 cm, so the seam is hidden under the slab's
lip; a second loop 40 m outside the edge keeps the near field flat at the same
height; the outer loop lies on a circle of 3850 m about the origin, inside the
4 km SkyCloudDome, so from any flight height the ground runs to the haze.

One flat-shaded mesh in world source coordinates, exported at the origin like
the union meshes. Headless; the 614 MB master is not opened.

Usage: blender -b --factory-startup -P build_skirt46.py -- <Edge46.json> <out_dir> <report.json>
"""
import bpy, bmesh, json, math, sys
from pathlib import Path

ARGS = sys.argv[sys.argv.index('--') + 1:]
EDGE, OUTDIR, REPORT = Path(ARGS[0]), Path(ARGS[1]), Path(ARGS[2])
MAT = 'MI_AP_F39Field'
DROP = 0.05
NEAR = 40.0
R_OUT = 3850.0


def main():
    E = json.loads(EDGE.read_text(encoding='utf-8'))
    assert E['status'] == 'SUCCESS'
    x0, x1, y0, y1 = E['rect']
    inset = E['inset']
    ed = E['edges']
    # One closed loop, anticlockwise seen from above: south edge west->east,
    # east edge south->north, north edge east->west, west edge north->south.
    loop = []
    for p in sorted(ed['south'], key=lambda p: p[0]):
        loop.append((p[0], y0, p[2], (0, -1)))
    for p in sorted(ed['east'], key=lambda p: p[1])[1:]:
        loop.append((x1, p[1], p[2], (1, 0)))
    for p in sorted(ed['north'], key=lambda p: -p[0])[1:]:
        loop.append((p[0], y1, p[2], (0, 1)))
    for p in sorted(ed['west'], key=lambda p: -p[1])[1:-1]:
        loop.append((x0, p[1], p[2], (-1, 0)))
    assert all(q[2] is not None for q in loop), 'edge survey has misses'

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bm = bmesh.new()
    inner, near, outer = [], [], []
    for x, y, z, (nx, ny) in loop:
        zz = z - DROP
        inner.append(bm.verts.new((x - nx * inset, y - ny * inset, zz)))
        near.append(bm.verts.new((x + nx * NEAR, y + ny * NEAR, zz)))
        # Outward along the edge normal, blended toward radial so neighbouring
        # rays fan out round the corners instead of crossing.
        dx, dy = x + nx * NEAR, y + ny * NEAR
        r = math.hypot(dx, dy) or 1.0
        ux, uy = 0.5 * nx + 0.5 * dx / r, 0.5 * ny + 0.5 * dy / r
        n = math.hypot(ux, uy)
        ux, uy = ux / n, uy / n
        # Solve |(dx,dy) + t(ux,uy)| = R_OUT for t > 0.
        b = dx * ux + dy * uy
        c = dx * dx + dy * dy - R_OUT * R_OUT
        t = -b + math.sqrt(b * b - c)
        outer.append(bm.verts.new((dx + ux * t, dy + uy * t, zz)))
    m = len(loop)
    for ring_a, ring_b in ((inner, near), (near, outer)):
        for i in range(m):
            j = (i + 1) % m
            bm.faces.new([ring_a[i], ring_a[j], ring_b[j], ring_b[i]])
    bm.normal_update()
    # Faces must point up.
    for f in bm.faces:
        if f.normal.z < 0:
            f.normal_flip()
    mesh = bpy.data.meshes.new('SM_AP_P46GroundSkirt')
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new('SM_AP_P46GroundSkirt', mesh)
    bpy.context.scene.collection.objects.link(obj)
    mat = bpy.data.materials.new(MAT)
    obj.data.materials.append(mat)
    # Planar UVs at 1 unit per 10 m, in case the material samples UVs.
    uv = mesh.uv_layers.new(name='UVMap')
    for poly in mesh.polygons:
        poly.use_smooth = False
        for li in poly.loop_indices:
            co = mesh.vertices[mesh.loops[li].vertex_index].co
            uv.data[li].uv = (co.x / 10.0, co.y / 10.0)
    OUTDIR.mkdir(parents=True, exist_ok=True)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    fbx = OUTDIR / 'SM_AP_P46GroundSkirt.fbx'
    bpy.ops.export_scene.fbx(
        filepath=str(fbx), use_selection=True, apply_unit_scale=True,
        global_scale=1.0, apply_scale_options='FBX_SCALE_NONE',
        object_types={'MESH'}, use_mesh_modifiers=True, mesh_smooth_type='FACE',
        bake_space_transform=False, axis_forward='Y', axis_up='Z')
    zs = [q[2] for q in loop]
    REPORT.write_text(json.dumps(dict(
        status='SUCCESS', blender=bpy.app.version_string,
        asset='SM_AP_P46GroundSkirt', fbx=str(fbx.resolve()), materials=[MAT],
        loop_points=m, edge_z=[min(zs), max(zs)], drop_m=DROP, near_m=NEAR,
        outer_radius_m=R_OUT, faces=2 * m), indent=1), encoding='utf-8')
    print('SKIRT46 BUILD SUCCESS', m)


main()
