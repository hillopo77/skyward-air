"""Pass47: corrected faces for the two signs whose arrow overprints the text.

architecture38._sign puts the arrow .34 in from the edge and .20 below centre,
which on narrow signs lands on the second line: 'START HERE / CHECK-IN' (arrow
across 'IN') and 'CAFE / CLOUD NINE'. The builder is fixed for the next
rebuild, but those signs are merged into the architecture union, which comes
from the Blender master. So this builds a corrected face for each - same
navy laminate, same text sizes and positions, the text block shifted .26
away from the arrow exactly as the patched builder does - and mounts it 2 cm
in front of the old arrow so it hides the old face completely.

Built in world source coordinates, exported at the origin like the union
meshes. Headless; the master is not opened.

Usage: blender -b --factory-startup -P signs47_blender.py -- <out_dir> <report.json>
"""
import bpy, bmesh, json, math, sys
from pathlib import Path

ARGS = sys.argv[sys.argv.index('--') + 1:]
OUT, REPORT = Path(ARGS[0]), Path(ARGS[1])
SIGNS = [
    dict(id='Checkin_start', center=(-43.12, -12.6, 1.95), normal=(-1, 0), width=1.7, height=.9,
         lines=[('START HERE', .22, .20), ('CHECK-IN', -.12, .19)], arrow='right'),
    dict(id='Cafe_concourse', center=(-31.88, 9.00, 2.15), normal=(1, 0), width=1.75, height=1.2,
         lines=[('CAFE', .24, .30), ('CLOUD NINE', -.08, .12)], arrow='right'),
]
PLATE = (.060, .070)          # depth range of the new face, in front of the old arrow (<= .053)
MATS = dict(Navy=(0.06, 0.10, 0.16), Text=(0.93, 0.88, 0.78), Gold=(0.78, 0.60, 0.30))


def material(key):
    name = 'MI_AP_P38A' + key
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color = (*MATS[key], 1)
    return m


def build(sign, bm_objs):
    x, y, z = sign['center']; nx, ny = sign['normal']; right = (-ny, nx)
    w, h = sign['width'], sign['height']
    d = 1 if sign['arrow'] == 'right' else -1
    shift = -d * .26 if w < 2.4 else 0.
    objs = []
    # Navy face plate.
    bm = bmesh.new()
    fw, fh = w - .07, h - .07
    for depth in PLATE:
        for su, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            u = su * fw / 2
            bm.verts.new((x + right[0] * u + nx * depth, y + right[1] * u + ny * depth, z + sz * fh / 2))
    bm.verts.ensure_lookup_table(); v = bm.verts
    for f in [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]:
        bm.faces.new([v[i] for i in f])
    me = bpy.data.meshes.new(sign['id'] + ' face'); bm.normal_update(); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(sign['id'] + ' face', me); o.data.materials.append(material('Navy'))
    bpy.context.scene.collection.objects.link(o); objs.append(o)
    # Text, exactly as airport_model.font: default font, centred, extruded .0003.
    rot = (math.pi / 2, 0, math.atan2(ny, nx) + math.pi / 2)
    for text, dz, size in sign['lines']:
        cu = bpy.data.curves.new(text, 'FONT'); cu.body = text
        cu.align_x = 'CENTER'; cu.align_y = 'CENTER'; cu.size = size; cu.extrude = .0003
        t = bpy.data.objects.new(text, cu)
        depth = PLATE[1] + .002
        # Only a line whose band meets the arrow's (z -.315..-.085) moves;
        # the others stay centred as designed.
        s_line = shift if (dz - size / 2 < -.085 and dz + size / 2 > -.315) else 0.
        t.location = (x + nx * depth + right[0] * s_line, y + ny * depth + right[1] * s_line, z + dz)
        t.rotation_euler = rot
        cu.materials.append(material('Text'))
        bpy.context.scene.collection.objects.link(t); objs.append(t)
    # Arrow, same outline and place as the builder, on the new face.
    outline = [(-.23, -.035), (.06, -.035), (.06, -.115), (.24, 0), (.06, .115), (.06, .035), (-.23, .035)]
    u0 = w / 2 - .34
    verts = []
    for depth in (PLATE[1] + .001, PLATE[1] + .010):
        for du, dzz in outline:
            uu = u0 + d * du
            verts.append((x + right[0] * uu + nx * depth, y + right[1] * uu + ny * depth, z - .20 + dzz))
    faces = [tuple(reversed(range(7))), tuple(range(7, 14))] + [(j, (j + 1) % 7, (j + 1) % 7 + 7, j + 7) for j in range(7)]
    me = bpy.data.meshes.new(sign['id'] + ' arrow'); me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new(sign['id'] + ' arrow', me); o.data.materials.append(material('Gold'))
    bpy.context.scene.collection.objects.link(o); objs.append(o)
    return objs, shift


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    OUT.mkdir(parents=True, exist_ok=True)
    report = []
    allobjs = []
    for s in SIGNS:
        objs, shift = build(s, allobjs)
        allobjs += objs
        report.append(dict(id=s['id'], text_shift_m=shift, plate_depth=PLATE))
    # Text to mesh, then one joined object.
    for o in bpy.context.scene.objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = allobjs[0]
    bpy.ops.object.convert(target='MESH')
    bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = 'SM_AP_P47SignFaces'; obj.data.name = obj.name
    obj.location = (0, 0, 0); obj.rotation_euler = (0, 0, 0)
    fbx = OUT / 'SM_AP_P47SignFaces.fbx'
    bpy.ops.export_scene.fbx(filepath=str(fbx), use_selection=True, apply_unit_scale=True, global_scale=1.0,
                             apply_scale_options='FBX_SCALE_NONE', object_types={'MESH'}, use_mesh_modifiers=True,
                             mesh_smooth_type='FACE', bake_space_transform=False, axis_forward='Y', axis_up='Z')
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'sign_faces47.blend'))
    REPORT.write_text(json.dumps(dict(status='SUCCESS', asset=obj.name, fbx=str(fbx.resolve()),
                                      materials=[m.name for m in obj.data.materials], signs=report,
                                      polygons=len(obj.data.polygons)), indent=1), encoding='utf-8')
    print('SIGNS47', len(obj.data.polygons))


main()
