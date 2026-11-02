"""Pass47: paint the landside access road.

From the forecourt, the bus stop and the big-picture aerial the access road
(x -68..-62, top z 0.015, y -600..800 after road47_level) is a bare dark
strip on the lawn. A two-lane road gets the plainest standard paint: solid
white edge lines 0.2 m in from each kerb and a dashed centre line (3 m dash,
6 m gap). At the forecourt the kerb lane gets an amber taxi rank (y -22.5..11.5,
'TAXI' painted in the two gaps between the three taxis) and a bus bay
(y 13.5..29, 'BUS' before the shuttle): an amber outline 2.35 m out from the
kerb edge line, lettering stretched x2.2 along the lane as road text is,
reading for northbound drivers. Paint sits 1 cm above the asphalt (no collision); 1 cm rather than
5 mm because the road runs a kilometre out and depth precision thins there.

World source coordinates, exported at the origin. Headless.
Usage: blender -b --factory-startup -P landside_road47_blender.py -- <out_dir> <report.json>
"""
import bpy, bmesh, json, sys
from pathlib import Path

ARGS = sys.argv[sys.argv.index('--') + 1:]
OUT, REPORT = Path(ARGS[0]), Path(ARGS[1])
Z = 0.015 + 0.01
Y0, Y1 = -600.0, 800.0
CX, HALF = -65.0, 3.0
EDGES = (CX - HALF + 0.2, CX + HALF - 0.2)
DASH, GAP = 3.0, 6.0
EDGE_W, CENTRE_W = 0.12, 0.12
BAY_X = (CX + 0.45, EDGES[1])            # amber bay outline, inner and kerb side
BAYS = [((-22.5, 11.5), [('TAXI', -12.5), ('TAXI', 1.0)]), ((13.5, 29.0), [('BUS', 15.6)])]


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    OUT.mkdir(parents=True, exist_ok=True)
    bm = bmesh.new()

    def strip(x, ya, yb, w):
        bm.faces.new([bm.verts.new((x + sx * w / 2, y, Z)) for sx, y in ((-1, ya), (1, ya), (1, yb), (-1, yb))])

    for x in EDGES:
        strip(x, Y0, Y1, EDGE_W)
    y, dashes = Y0, 0
    while y + DASH <= Y1:
        strip(CX, y, y + DASH, CENTRE_W); y += DASH + GAP; dashes += 1
    white_faces = len(bm.faces)
    for (ya, yb), _ in BAYS:
        strip(BAY_X[0], ya, yb, 0.10)
        for y in (ya, yb):
            bm.faces.new([bm.verts.new(v) for v in ((BAY_X[0], y - .05, Z), (BAY_X[1], y - .05, Z),
                                                     (BAY_X[1], y + .05, Z), (BAY_X[0], y + .05, Z))])
    bm.normal_update()
    for f in bm.faces:
        if f.normal.z < 0:
            f.normal_flip()
        f.material_index = 0 if f.index < white_faces else 1
    me = bpy.data.meshes.new('SM_AP_P47LandsideRoad'); bm.to_mesh(me); bm.free()
    white = bpy.data.materials.new('MI_AP_F39White'); white.diffuse_color = (0.92, 0.92, 0.9, 1)
    amber = bpy.data.materials.new('MI_AP_P38EAmber'); amber.diffuse_color = (0.85, 0.62, 0.2, 1)
    me.materials.append(white); me.materials.append(amber)
    obj = bpy.data.objects.new('SM_AP_P47LandsideRoad', me)
    bpy.context.scene.collection.objects.link(obj)
    # Bay lettering, flat on the road, letters' tops to the north.
    words = []
    for _, labels in BAYS:
        for body, y in labels:
            cu = bpy.data.curves.new(body, 'FONT'); cu.body = body; cu.size = 0.72
            cu.align_x = 'CENTER'; cu.align_y = 'CENTER'
            t = bpy.data.objects.new(body, cu); t.location = ((BAY_X[0] + BAY_X[1]) / 2, y, Z + .001)
            t.scale = (1.0, 2.2, 1.0); cu.materials.append(amber)
            bpy.context.scene.collection.objects.link(t); words.append(t)
    for o in bpy.context.scene.objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target='MESH')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = 'SM_AP_P47LandsideRoad'; obj.data.name = obj.name
    obj.select_set(True)
    fbx = OUT / 'SM_AP_P47LandsideRoad.fbx'
    bpy.ops.export_scene.fbx(filepath=str(fbx), use_selection=True, apply_unit_scale=True, global_scale=1.0,
                             apply_scale_options='FBX_SCALE_NONE', object_types={'MESH'}, use_mesh_modifiers=True,
                             mesh_smooth_type='FACE', bake_space_transform=False, axis_forward='Y', axis_up='Z')
    REPORT.write_text(json.dumps(dict(status='SUCCESS', asset=obj.name, fbx=str(fbx.resolve()),
                                      materials=[x.name for x in obj.data.materials], bays=BAYS, edges=EDGES, centre=CX, dashes=dashes,
                                      y=[Y0, Y1], z=Z, polygons=len(obj.data.polygons)), indent=1), encoding='utf-8')
    print('LANDSIDE47', dashes)


main()
