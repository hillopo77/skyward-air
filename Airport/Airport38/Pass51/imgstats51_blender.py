"""Pass51: mean brightness of matching stills in two folders (headless). Args: -- dirA dirB names..."""
import bpy, sys
a, b, *names = sys.argv[sys.argv.index('--') + 1:]
def stats(p):
    im = bpy.data.images.load(p); px = list(im.pixels); w, h = im.size
    rows = lambda r0, r1: [px[(y * w + x) * 4 + c] for y in range(r0, r1, 4) for x in range(0, w, 8) for c in range(3)]
    m = lambda v: round(sum(v) / len(v), 3)
    return m(rows(0, h)), m(rows(h - 200, h)), m(rows(0, 200))      # all, top band (blender y up), bottom band
for n in names:
    print(n, 'A', stats(f'{a}/{n}.png'), 'B', stats(f'{b}/{n}.png'))
