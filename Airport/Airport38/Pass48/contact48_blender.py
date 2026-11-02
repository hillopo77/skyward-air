"""Contact sheets of the critique stills: 4 x 5 tiles of 480 x 270 each.
Usage: blender -b --factory-startup -P contact47_blender.py -- <png dir> <out prefix>"""
import bpy, sys, glob, os
a = sys.argv[sys.argv.index('--') + 1:]
files = sorted(glob.glob(os.path.join(a[0], '*.png')))
TW, TH, C, R = 480, 270, 4, 5
for s in range(0, len(files), C * R):
    out = bpy.data.images.new('sheet', C * TW, R * TH)
    px = [0.0] * (C * TW * R * TH * 4)
    for k, f in enumerate(files[s:s + C * R]):
        im = bpy.data.images.load(f); im.scale(TW, TH); src = im.pixels[:]
        cx, cy = k % C, R - 1 - k // C
        for row in range(TH):
            d = ((cy * TH + row) * C * TW + cx * TW) * 4
            px[d:d + TW * 4] = src[row * TW * 4:(row + 1) * TW * 4]
        bpy.data.images.remove(im)
    out.pixels[:] = px
    out.filepath_raw = '%s_%d.png' % (a[1], s // (C * R)); out.file_format = 'PNG'; out.save()
    print('SHEET', out.filepath_raw, [os.path.basename(f) for f in files[s:s + C * R]])
