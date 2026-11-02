"""Pass51: before/after stills as 1600x900 JPEGs for the slider page (headless).
Args: -- beforeDir afterDir outDir name,name,..."""
import bpy, sys, os
a = sys.argv[sys.argv.index('--') + 1:]
before, after, out, names = a[0], a[1], a[2], a[3].split(',')
os.makedirs(out, exist_ok=True)
sc = bpy.context.scene
sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 84
for tag, d in (('before', before), ('after', after)):
    for n in names:
        im = bpy.data.images.load(os.path.join(d, n + '.png')); im.scale(1600, 900)
        im.save_render(os.path.join(out, '%s_%s.jpg' % (n, tag)), scene=sc)
        bpy.data.images.remove(im)
print('JPEG51 done')
