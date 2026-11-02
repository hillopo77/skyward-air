import bpy, sys
a = sys.argv[sys.argv.index('--') + 1:]
im = bpy.data.images.load(a[0]); w, h = im.size
x0, y0, x1, y1 = map(int, a[2:6])
px = list(im.pixels); out = bpy.data.images.new('c', x1 - x0, y1 - y0)
rows = []
for y in range(h - y1, h - y0):
    rows += px[(y * w + x0) * 4:(y * w + x1) * 4]
out.pixels = rows; out.scale((x1 - x0) * 2, (y1 - y0) * 2); out.filepath_raw = a[1]; out.file_format = 'PNG'; out.save()
