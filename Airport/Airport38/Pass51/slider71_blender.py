"""Pass71: before / after JPEGs for the slider page, and side-by-side pairs (headless).
Args: -- pairs.json   with {"out": dir, "pairs": [[id, before_png, after_png], ...]} (paths relative to Pass51).
Writes <out>/img/<id>_before.jpg, <id>_after.jpg (1600 x 900) and <out>/pairs/<id>_before_after.jpg."""
import bpy, sys, os, json
import numpy as np
spec = json.load(open(sys.argv[sys.argv.index('--') + 1], encoding='utf-8'))
here = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(here, spec['out'])
for d in ('img', 'pairs'):
    os.makedirs(os.path.join(out, d), exist_ok=True)
sc = bpy.context.scene
sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 86
W, H, GAP = 1600, 900, 12
for pid, bpath, apath in spec['pairs']:
    px = []
    for tag, p in (('before', bpath), ('after', apath)):
        im = bpy.data.images.load(os.path.join(here, p))
        im.scale(W, H)
        im.save_render(os.path.join(out, 'img', '%s_%s.jpg' % (pid, tag)), scene=sc)
        px.append(np.array(im.pixels[:], dtype=np.float32).reshape(H, W, 4))
        bpy.data.images.remove(im)
    whole = np.concatenate([px[0], np.ones((H, GAP, 4), dtype=np.float32), px[1]], axis=1)
    img = bpy.data.images.new(pid + '_pair', W * 2 + GAP, H)
    img.pixels = whole.ravel()
    img.save_render(os.path.join(out, 'pairs', pid + '_before_after.jpg'), scene=sc)
    bpy.data.images.remove(img)
print('SLIDER71 done', len(spec['pairs']))
