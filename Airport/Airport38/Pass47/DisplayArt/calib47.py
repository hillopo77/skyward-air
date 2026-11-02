import bpy, sys, numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
def load(p):
    im = bpy.data.images.load(p); w, h = im.size
    px = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(px)
    return px.reshape(h, w, 4)[::-1, :, :3]          # top-down rows
def bbox(img, rgb, tol=0.06):
    m = (np.abs(img - np.array(rgb)).max(-1) < tol)
    ys, xs = np.nonzero(m)
    return (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())) if len(xs) else None
gold = [0xF1/255, 0xD6/255, 0x9C/255]; tag = [0xA1/255, 0xC8/255, 0xB2/255]
for p in a:
    img = load(p)
    print(p.split('/')[-1], 'title', bbox(img, gold), 'row tags', bbox(img[240:520], tag))
