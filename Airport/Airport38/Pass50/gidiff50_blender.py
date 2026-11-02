import bpy, numpy as np, sys
d = sys.argv[sys.argv.index('--') + 1]
def load(n):
    im = bpy.data.images.load(d + '/' + n + '.png'); w, h = im.size
    return np.array(im.pixels[:], np.float32).reshape(h, w, 4)[..., :3]
for a, b in (('T_sec_gi0', 'T_sec_gi1'), ('T_hall_gi0', 'T_hall_gi1')):
    x, y = load(a), load(b)
    print('GIDIFF', a, 'mean0 %.4f mean1 %.4f absdiff %.4f' % (x.mean(), y.mean(), np.abs(x - y).mean()))
