"""Pass47: paint the airside service road.

The apron between the grass bank (toe at x -9.1) and the aircraft stand is
one unbroken grey slab at z -3.689: from the gate windows, the jet bridge and
the flight camera nothing says where vehicles drive or where the stand
begins. This paints a 4.8 m service road along the terminal's airside face,
the way every stand is fronted: solid white edge lines at x -8.8 and -4.0,
a dashed centre line at x -6.4 (3 m dash, 3 m gap).
Lines sit 5 mm above the pavement (paint, no collision), y -24..36, which
stays clear of the wing (x >= -3.0) and passes under the bridge (z 2.8).
The staff zebra crossing at y 17.35..19.75 (bars every 0.8 m, measured from
a top-down still) stopped at x -5.0, mid-road: the lines break across it
and two matching bars carry it over the east edge line to the stand.

World source coordinates, exported at the origin. Headless.
Usage: blender -b --factory-startup -P airside_road47_blender.py -- <out_dir> <report.json>
"""
import bpy, bmesh, json, sys
from pathlib import Path

ARGS = sys.argv[sys.argv.index('--') + 1:]
OUT, REPORT = Path(ARGS[0]), Path(ARGS[1])
Z = -3.689 + 0.005
Y0, Y1 = -24.0, 36.0
EDGES = (-8.8, -4.0)
CENTRE, DASH, GAP = -6.4, 3.0, 3.0
WIDE, THIN = 0.15, 0.12
CROSS = (17.35, 19.75)                 # existing zebra, y extent
CLEAR = (CROSS[0] - 0.35, CROSS[1] + 0.35)
NEW_BARS = (-4.39, -3.59)              # continue the 0.8 m pitch, 0.38 bars


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    OUT.mkdir(parents=True, exist_ok=True)
    bm = bmesh.new()

    def strip(x, ya, yb, w):
        vs = [bm.verts.new((x + sx * w / 2, y, Z)) for sx, y in ((-1, ya), (1, ya), (1, yb), (-1, yb))]
        bm.faces.new(vs)

    def broken(x, ya, yb, w):
        n = 0
        for a, b in ((ya, min(yb, CLEAR[0])), (max(ya, CLEAR[1]), yb)):
            if b - a > 0.3:
                strip(x, a, b, w); n += 1
        return n

    for x in EDGES:
        broken(x, Y0, Y1, WIDE)
    y, dashes = Y0, 0
    while y + DASH <= Y1:
        dashes += broken(CENTRE, y, y + DASH, THIN); y += DASH + GAP
    for x in NEW_BARS:
        strip(x, CROSS[0], CROSS[1], 0.38)
    bm.normal_update()
    for f in bm.faces:                                   # face up
        if f.normal.z < 0:
            f.normal_flip()
    me = bpy.data.meshes.new('SM_AP_P47AirsideRoad'); bm.to_mesh(me); bm.free()
    m = bpy.data.materials.new('MI_AP_F39White'); m.diffuse_color = (0.92, 0.92, 0.9, 1)
    me.materials.append(m)
    obj = bpy.data.objects.new('SM_AP_P47AirsideRoad', me)
    bpy.context.scene.collection.objects.link(obj)
    obj.select_set(True); bpy.context.view_layer.objects.active = obj
    fbx = OUT / 'SM_AP_P47AirsideRoad.fbx'
    bpy.ops.export_scene.fbx(filepath=str(fbx), use_selection=True, apply_unit_scale=True, global_scale=1.0,
                             apply_scale_options='FBX_SCALE_NONE', object_types={'MESH'}, use_mesh_modifiers=True,
                             mesh_smooth_type='FACE', bake_space_transform=False, axis_forward='Y', axis_up='Z')
    REPORT.write_text(json.dumps(dict(status='SUCCESS', asset=obj.name, fbx=str(fbx.resolve()),
                                      materials=[m.name], edges=EDGES, centre=CENTRE, dashes=dashes,
                                      y=[Y0, Y1], z=Z, polygons=len(me.polygons)), indent=1), encoding='utf-8')
    print('AIRSIDE47', dashes)


main()
