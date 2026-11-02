"""Before/after pairs: each row is the Pass47 still (left) and the Pass48 still (right) of one view."""
import bpy, sys, os, numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
before, after, out, names = a[0], a[1], a[2], a[3].split(',')
TW, TH = 960, 540
sheet = np.zeros((TH * len(names), TW * 2, 4), np.float32); sheet[..., 3] = 1
for r, n in enumerate(names):
    for c, d in enumerate((before, after)):
        im = bpy.data.images.load(os.path.join(d, n + '.png')); im.scale(TW, TH)
        p = np.array(im.pixels[:], np.float32).reshape(TH, TW, 4)
        row = len(names) - 1 - r
        sheet[row * TH:(row + 1) * TH, c * TW:(c + 1) * TW] = p
        bpy.data.images.remove(im)
img = bpy.data.images.new('s', TW * 2, TH * len(names)); img.pixels.foreach_set(sheet.ravel())
img.filepath_raw = out; img.file_format = 'PNG'; img.save(); print('BA48', out)
