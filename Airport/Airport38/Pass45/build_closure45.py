"""Pass45: build the jetbridge joint-closure panels in Blender.

Runs headless against factory-empty data in this folder. The 614 MB airport
master is NOT opened or modified; these are new standalone assets exported for
native import, which keeps the repair reversible and avoids a long rebuild.

Each panel closes one junction gap confirmed by the walk-off probe. The panel
language follows the existing sleeves: a solid lower wall with a teal band, a
glazed upper section, a trim header, and steel mullions, so a closed junction
reads as the same structure rather than a patch laid over it.

Geometry is built in SOURCE metres at the panel's own origin, so each asset
can be attached to its moving bridge parent with KEEP_WORLD and follow the
deployed pose without a doubled transform.
"""
import bpy, bmesh, json, math, sys
from pathlib import Path
from mathutils import Vector

ARGS = sys.argv[sys.argv.index('--') + 1:]
SPECS = Path(ARGS[0])
OUTDIR = Path(ARGS[1])
REPORT = Path(ARGS[2])

# Section heights, metres above the local deck.
KICK_TOP = 0.06
SOLID_TOP = 1.02
GLASS_TOP = 2.18
HEAD_TOP = 2.34
SOLID_T = 0.090
GLASS_T = 0.026
HEAD_T = 0.110
MULLION_T = 0.055
MULLION_SPACING = 1.25
BAND_BOTTOM = 0.70          # teal stripe, matching the sleeves
BAND_TOP = 0.86

MATS = {
    'Shell': (0.898, 0.886, 0.859, 1.0),
    'Teal': (0.047, 0.325, 0.325, 1.0),
    'Glass': (0.75, 0.82, 0.83, 0.18),
    'Trim': (0.141, 0.168, 0.200, 1.0),
    'Steel': (0.560, 0.588, 0.615, 1.0),
}
MAT_ORDER = ['Shell', 'Teal', 'Glass', 'Trim', 'Steel']


def material(name):
    key = 'MI_AP_P38B' + name
    m = bpy.data.materials.get(key)
    if m:
        return m
    m = bpy.data.materials.new(key)
    m.use_nodes = True
    bsdf = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    r, g, b, a = MATS[name]
    bsdf.inputs['Base Color'].default_value = (r, g, b, 1.0)
    if name == 'Glass':
        bsdf.inputs['Roughness'].default_value = 0.06
        if 'Transmission Weight' in bsdf.inputs:
            bsdf.inputs['Transmission Weight'].default_value = 0.92
        m.blend_method = 'BLEND' if hasattr(m, 'blend_method') else m.blend_method
    elif name == 'Steel':
        bsdf.inputs['Metallic'].default_value = 0.85
        bsdf.inputs['Roughness'].default_value = 0.34
    else:
        bsdf.inputs['Roughness'].default_value = 0.52
    return m


def add_box(bm, centre, half, mat_index):
    """Axis-aligned box in the panel's local frame (x along, y across, z up)."""
    verts = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                verts.append(bm.verts.new((
                    centre[0] + sx * half[0],
                    centre[1] + sy * half[1],
                    centre[2] + sz * half[2])))
    bm.verts.ensure_lookup_table()
    idx = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1),
           (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    for quad in idx:
        f = bm.faces.new([verts[i] for i in quad])
        f.material_index = mat_index


def build_panel(name, length):
    """One closure panel, centred on its own origin, running along local +X."""
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    for key in MAT_ORDER:
        obj.data.materials.append(material(key))
    mi = {k: i for i, k in enumerate(MAT_ORDER)}

    bm = bmesh.new()
    hx = length / 2.0

    # kick, solid wall, teal band, glazing, header
    add_box(bm, (0, 0, KICK_TOP / 2), (hx, HEAD_T / 2, KICK_TOP / 2), mi['Trim'])
    solid_h = SOLID_TOP - KICK_TOP
    add_box(bm, (0, 0, KICK_TOP + solid_h / 2), (hx, SOLID_T / 2, solid_h / 2), mi['Shell'])
    band_h = BAND_TOP - BAND_BOTTOM
    add_box(bm, (0, 0, BAND_BOTTOM + band_h / 2),
            (hx, SOLID_T / 2 + 0.004, band_h / 2), mi['Teal'])
    glass_h = GLASS_TOP - SOLID_TOP
    add_box(bm, (0, 0, SOLID_TOP + glass_h / 2), (hx, GLASS_T / 2, glass_h / 2), mi['Glass'])
    head_h = HEAD_TOP - GLASS_TOP
    add_box(bm, (0, 0, GLASS_TOP + head_h / 2), (hx, HEAD_T / 2, head_h / 2), mi['Trim'])
    # transom at the glazing foot, so the glass sits on something
    add_box(bm, (0, 0, SOLID_TOP + 0.022), (hx, HEAD_T / 2 - 0.012, 0.030), mi['Trim'])

    # mullions
    count = max(2, int(round(length / MULLION_SPACING)) + 1)
    for i in range(count):
        t = -hx + (length * i / (count - 1) if count > 1 else 0)
        t = max(-hx + MULLION_T / 2, min(hx - MULLION_T / 2, t))
        add_box(bm, (t, 0, SOLID_TOP + glass_h / 2),
                (MULLION_T / 2, GLASS_T / 2 + 0.014, glass_h / 2), mi['Steel'])

    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()

    # bevel the visible hard edges, as the style bible asks for
    bev = obj.modifiers.new('Bevel', 'BEVEL')
    bev.width = 0.008
    bev.segments = 2
    bev.limit_method = 'ANGLE'
    bev.angle_limit = math.radians(50)
    for p in mesh.polygons:
        p.use_smooth = False
    return obj


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = 'METRIC'
    bpy.context.scene.unit_settings.scale_length = 1.0

    specs = json.loads(SPECS.read_text(encoding='utf-8'))['panels']
    OUTDIR.mkdir(parents=True, exist_ok=True)
    built = []

    for i, s in enumerate(specs):
        ax, ay = s['a']
        bx, by = s['b']
        length = math.hypot(bx - ax, by - ay)
        if length < 0.25:
            continue
        name = 'SM_AP_P45B_Closure%02d' % i
        obj = build_panel(name, length)
        yaw = math.atan2(by - ay, bx - ax)
        # Export the panel at the origin with identity rotation, so the mesh
        # carries no world transform. The native importer applies position and
        # yaw to the actor instead; baking the yaw here too would rotate the
        # panel twice.
        obj.rotation_euler = (0.0, 0.0, 0.0)
        obj.location = Vector((0.0, 0.0, 0.0))

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

        built.append(dict(
            index=i, asset=name, fbx=str(fbx), part=s['part'],
            world_centre=[round((ax + bx) / 2.0, 4), round((ay + by) / 2.0, 4),
                          round(s['deck_z'], 4)],
            yaw_degrees=round(math.degrees(yaw), 4),
            length_m=round(length, 4),
            outward=s['outward'],
            height_m=HEAD_TOP,
            triangles=len(obj.data.polygons) * 2))

    blend = OUTDIR / 'bridge_closure45.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))

    REPORT.write_text(json.dumps(dict(
        status='SUCCESS', blender=bpy.app.version_string,
        panels=built, count=len(built),
        section=dict(kick_top=KICK_TOP, solid_top=SOLID_TOP,
                     glass_top=GLASS_TOP, head_top=HEAD_TOP),
        blend=str(blend)), indent=2), encoding='utf-8')
    print('CLOSURE45 BUILT %d panels' % len(built))


main()
