"""Pass47: give the landside front a face.

From the road the terminal reads as a long low box with a small fascia under
the entrance porch, and the arrivals exit has no sign outside at all.

  letters   'SKYWARD AIR' in 0.85 m gold letters standing on the entrance
            foyer roof (measured z 4.14), 0.4 m back from the edge so they
            read over the 3.74 m porch from the forecourt, the road and the
            flight camera. Segoe UI Bold, as on every screen in the terminal;
            on a dark steel rail frame with posts and base plates.
  arrivals  'ARRIVALS / TAXIS & SHUTTLE' fascia over the public exit doors
            (y -20, door head 2.70), the same oak backing + navy face + text
            construction as the existing 'SKYWARD AIR / DEPARTURES' fascia.

World source coordinates, exported at the origin. Headless.
Usage: blender -b --factory-startup -P facade47_blender.py -- <out_dir> <report.json>
"""
import bpy, bmesh, json, math, sys
from pathlib import Path

ARGS = sys.argv[sys.argv.index('--') + 1:]
OUT, REPORT = Path(ARGS[0]), Path(ARGS[1])
COL = dict(MI_AP_P38AGold=(0.78, 0.60, 0.30), MI_AP_DarkSteel_001=(0.1, 0.11, 0.12),
           MI_AP_P38AOak=(0.62, 0.43, 0.25), MI_AP_P38ANavy=(0.06, 0.10, 0.16), MI_AP_P38AText=(0.93, 0.88, 0.78))
ROOF_Z, EDGE_X, CY = 4.14, -49.0, -12.5


def mat(n):
    m = bpy.data.materials.get(n) or bpy.data.materials.new(n); m.diffuse_color = (*COL[n], 1); return m


def box(name, c, s, m):
    bm = bmesh.new()
    vs = [bm.verts.new((c[0] + sx * s[0] / 2, c[1] + sy * s[1] / 2, c[2] + sz * s[2] / 2))
          for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
    for f in [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]:
        bm.faces.new([vs[i] for i in f])
    me = bpy.data.meshes.new(name); bm.normal_update(); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); o.data.materials.append(mat(m)); bpy.context.scene.collection.objects.link(o)
    return o


def text(body, loc, size, m, font=None, extrude=.0003, align='CENTER'):
    cu = bpy.data.curves.new(body, 'FONT'); cu.body = body; cu.size = size
    cu.align_x = align; cu.align_y = 'BOTTOM' if font else 'CENTER'; cu.extrude = extrude
    if font:
        cu.font = bpy.data.fonts.load(font, check_existing=True)
    o = bpy.data.objects.new(body, cu); o.location = loc
    o.rotation_euler = (math.pi / 2, 0, -math.pi / 2)     # face -x (west), read toward -y
    cu.materials.append(mat(m)); bpy.context.scene.collection.objects.link(o)
    return o


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    OUT.mkdir(parents=True, exist_ok=True)
    # Rooftop letters: front face at x -48.62, sitting 0.12 above the roof on the frame.
    lx = EDGE_X + 0.40
    letters = text('SKYWARD AIR', (lx - 0.03, CY, ROOF_Z + 0.12), 1.12, 'MI_AP_P38AGold',
                   font='C:/Windows/Fonts/segoeuib.ttf', extrude=.03)
    bpy.context.view_layer.update()
    span = max(v[1] for v in letters.bound_box) - min(v[1] for v in letters.bound_box)
    half = 0.5 * max((letters.matrix_world @ __import__('mathutils').Vector(c)).y for c in letters.bound_box) - \
           0.5 * min((letters.matrix_world @ __import__('mathutils').Vector(c)).y for c in letters.bound_box)
    # Rails behind the letters and posts with base plates on the roof.
    rx = lx + 0.10
    for z in (ROOF_Z + 0.22, ROOF_Z + 0.78):
        box('rail', (rx, CY, z), (0.05, 2 * half + 0.3, 0.05), 'MI_AP_DarkSteel_001')
    n = max(2, int((2 * half) / 1.2) + 1)
    for k in range(n + 1):
        y = CY - half - 0.1 + k * (2 * half + 0.2) / n
        box('post', (rx, y, ROOF_Z + 0.45), (0.05, 0.05, 0.9), 'MI_AP_DarkSteel_001')
        box('strut', (rx + 0.30, y, ROOF_Z + 0.30), (0.6, 0.04, 0.04), 'MI_AP_DarkSteel_001')
        box('plate', (rx + 0.25, y, ROOF_Z + 0.01), (0.7, 0.18, 0.02), 'MI_AP_DarkSteel_001')
    # Arrivals fascia, Terminal_exterior construction: oak backing, navy face, text.
    fx, fy, fz, fw, fh = -49.12, -20.0, 3.12, 3.3, .46
    box('fascia backing', (fx, fy, fz), (.045, fw, fh), 'MI_AP_P38AOak')
    box('fascia face', (fx - .031, fy, fz), (.024, fw - .07, fh - .07), 'MI_AP_P38ANavy')
    text('ARRIVALS  /  TAXIS & SHUTTLE', (fx - .046, fy, fz), .18, 'MI_AP_P38AText')
    for o in bpy.context.scene.objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = letters
    bpy.ops.object.convert(target='MESH')
    bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = 'SM_AP_P47Facade'; obj.data.name = obj.name
    for p in obj.data.polygons:
        p.use_smooth = False
    fbx = OUT / 'SM_AP_P47Facade.fbx'
    bpy.ops.export_scene.fbx(filepath=str(fbx), use_selection=True, apply_unit_scale=True, global_scale=1.0,
                             apply_scale_options='FBX_SCALE_NONE', object_types={'MESH'}, use_mesh_modifiers=True,
                             mesh_smooth_type='FACE', bake_space_transform=False, axis_forward='Y', axis_up='Z')
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'facade47.blend'))
    REPORT.write_text(json.dumps(dict(status='SUCCESS', asset=obj.name, fbx=str(fbx.resolve()),
                                      materials=[m.name for m in obj.data.materials],
                                      letters_span_m=round(2 * half, 2), polygons=len(obj.data.polygons)), indent=1),
                      encoding='utf-8')
    print('FACADE47', round(2 * half, 2))


main()
