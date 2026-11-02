"""Pass47: original terminal ambience, synthesised locally. No downloads, no paid
generation; Blender's bundled numpy does the signal work, the announcer voice
is Windows' offline speech engine (recorded by Make-Voice47 into Audio/src).

Every loop is built in the frequency domain - a shaped spectrum with random
phases, inverse-FFT'd - so it is exactly periodic and loops with no seam.

  RoomTone47  air-handling hush of a large interior, a little 120 Hz
  Murmur47    distant crowd: fourteen band-limited "voices" with syllable and
              phrase envelopes, heard through a room (top end rolled off)
  Outdoor47   breeze in slow gusts over distant road rumble
  Apron47     a parked aircraft's APU idle: harmonic whine, hiss and rumble
  PA47        a 120 s loop: three-tone chime, then an announcement, four times,
              band-limited like a ceiling speaker, with a short hall tail

Usage: blender -b --factory-startup -P audio47_blender.py -- <pass47_dir>
"""
import sys, wave, json
from pathlib import Path
import numpy as np

ROOT = Path(sys.argv[sys.argv.index('--') + 1])
OUT = ROOT / 'Audio'
RATE = 22050
rng = np.random.default_rng(4747)


def shaped_noise(seconds, mag):
    """Periodic noise whose magnitude spectrum is mag(f)."""
    n = int(RATE * seconds)
    f = np.fft.rfftfreq(n, 1 / RATE)
    spec = mag(np.maximum(f, 1e-3)) * np.exp(1j * rng.uniform(0, 2 * np.pi, f.size))
    spec[0] = 0
    x = np.fft.irfft(spec, n)
    return x / (np.abs(x).max() + 1e-9)


def band(lo, hi, slope=6.0):
    def m(f):
        return 1 / (1 + (lo / f) ** slope) / (1 + (f / hi) ** slope)
    return m


def periodic_env(seconds, hz, sharp=1.0):
    """A smooth random envelope, periodic over the loop, centred ~0.5."""
    e = shaped_noise(seconds, band(hz * 0.3, hz, 4))
    e = (e - e.min()) / (e.max() - e.min() + 1e-9)
    return e ** sharp


def norm(x, rms):
    return x * (rms / (np.sqrt((x ** 2).mean()) + 1e-9))


def write(name, x):
    x = np.clip(x, -0.98, 0.98)
    pcm = (x * 32767).astype('<i2').tobytes()
    with wave.open(str(OUT / (name + '.wav')), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE); w.writeframes(pcm)
    return dict(name=name, seconds=round(len(x) / RATE, 2),
                rms=round(float(np.sqrt((x ** 2).mean())), 4), peak=round(float(np.abs(x).max()), 3))


def tone_loop(seconds, freq):
    """A sine with a whole number of cycles in the loop, so it stays seamless."""
    n = int(RATE * seconds)
    cycles = round(freq * seconds)
    return np.sin(2 * np.pi * cycles * np.arange(n) / n)


def room_tone():
    s = 10.0
    hush = shaped_noise(s, lambda f: band(35, 1800, 3)(f) / f ** 0.6)
    hum = 0.08 * tone_loop(s, 120) + 0.03 * tone_loop(s, 240)
    return norm(hush + hum, 0.045)


def murmur():
    s = 20.0
    n = int(RATE * s)
    x = np.zeros(n)
    for v in range(14):
        lo = rng.uniform(220, 420)
        hi = rng.uniform(900, 1700)
        voice = shaped_noise(s, band(lo, hi, 4))
        syll = periodic_env(s, rng.uniform(3.0, 5.5), 2.2)
        phrase = periodic_env(s, rng.uniform(0.15, 0.35), 1.5)
        # Smooth phrase gate: a hard threshold would switch noise on and off
        # instantly and click. Smoothstep over 0.25..0.45 fades it instead.
        g = np.clip((phrase - 0.25) / 0.2, 0, 1)
        x += voice * syll * g * g * (3 - 2 * g) * rng.uniform(0.5, 1.0)
    # Heard across a room: soften the top end through the same periodic FFT.
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / RATE)
    spec *= 1 / (1 + (f / 1400.0) ** 4)
    x = np.fft.irfft(spec, n)
    return norm(x, 0.05)


def outdoor():
    s = 20.0
    wind = shaped_noise(s, lambda f: band(60, 700, 3)(f) / f ** 0.8)
    gust = 0.35 + 0.65 * periodic_env(s, 0.25, 1.4)
    road = shaped_noise(s, band(25, 160, 4))
    return norm(wind * gust + 0.6 * road, 0.055)


def apron():
    s = 12.0
    whine = sum(a * tone_loop(s, f) for f, a in ((412, 0.5), (824, 0.25), (1236, 0.12), (2061, 0.05)))
    wob = 0.85 + 0.15 * periodic_env(s, 0.5, 1.0)
    hiss = shaped_noise(s, band(1800, 6500, 4))
    rumble = shaped_noise(s, band(30, 180, 4))
    return norm(0.55 * whine * wob + 0.35 * hiss + 0.5 * rumble, 0.045)


def read_wav(p):
    with wave.open(str(p), 'rb') as w:
        assert w.getframerate() == RATE and w.getnchannels() == 1 and w.getsampwidth() == 2, p
        return np.frombuffer(w.readframes(w.getnframes()), dtype='<i2').astype(np.float64) / 32768


def chime():
    out = []
    for f in (784.0, 659.3, 523.3):              # G5 E5 C5, the classic descending chime
        t = np.arange(int(RATE * 0.75)) / RATE
        bell = (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2 * f * t)
                + 0.12 * np.sin(2 * np.pi * 3.01 * f * t))
        out.append(bell * np.exp(-t * 3.2) * np.minimum(1, t * 200))
    return np.concatenate(out) * 0.32


def speaker(x):
    """Ceiling-speaker band and a short hall tail."""
    n = len(x) + int(RATE * 0.8)
    f = np.fft.rfftfreq(n, 1 / RATE)
    spec = np.fft.rfft(x, n) * band(320, 3800, 4)(np.maximum(f, 1e-3))
    ir_t = np.arange(int(RATE * 0.8)) / RATE
    ir = rng.standard_normal(ir_t.size) * np.exp(-ir_t * 7.5) * 0.18
    ir[0] = 1.0
    y = np.fft.irfft(spec * np.fft.rfft(ir, n), n)
    return y / (np.abs(y).max() + 1e-9) * 0.62


def pa():
    s = 120.0
    x = np.zeros(int(RATE * s))
    ch = chime()
    starts = []
    for k, at in enumerate((2.0, 32.0, 62.0, 92.0)):
        voice = speaker(read_wav(ROOT / 'Audio' / 'src' / ('pa_%d.wav' % (k + 1))))
        i = int(RATE * at)
        x[i:i + ch.size] += ch
        j = i + ch.size + int(RATE * 0.35)
        x[j:j + voice.size] += voice[: max(0, min(voice.size, x.size - j))]
        starts.append(dict(chime_s=at, voice_s=round(j / RATE, 2), voice_len_s=round(voice.size / RATE, 2)))
    return x, starts


OUT.mkdir(parents=True, exist_ok=True)
report = [write('RoomTone47', room_tone()), write('Murmur47', murmur()),
          write('Outdoor47', outdoor()), write('Apron47', apron())]
p, starts = pa()
report.append(dict(write('PA47', p), announcements=starts))
(ROOT / 'Audio47.json').write_text(json.dumps(report, indent=1), encoding='utf-8')
print('AUDIO47', [r['name'] for r in report])
