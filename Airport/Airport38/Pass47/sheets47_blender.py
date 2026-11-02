"""Pass47: contact sheets and image statistics, in headless Blender.

This machine's Python has no imaging library and installing one would mean a
download, so Blender (which bundles numpy and reads PNG) does the image work.

  sheets  Tile the model stills 5 x 4 per 1920 x 1080 sheet, in index order,
          so each sheet can be read against Models47.json's shot list.
  stats   For every Pass47 room still: mean luminance, the share of
          near-black and near-white pixels, and the mean colour of the top
          third (ceiling) - the numbers behind the ambience critique.

Usage: blender -b --factory-startup -P sheets47_blender.py -- <pass47_dir>
"""
import bpy, json, sys
from pathlib import Path
import numpy as np

ROOT = Path(sys.argv[sys.argv.index('--') + 1])
COLS, ROWS, W, H = 5, 4, 1920, 1080
TW, TH = W // COLS, H // ROWS


def load(path):
    img = bpy.data.images.load(str(path), check_existing=False)
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    return px.reshape(h, w, 4)            # rows bottom-up, as Blender stores them


def shrink(a, tw, th):
    h, w = a.shape[:2]
    ys = (np.arange(th) * h / th).astype(int)
    xs = (np.arange(tw) * w / tw).astype(int)
    return a[ys][:, xs]


def save(arr, path):
    h, w = arr.shape[:2]
    img = bpy.data.images.new(path.stem, w, h, alpha=True)
    img.pixels.foreach_set(arr.astype(np.float32).ravel())
    img.filepath_raw = str(path)
    img.file_format = 'PNG'
    img.save()
    bpy.data.images.remove(img)


def sheets():
    shots = json.loads((ROOT / 'Models47.json').read_text(encoding='utf-8'))['shots']
    out = ROOT / 'ModelSheets'
    out.mkdir(exist_ok=True)
    per = COLS * ROWS
    index = []
    for s in range(0, len(shots), per):
        sheet = np.zeros((H, W, 4), dtype=np.float32)
        sheet[..., 3] = 1.0
        for k, shot in enumerate(shots[s:s + per]):
            tile = shrink(load(shot['file']), TW - 4, TH - 4)
            col, row = k % COLS, k // COLS
            y0 = H - (row + 1) * TH + 2          # bottom-up storage
            x0 = col * TW + 2
            sheet[y0:y0 + TH - 4, x0:x0 + TW - 4] = tile
        name = 'sheet_%02d.png' % (s // per)
        save(sheet, out / name)
        index.append(dict(sheet=name, tiles=[dict(pos=k, row=k // COLS, col=k % COLS,
                                                  mesh=x['mesh'], actor=x['actor'],
                                                  size_m=x['size_m'])
                                             for k, x in enumerate(shots[s:s + per])]))
    (ROOT / 'ModelSheets' / 'index.json').write_text(json.dumps(index, indent=1), encoding='utf-8')
    print('SHEETS', len(index))


def stats():
    rows = []
    for p in sorted((ROOT / 'Captures').glob('*.png')):
        if p.name.startswith('sheet'):
            continue
        a = load(p)[..., :3]
        lum = a @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
        top = a[int(a.shape[0] * 2 / 3):]          # bottom-up: top third of the image
        rows.append(dict(view=p.stem, mean_lum=round(float(lum.mean()), 3),
                         dark_pct=round(100 * float((lum < 0.06).mean()), 1),
                         clipped_pct=round(100 * float((lum > 0.97).mean()), 1),
                         ceiling_rgb=[round(float(v), 3) for v in top.reshape(-1, 3).mean(0)]))
    (ROOT / 'Ambience47.json').write_text(json.dumps(rows, indent=1), encoding='utf-8')
    print('STATS', len(rows))


bpy.ops.wm.read_factory_settings(use_empty=True)
if (ROOT / 'Models47.json').exists() and json.loads((ROOT / 'Models47.json').read_text(encoding='utf-8')).get('status') == 'SUCCESS':
    sheets()
stats()
