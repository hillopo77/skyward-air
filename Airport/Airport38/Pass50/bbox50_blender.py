"""Pass50: print an FBX's world bounds and transform as Blender imports it (headless)."""
import bpy, sys

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=sys.argv[sys.argv.index('--') + 1])
for o in bpy.data.objects:
    if o.type != 'MESH':
        continue
    ws = [o.matrix_world @ v.co for v in o.data.vertices]
    print('BB', o.name, [round(min(w[i] for w in ws), 3) for i in range(3)], [round(max(w[i] for w in ws), 3) for i in range(3)],
          'mw', [[round(x, 4) for x in r] for r in o.matrix_world], 'mats', [m.name for m in o.data.materials])
