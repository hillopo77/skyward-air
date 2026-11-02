"""Pass50: crop and enlarge part of a still (headless). Usage: -- <png> <x0> <y0> <x1> <y1> <out> (pixels, top-left origin)"""
import bpy, sys, numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
im = bpy.data.images.load(a[0]); w, h = im.size
p = np.array(im.pixels[:], np.float32).reshape(h, w, 4)[::-1]
x0, y0, x1, y1 = [int(v) for v in a[1:5]]
c = p[y0:y1, x0:x1]
k = max(1, 1600 // (x1 - x0))
c = np.repeat(np.repeat(c, k, 0), k, 1)
o = bpy.data.images.new('c', c.shape[1], c.shape[0]); o.pixels.foreach_set(c[::-1].ravel())
o.filepath_raw = a[5]; o.file_format = 'PNG'; o.save()
