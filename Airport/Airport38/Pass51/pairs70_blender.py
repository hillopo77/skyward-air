"""Pass70: side-by-side before | after images of every slider pair (headless).
Args: -- imgDir outDir id,id,..."""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
src, out, ids = a[0], a[1], a[2].split(',')
os.makedirs(out, exist_ok=True)
sc = bpy.context.scene
sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 88
GAP = 12
for i in ids:
    b = bpy.data.images.load(os.path.join(src, i + '_before.jpg'))
    f = bpy.data.images.load(os.path.join(src, i + '_after.jpg'))
    w, h = b.size
    pb = np.array(b.pixels[:], dtype=np.float32).reshape(h, w, 4)
    pf = np.array(f.pixels[:], dtype=np.float32).reshape(h, w, 4)
    gap = np.ones((h, GAP, 4), dtype=np.float32)
    whole = np.concatenate([pb, gap, pf], axis=1)
    img = bpy.data.images.new(i + '_pair', w * 2 + GAP, h)
    img.pixels = whole.ravel()
    img.save_render(os.path.join(out, i + '_before_after.jpg'), scene=sc)
    for x in (b, f, img):
        bpy.data.images.remove(x)
print('PAIRS70 done')
