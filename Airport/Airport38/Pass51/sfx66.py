"""Pass66: synthesise Gameplay66's cartoon sound effects (plain Python + numpy, no downloads, no paid generation).

Writes 44.1 kHz 16-bit mono WAVs to Pass51/Sfx66/:
  SFX66_Hop     a short rising 'boing' with a little wobble
  SFX66_Land    a soft low thud with a felt-like tap
  SFX66_Grab    a bright 'bloop'
  SFX66_Throw   a quick whoosh (swept, filtered noise)
  SFX66_Slide   a longer, lower whoosh with a squeak at the start
  SFX66_Bonk    a hollow wood-block bonk with a low knock
  SFX66_Clang   a short metallic clang (inharmonic partials)
  SFX66_Sip     a little slurp
  SFX66_Equip   a soft double click
"""
import numpy as np, wave
from pathlib import Path

SR = 44100
OUT = Path(__file__).resolve().parent / 'Sfx66'
RNG = np.random.default_rng(66)


def t(sec):
    return np.arange(int(SR * sec)) / SR


def env(n, attack, decay_rate):
    x = np.arange(n) / SR
    a = np.clip(x / max(attack, 1e-4), 0, 1)
    return a * np.exp(-x * decay_rate)


def sweep(f0, f1, sec, curve=1.0):
    x = t(sec); k = (x / sec) ** curve
    f = f0 + (f1 - f0) * k
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def lowpass(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR); y = np.zeros_like(x); s = 0.0
    for i, v in enumerate(x):
        s = (1 - a) * v + a * s; y[i] = s
    return y


def bandsweep(noise, f0, f1):
    """Cheap moving band-pass: two one-pole low-passes with a swept cutoff, subtracted."""
    n = len(noise); y = np.zeros(n); lo = hi = 0.0
    for i in range(n):
        f = f0 + (f1 - f0) * i / n
        a1 = np.exp(-2 * np.pi * f * 1.6 / SR); a2 = np.exp(-2 * np.pi * f / 1.6 / SR)
        hi = (1 - a1) * noise[i] + a1 * hi; lo = (1 - a2) * noise[i] + a2 * lo
        y[i] = hi - lo
    return y


def save(name, x, gain=.8):
    x = x / max(1e-6, np.max(np.abs(x))) * gain
    fade = min(len(x), int(SR * .006))
    x[-fade:] *= np.linspace(1, 0, fade)
    data = (x * 32767).astype(np.int16)
    OUT.mkdir(exist_ok=True)
    with wave.open(str(OUT / (name + '.wav')), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(data.tobytes())


def main():
    sec = .26                                                      # hop: boing
    x = t(sec); f = 230 + 330 * (x / sec) ** .6 + 18 * np.sin(2 * np.pi * 26 * x)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) + .3 * np.sin(4 * np.pi * np.cumsum(f) / SR)
    save('SFX66_Hop', s * env(len(x), .004, 11), .55)

    x = t(.22)                                                     # land: thud
    s = sweep(110, 48, .22, .5) * env(len(x), .002, 22) + lowpass(RNG.normal(0, 1, len(x)), 900) * env(len(x), .001, 60) * 2.5
    save('SFX66_Land', s, .7)

    x = t(.1)                                                      # grab: bloop
    s = sweep(520, 980, .1, .7) * env(len(x), .003, 30)
    save('SFX66_Grab', s, .45)

    n = RNG.normal(0, 1, int(SR * .3))                              # throw: whoosh
    s = bandsweep(n, 500, 2600) * np.sin(np.pi * np.linspace(0, 1, len(n))) ** 1.5
    save('SFX66_Throw', s, .6)

    n = RNG.normal(0, 1, int(SR * .6))                              # slide: long low whoosh + squeak
    s = bandsweep(n, 900, 300) * np.sin(np.pi * np.linspace(0, 1, len(n))) ** .8
    sq = np.zeros_like(s); m = int(SR * .12)
    sq[:m] = sweep(1400, 1900, .12)[:m] * env(m, .005, 18) * .5
    save('SFX66_Slide', s / np.max(np.abs(s)) + sq, .55)

    x = t(.25)                                                     # bonk: wood block
    s = (np.sin(2 * np.pi * 760 * x) + .6 * np.sin(2 * np.pi * 1180 * x)) * env(len(x), .001, 28) + \
        sweep(160, 90, .25) * env(len(x), .001, 35) * 1.2
    save('SFX66_Bonk', s, .75)

    x = t(.6)                                                      # clang: metal
    s = sum(a * np.sin(2 * np.pi * f * x) * np.exp(-x * d) for f, a, d in ((523, 1, 7), (1311, .7, 9), (2147, .5, 12), (3020, .3, 16)))
    save('SFX66_Clang', s * np.clip(x / .002, 0, 1), .5)

    x = t(.45)                                                     # sip: slurp
    n = lowpass(RNG.normal(0, 1, len(x)), 2400) - lowpass(RNG.normal(0, 1, len(x)), 500)
    am = (.5 + .5 * np.sin(2 * np.pi * 14 * x)) * np.sin(np.pi * x / .45)
    save('SFX66_Sip', n * am + .2 * sweep(300, 520, .45) * am, .45)

    x = t(.12)                                                     # equip: double click
    c = np.zeros(len(x))
    for at in (0, .055):
        i = int(at * SR); m = int(SR * .02)
        c[i:i + m] += (RNG.normal(0, 1, m) * .5 + np.sin(2 * np.pi * 2400 * t(.02)[:m])) * env(m, .0005, 260)
    save('SFX66_Equip', c, .5)
    print('SFX66', sorted(p.name for p in OUT.glob('*.wav')))


main()
