"""Pass48 makeover: new surface maps for the whole terminal.

Same contract as Finish43 (packed sRGB colour in RGB, linear roughness in A,
seamless, UV0 in source metres scaled by 1/tile), so they drop straight into
the existing finish slots. Everything is generated here from maths and seeded
noise; no external images.

  Floor48     polished terrazzo: ivory matrix, five chip colours in three
              sizes, brass divider strip on a 3 m grid           tile 3.0 m
  Carpet48    Skyward gate carpet: deep navy pile, teal flight-path
              contours, gold waypoint dots                      tile 2.0 m
  WC48        50 mm mosaic in three sage/ivory tones, pale grout tile 2.0 m
  Ceiling48   bright seamless plaster (baffles carry the pattern)  tile 3.6 m
  Wainscot48  vertical light-oak boards, 150 mm, grooved, grain  tile 2.4 m
  Oak48       richer oak grain for rails and timber panels       tile 2.0 m

Usage: blender -b --factory-startup -P textures48_blender.py -- <out_dir>
"""
import bpy, sys, numpy as np
from pathlib import Path

OUT = Path(sys.argv[sys.argv.index('--') + 1:][0]); OUT.mkdir(parents=True, exist_ok=True)
RNG = np.random.default_rng(48)


def hexrgb(h):
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])


def blur(a, sigma):
    """Wrap-around gaussian blur (FFT), so every map tiles seamlessly."""
    n = a.shape[0]
    f = np.fft.fftfreq(n)
    g = np.exp(-2 * (np.pi * sigma) ** 2 * (f[:, None] ** 2 + f[None, :] ** 2))
    return np.real(np.fft.ifft2(np.fft.fft2(a) * g))


def blobs(n, sigma, cover):
    """Irregular chips: blurred white noise, thresholded to the wanted cover."""
    b = blur(RNG.standard_normal((n, n)), sigma)
    return b > np.quantile(b, 1 - cover)


def save(name, rgb, rough):
    n = rgb.shape[0]
    img = bpy.data.images.new(name, n, n, alpha=True)
    px = np.zeros((n, n, 4), np.float32)
    px[..., :3] = np.clip(rgb, 0, 1); px[..., 3] = np.clip(rough, 0, 1)
    img.pixels.foreach_set(px[::-1].ravel())        # Blender rows run bottom-up
    img.filepath_raw = str(OUT / (name + '.png')); img.file_format = 'PNG'
    img.alpha_mode = 'CHANNEL_PACKED'
    img.save()
    print('TEX48', name, n)


def uv(n):
    v, u = np.meshgrid((np.arange(n) + .5) / n, (np.arange(n) + .5) / n, indexing='ij')
    return u, v


def floor():
    n, tile = 2048, 3.0
    rgb = np.ones((n, n, 3)) * hexrgb('E9E3D6')
    cloud = blur(RNG.standard_normal((n, n)), 60); cloud /= np.abs(cloud).max()
    rgb *= (1 + .03 * cloud)[..., None]
    rough = np.full((n, n), .26) + .03 * cloud
    chips = [('A39C8E', 2.2, .07), ('3B3E40', 1.6, .03), ('C69A58', 1.8, .025),
             ('4F7D79', 1.6, .02), ('FAF7EF', 2.6, .045), ('7A6E62', 4.0, .018), ('2F4A55', 1.2, .014)]
    for col, sigma, cover in chips:
        m = blobs(n, sigma, cover)
        rgb[m] = hexrgb(col) * (1 + .06 * RNG.standard_normal((m.sum(), 1)))
        rough[m] = .22
    # Brass divider strip, 5 mm, on the tile edge (both axes).
    u, v = uv(n)
    d = np.minimum(np.minimum(u, 1 - u), np.minimum(v, 1 - v)) * tile
    strip = d < .0025
    rgb[strip] = hexrgb('B8913F'); rough[strip] = .18
    save('Floor48', rgb, rough)


def carpet():
    n, tile = 1024, 2.0
    u, v = uv(n)
    pile = blur(RNG.standard_normal((n, n)), 1.2); pile /= np.abs(pile).max()
    rgb = np.ones((n, n, 3)) * hexrgb('1B2A3A') * (1 + .10 * pile)[..., None]
    # Flight-path contours: two families of wavy lines, integer periods so they tile.
    w1 = (8 * (v + .06 * np.sin(2 * np.pi * u) + .03 * np.sin(4 * np.pi * u + 1.0))) % 1
    w2 = (5 * (u + .08 * np.sin(2 * np.pi * v + .5))) % 1
    teal = (np.abs(w1 - .5) < .028)
    soft = (np.abs(w2 - .5) < .012) & ~teal
    rgb[teal] = hexrgb('3F7F7C') * (1 + .08 * pile[teal])[:, None]
    rgb[soft] = hexrgb('2B4656') * (1 + .08 * pile[soft])[:, None]
    # Gold waypoints where the families cross.
    gold = (np.abs(w1 - .5) < .05) & (np.abs(w2 - .5) < .03)
    rgb[gold] = hexrgb('C9A24E')
    rough = np.full((n, n), .95)
    save('Carpet48', rgb, rough)


def mosaic():
    n, tile, count = 1024, 2.0, 40
    u, v = uv(n)
    iu, iv = (u * count).astype(int) % count, (v * count).astype(int) % count
    tones = np.array([hexrgb('E9E6DC'), hexrgb('C4D2C6'), hexrgb('9DB5A8'), hexrgb('DCE3DA')])
    pick = RNG.choice(4, size=(count, count), p=[.4, .3, .1, .2])
    rgb = tones[pick[iv, iu]] * (1 + .04 * RNG.standard_normal((count, count))[iv, iu])[..., None]
    fu, fv = (u * count) % 1, (v * count) % 1
    grout = (np.minimum(fu, 1 - fu) < .045) | (np.minimum(fv, 1 - fv) < .045)
    rgb[grout] = hexrgb('B9B6AC')
    rough = np.where(grout, .9, .35)
    save('WC48', rgb, rough)


def ceiling():
    n, tile, panels = 1536, 3.6, 3
    u, v = uv(n)
    cloud = blur(RNG.standard_normal((n, n)), 30); cloud /= np.abs(cloud).max()
    rgb = np.ones((n, n, 3)) * hexrgb('F2F0E9') * (1 + .015 * cloud)[..., None]
    # Seamless smooth plaster: the 1.2 m grid read as an office ceiling.
    rough = np.full((n, n), .92)
    save('Ceiling48', rgb, rough)


def oak(name, n, tile, board, base, groove, wave=1.7):
    u, v = uv(n)
    boards = int(round(tile / board)) if board else 0
    idx = (u * boards).astype(int) if boards else np.zeros_like(u, int)
    tone = (1 + .07 * RNG.standard_normal(max(boards, 1)))[idx]
    phase = RNG.uniform(0, 1, max(boards, 1))[idx]
    grain = np.sin(2 * np.pi * (26 * u + wave * np.sin(2 * np.pi * (v + phase)) + 9 * phase))
    fine = blur(RNG.standard_normal((n, n)), .8); fine /= np.abs(fine).max()
    rgb = np.ones((n, n, 3)) * hexrgb(base) * (tone * (1 + .07 * grain + .05 * fine))[..., None]
    rough = .55 + .05 * grain
    if boards and groove:
        fu = (u * boards) % 1
        g = np.minimum(fu, 1 - fu) * board < groove
        rgb[g] *= .45; rough = np.where(g, .8, rough)
    save(name, rgb, rough)


floor()
carpet()
mosaic()
ceiling()
oak('Wainscot48', 1024, 2.4, .15, 'B88D5E', .003)
oak('Oak48', 1024, 2.0, 0, 'A87445', 0, wave=.3)
