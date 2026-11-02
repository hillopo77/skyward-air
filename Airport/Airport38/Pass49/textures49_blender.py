"""Pass49: ground, roof and wall maps for the outside and the plaster walls.

Pass48 left everything outdoors in flat colour: one green for a 1.5 km
airfield, one grey for the apron, the roads and the roof. These maps give
them material: packed sRGB colour in RGB, linear roughness in A, seamless.
They are projected in world space by M_AP_Ground49 (no UVs needed), and each
existing instance keeps its own colour: the editor tints every map by the
instance's old base colour over the map's mean (Textures49.json).

  Grass49     mown turf: 4 m light/dark mowing stripes, blade speckle,
              clover and dry patches                              tile 8 m
  Concrete49  apron / forecourt slabs: 5 m bays, sealed joints, per-bay
              tone, aggregate, faint tyre and oil staining        tile 10 m
  Asphalt49   dense asphalt: aggregate speckle, patching, wear    tile 4 m
  Roof49      single-ply roof membrane, 2 m sheets, welded laps   tile 6 m
  Macro49     very soft large-scale variation (multiplier) that
              stops any map reading as a repeat                   tile 70 m
  Plaster49   limewash mottle on the existing plaster colours     tile 4 m
  PlasterWarm49

Usage: blender -b --factory-startup -P textures49_blender.py -- <out_dir>
"""
import bpy, json, sys, numpy as np
from pathlib import Path

OUT = Path(sys.argv[sys.argv.index('--') + 1:][0]).resolve(); OUT.mkdir(parents=True, exist_ok=True)
HERE = Path(__file__).resolve().parent
FIN43 = HERE.parent / 'Fixes' / '06_visual_finish43' / 'Textures'
RNG = np.random.default_rng(49)
MEANS = {}


def hexrgb(h):
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])


def blur(a, sigma):
    """Wrap-around gaussian blur (FFT), so every map tiles seamlessly."""
    n = a.shape[0]
    f = np.fft.fftfreq(n)
    g = np.exp(-2 * (np.pi * sigma) ** 2 * (f[:, None] ** 2 + f[None, :] ** 2))
    return np.real(np.fft.ifft2(np.fft.fft2(a) * g))


def noise(n, sigma):
    b = blur(RNG.standard_normal((n, n)), sigma)
    return b / (np.abs(b).max() + 1e-9)


def lin(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= .04045, c / 12.92, ((c + .055) / 1.055) ** 2.4)


def save(name, rgb, rough):
    n = rgb.shape[0]
    img = bpy.data.images.new(name, n, n, alpha=True)
    px = np.zeros((n, n, 4), np.float32)
    px[..., :3] = np.clip(rgb, 0, 1); px[..., 3] = np.clip(rough, 0, 1)
    img.pixels.foreach_set(px[::-1].ravel())        # Blender rows run bottom-up
    img.filepath_raw = str(OUT / (name + '.png')); img.file_format = 'PNG'
    img.alpha_mode = 'CHANNEL_PACKED'
    img.save()
    MEANS[name] = [round(float(v), 4) for v in lin(px[..., :3]).reshape(-1, 3).mean(0)]
    print('TEX49', name, n, MEANS[name])


def uv(n):
    v, u = np.meshgrid((np.arange(n) + .5) / n, (np.arange(n) + .5) / n, indexing='ij')
    return u, v


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def grass():
    n, tile = 1024, 8.0
    u, v = uv(n)
    rgb = np.ones((n, n, 3)) * hexrgb('6A8F52')
    # Mowing stripes: two 4 m passes, soft edged, along v (world y).
    stripe = blur(np.where(u < .5, 1.0, -1.0), 6)             # soft edges between passes
    rgb *= (1 + .045 * stripe)[..., None]
    # Blades: fine speckle, a touch yellower in the light flecks.
    blade = noise(n, .7)
    rgb *= (1 + .16 * blade)[..., None]
    rgb[..., 0] *= 1 + .05 * blade; rgb[..., 2] *= 1 - .06 * blade
    # Clover (darker, bluer) and dry (straw) patches.
    clover = smooth(.25, .6, noise(n, 18))
    rgb = rgb * (1 - .25 * clover[..., None]) + hexrgb('4E7646') * .25 * clover[..., None]
    dry = smooth(.35, .8, noise(n, 30))
    rgb = rgb * (1 - .3 * dry[..., None]) + hexrgb('9A9A5C') * .3 * dry[..., None]
    rough = .92 + .05 * blade
    save('Grass49', rgb, rough)


def concrete():
    n, tile, bay = 1024, 10.0, 5.0
    u, v = uv(n)
    x, y = u * tile, v * tile
    rgb = np.ones((n, n, 3)) * hexrgb('BDBDB6')
    bi, bj = (x // bay).astype(int), (y // bay).astype(int)
    tone = np.array([[.0, .035], [-.03, .015]])[bi, bj]
    rgb *= (1 + tone)[..., None]
    rgb *= (1 + .05 * noise(n, .6))[..., None]                       # aggregate
    rgb *= (1 + .045 * noise(n, 12))[..., None]                      # trowel cloud
    stain = smooth(.45, .9, noise(n, 35))
    rgb *= (1 - .07 * stain)[..., None]                               # oil / tyre shadows
    tyre = np.exp(-((x % bay) - 2.5) ** 2 / .5) * smooth(.0, .7, noise(n, 50) + .3)
    rgb *= (1 - .06 * tyre)[..., None]
    # Sealed joints: 12 mm dark band with a softer 20 mm arris either side.
    dj = np.minimum(np.minimum(x % bay, bay - x % bay), np.minimum(y % bay, bay - y % bay))
    rgb *= (1 - .55 * (dj < .006) - .12 * ((dj >= .006) & (dj < .016)))[..., None]
    rough = .86 + .05 * noise(n, 8) - .1 * stain
    save('Concrete49', rgb, rough)


def asphalt():
    n = 1024
    rgb = np.ones((n, n, 3)) * hexrgb('4A4E52')
    fine = RNG.standard_normal((n, n))
    rgb *= (1 + .12 * blur(fine, .5) / np.abs(blur(fine, .5)).max())[..., None]
    stones = blur(RNG.standard_normal((n, n)), 1.1)
    light = stones > np.quantile(stones, .965)
    dark = stones < np.quantile(stones, .02)
    rgb[light] = hexrgb('8B8D89') * (1 + .1 * RNG.standard_normal((light.sum(), 1)))
    rgb[dark] = hexrgb('2A2C2F')
    patch = smooth(.4, .75, noise(n, 60))
    rgb *= (1 - .1 * patch)[..., None]
    wear = noise(n, 25)
    rgb *= (1 + .05 * wear)[..., None]
    rough = .9 - .05 * wear
    save('Asphalt49', rgb, rough)


def roof():
    n, tile, sheet = 1024, 6.0, 2.0
    u, v = uv(n)
    x = u * tile
    rgb = np.ones((n, n, 3)) * hexrgb('8E9592')
    rgb *= (1 + .035 * noise(n, 20))[..., None]
    rgb *= (1 + .025 * noise(n, 1.0))[..., None]
    lap = x % sheet
    rgb *= (1 + .07 * (lap < .04) - .1 * ((lap >= .04) & (lap < .055)))[..., None]   # welded lap and its shadow
    puddle = smooth(.5, .85, noise(n, 45))
    rgb *= (1 - .08 * puddle)[..., None]
    rough = .62 + .08 * noise(n, 10) - .15 * puddle
    save('Roof49', rgb, rough)


def macro():
    n = 512
    m = .6 * noise(n, 18) + .4 * noise(n, 55)
    m = .5 + .5 * m / np.abs(m).max()
    rgb = np.repeat(m[..., None], 3, axis=2)
    save('Macro49', rgb, np.ones((n, n)))


def plaster(src, name):
    img = bpy.data.images.load(str(FIN43 / (src + '.png')))
    w, h = img.size
    px = np.array(img.pixels[:], np.float32).reshape(h, w, 4)
    base = px[..., :3].reshape(-1, 3).mean(0)
    rough0 = float(px[..., 3].mean())
    n = 1024
    rgb = np.ones((n, n, 3)) * base
    rgb *= (1 + .028 * noise(n, 40) + .018 * noise(n, 9) + .008 * noise(n, 1.2))[..., None]
    save(name, rgb, np.full((n, n), rough0) + .04 * noise(n, 30))


grass(); concrete(); asphalt(); roof(); macro()
plaster('Plaster43', 'Plaster49'); plaster('PlasterWarm43', 'PlasterWarm49')
(OUT.parent / 'Textures49.json').write_text(json.dumps(MEANS, indent=1), encoding='utf-8')
