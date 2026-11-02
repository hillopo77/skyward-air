"""Pass46: build ceiling mounts for the two check-in service headers.

`Check-in service header29 0` and `1` are 3.34 m wide, 0.66 m tall boards
hanging at z 2.85 in a room with a 3.80 m ceiling, and the 54-ray inventory
fan found no geometry within 14 cm of them in any direction. Unlike the two
gate flight displays - which Pass45 wrongly reported as floating, and which
`secondary_patch38.py:47` in fact mounts with real shoes, threaded hangers and
captured saddles - nothing in the level mounts these two.

The part language is copied from that function exactly, so a mounted header
reads as the same construction rather than a new invention:

    ceiling shoe   box (.16, .20, .024) at z = H - .012, bearing on the ceiling
    threaded rod   r = .014, from z = top - .025 up to z = H - .023
    captured saddle box (.10, .16, .032) at z = top - .006, straddling the
                   board's top edge so it grips it instead of touching it

Runs headless against factory-empty data. The 614 MB airport master is NOT
opened; these are new standalone assets, which keeps the repair reversible.
"""
import bpy, bmesh, json, math, sys
from pathlib import Path
from mathutils import Vector

ARGS = sys.argv[sys.argv.index('--') + 1:]
OUTDIR = Path(ARGS[0])
REPORT = Path(ARGS[1])

# Measured from Inventory46.json, not assumed.
HEADERS = [
    dict(name='Header0', actor='Check-in service header29 0',
         x=-30.307, y=-11.6, top=3.18, ceiling=3.80, half_width=1.67),
    dict(name='Header1', actor='Check-in service header29 1',
         x=-30.307, y=-14.6, top=3.18, ceiling=3.80, half_width=1.67),
]
HANGER_OFFSET = 1.20          # m either side of centre, inside the 1.67 m half-width
SHOE = (0.16, 0.20, 0.024)
SADDLE = (0.10, 0.16, 0.032)
ROD_R = 0.014
FRAME = 'MI_AP_P38AFrame'


def material():
    m = bpy.data.materials.get(FRAME)
    if m:
        return m
    m = bpy.data.materials.new(FRAME)
    m.use_nodes = True
    bsdf = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs['Base Color'].default_value = (0.141, 0.168, 0.200, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.42
    if 'Metallic' in bsdf.inputs:
        bsdf.inputs['Metallic'].default_value = 0.35
    return m


def add_box(bm, centre, half):
    verts = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                verts.append(bm.verts.new((centre[0] + sx * half[0],
                                           centre[1] + sy * half[1],
                                           centre[2] + sz * half[2])))
    bm.verts.ensure_lookup_table()
    for quad in [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1),
                 (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]:
        bm.faces.new([verts[i] for i in quad])


def add_rod(bm, x, y, z0, z1, r, segments=12):
    ring0, ring1 = [], []
    for i in range(segments):
        a = 2 * math.pi * i / segments
        cx, cy = x + r * math.cos(a), y + r * math.sin(a)
        ring0.append(bm.verts.new((cx, cy, z0)))
        ring1.append(bm.verts.new((cx, cy, z1)))
    bm.verts.ensure_lookup_table()
    for i in range(segments):
        j = (i + 1) % segments
        bm.faces.new([ring0[i], ring0[j], ring1[j], ring1[i]])
    bm.faces.new(list(reversed(ring0)))
    bm.faces.new(ring1)


def build(spec):
    name = 'SM_AP_P46M_' + spec['name']
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(material())

    bm = bmesh.new()
    top, H = spec['top'], spec['ceiling']
    parts = []
    # Built in local coordinates about the header centre: local x,y = 0 is the
    # board's own centre, and z is absolute, so the actor is placed at z = 0.
    for dy in (-HANGER_OFFSET, HANGER_OFFSET):
        add_box(bm, (0.0, dy, H - 0.012), (SHOE[0] / 2, SHOE[1] / 2, SHOE[2] / 2))
        add_rod(bm, 0.0, dy, top - 0.025, H - 0.023, ROD_R)
        add_box(bm, (0.0, dy, top - 0.006),
                (SADDLE[0] / 2, SADDLE[1] / 2, SADDLE[2] / 2))
        parts += [
            dict(part='ceiling shoe', local=[0.0, dy, H - 0.012], size=list(SHOE),
                 bears_on='ceiling underside at z=%.3f' % H),
            dict(part='threaded hanger', local=[0.0, dy, (top - 0.025 + H - 0.023) / 2],
                 radius=ROD_R, z=[top - 0.025, H - 0.023]),
            dict(part='captured saddle', local=[0.0, dy, top - 0.006],
                 size=list(SADDLE),
                 grips='board top edge at z=%.3f, 10 mm of capture' % top)]
    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()

    bev = obj.modifiers.new('Bevel', 'BEVEL')
    bev.width = 0.003
    bev.segments = 2
    bev.limit_method = 'ANGLE'
    bev.angle_limit = math.radians(50)
    for p in mesh.polygons:
        p.use_smooth = False
    return obj, parts


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = 'METRIC'
    bpy.context.scene.unit_settings.scale_length = 1.0
    OUTDIR.mkdir(parents=True, exist_ok=True)

    built = []
    for spec in HEADERS:
        obj, parts = build(spec)
        # Export unrotated at the origin. Pass45 lost half a session to baking
        # yaw into the mesh and then letting the importer apply it again.
        obj.rotation_euler = (0.0, 0.0, 0.0)
        obj.location = Vector((0.0, 0.0, 0.0))
        for o in bpy.context.scene.objects:
            o.select_set(False)
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        fbx = OUTDIR / (obj.name + '.fbx')
        bpy.ops.export_scene.fbx(
            filepath=str(fbx), use_selection=True, apply_unit_scale=True,
            global_scale=1.0, apply_scale_options='FBX_SCALE_NONE',
            object_types={'MESH'}, use_mesh_modifiers=True,
            mesh_smooth_type='FACE', bake_space_transform=False,
            axis_forward='Y', axis_up='Z')
        built.append(dict(
            asset=obj.name, fbx=str(fbx.resolve()), actor=spec['actor'],
            world_centre=[spec['x'], spec['y'], 0.0], yaw_degrees=0.0,
            hanger_offset_m=HANGER_OFFSET, board_top_m=spec['top'],
            ceiling_m=spec['ceiling'], parts=parts,
            triangles=len(obj.data.polygons) * 2))

    blend = OUTDIR / 'header_mounts46.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    REPORT.write_text(json.dumps(dict(
        status='SUCCESS', blender=bpy.app.version_string,
        mounts=built, count=len(built), blend=str(blend),
        language_copied_from='secondary_patch38.apply, the gate display mounts'),
        indent=1), encoding='utf-8')
    print('MOUNTS46 BUILT %d' % len(built))


main()
