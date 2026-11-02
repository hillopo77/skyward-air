"""Preview sheet of the Pass49 textures (RGB only, crops at real scale)."""
import bpy, sys, numpy as np, glob, os
a = sys.argv[sys.argv.index('--') + 1:]
files = sorted(glob.glob(os.path.join(a[0], '*49.png')))
T = 512
sheet = np.zeros((T * 2, T * 4, 4), np.float32); sheet[..., 3] = 1
for k, f in enumerate(files[:8]):
    im = bpy.data.images.load(f); n = im.size[0]
    p = np.array(im.pixels[:], np.float32).reshape(n, n, 4)
    rough = p[..., 3].mean()
    p = p[:T, :T] if n >= T else np.tile(p, (T // n + 1, T // n + 1, 1))[:T, :T]
    r, c = k // 4, k % 4
    sheet[(1 - r) * T:(2 - r) * T, c * T:(c + 1) * T, :3] = p[..., :3]
    print('PREV', os.path.basename(f), n, 'mean rough %.2f' % rough, 'mean rgb', p[..., :3].mean((0, 1)).round(3))
img = bpy.data.images.new('sheet', T * 4, T * 2); img.pixels.foreach_set(sheet.ravel())
img.filepath_raw = a[1]; img.file_format = 'PNG'; img.save()
