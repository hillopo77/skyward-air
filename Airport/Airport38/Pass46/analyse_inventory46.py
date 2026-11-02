"""Pass46: judge the whole-game inventory offline.

One engine pass produced Inventory46.json; every check below runs against that
file, so a wrong judgment costs a re-run of this script rather than a fresh
engine session. That is the lesson from Pass45, where three wrong calls each
cost a launch.
"""
import json, math, sys
from pathlib import Path
from collections import defaultdict

HERE = Path(__file__).resolve().parent
D = json.loads((HERE / 'Inventory46.json').read_text(encoding='utf-8'))
LAY = json.loads((HERE.parents[0] / 'Exports/airport_layout.json').read_text(encoding='utf-8'))
rows = D['actors']
zones = LAY['zones']

print('=' * 100)
print('INVENTORY  %d actors, %d support-traced, method: %s'
      % (D['counted'], D['traced'], D['method']['rule']))
print('=' * 100)

by_class = defaultdict(int)
for r in rows:
    by_class[r['cls']] += 1
print('classes: ' + ', '.join('%s x%d' % (k, v) for k, v in
                              sorted(by_class.items(), key=lambda kv: -kv[1])[:10]))
tris = sum(r.get('triangles') or 0 for r in rows)
print('total triangles in placed actors: %s' % format(tris, ','))

# ------------------------------------------------------------ 1. unsupported
print()
print('-' * 100)
print('1. UNSUPPORTED after a 54-ray fan  (Pass45 used one ray per face centre)')
print('-' * 100)
bad = D['unsupported']
print('%-44s %-26s %s' % ('actor', 'centre m', 'extent cm'))
for q in sorted(bad, key=lambda q: q['actor']):
    print('%-44s %-26s %s' % (q['actor'][:43], str(q['centre_m']), q['extent_cm']))
print('%d unsupported' % len(bad))

PASS45 = ['CH12HAND L', 'CH12HAND R', 'Extinguisher powder effect',
          'Gate A07 flight display', 'Gate A08 flight display',
          'WC release 0 inside', 'WC release 1 inside',
          'Check-in service header29 0', 'Check-in service header29 1',
          'Queue ribbon31 6', 'Queue ribbon31 7', 'Queue ribbon31 8',
          'Queue ribbon31 9', 'Gallery bench24 0', 'Gallery bench24 1',
          'Crafted GalleryStair35', 'Gallery waste sorting36',
          'Ground crew parking bay38', 'Airport43 baggage service backdrop']
now = {q['actor'] for q in bad}
print()
print('Pass45 called these unsupported. Corrected verdict:')
for n in PASS45:
    print('  %-42s %s' % (n, 'STILL unsupported' if n in now else 'cleared - it was the single-ray artifact'))

# ----------------------------------------------------- 2. material problems
print()
print('-' * 100)
print('2. MATERIAL SLOTS unassigned or left on an engine default')
print('-' * 100)
n = 0
for r in rows:
    if r.get('missing_slots'):
        n += 1
        if n <= 25:
            print('%-46s %-28s slots %s' % (r['actor'][:45], str(r.get('mesh'))[:27],
                                            r.get('slots')))
print('%d actors with a bad material slot' % n)

# ----------------------------------------------------- 3. degenerate transforms
print()
print('-' * 100)
print('3. DEGENERATE transforms  (zero/negative/extreme scale, non-finite)')
print('-' * 100)
n = 0
for r in rows:
    s = r.get('scale') or [1, 1, 1]
    bad_s = any((not math.isfinite(v)) or abs(v) < 1e-4 or abs(v) > 60 or v < 0 for v in s)
    loc = r.get('loc_m') or [0, 0, 0]
    bad_l = any(not math.isfinite(v) for v in loc)
    if bad_s or bad_l:
        n += 1
        if n <= 20:
            print('%-46s scale %s loc %s' % (r['actor'][:45], s, loc))
print('%d degenerate' % n)

# ------------------------------------------------- 4. duplicate placements
print()
print('-' * 100)
print('4. DUPLICATE PLACEMENTS  (same mesh within 2 cm; co-located geometry)')
print('-' * 100)
buckets = defaultdict(list)
for r in rows:
    if not r.get('mesh'):
        continue
    c = r['centre_m']
    buckets[(r['mesh'], round(c[0], 2), round(c[1], 2), round(c[2], 2))].append(r['actor'])
n = 0
for k, names in sorted(buckets.items()):
    if len(names) > 1:
        n += 1
        if n <= 25:
            print('%-30s at %-26s x%d  %s' % (k[0][:29], str(k[1:]), len(names),
                                              ', '.join(x[:26] for x in names[:4])))
print('%d duplicate groups' % n)

# ------------------------------------------- 5. actors outside the envelope
print()
print('-' * 100)
print('5. OUTSIDE THE PLAYABLE ENVELOPE  (below the lowest floor, or far out)')
print('-' * 100)
n = 0
for r in rows:
    c = r.get('centre_m') or [0, 0, 0]
    e = r.get('extent_cm') or [0, 0, 0]
    low = c[2] - e[2] / 100.0
    if low < -5.0 or abs(c[0]) > 400 or abs(c[1]) > 900:
        n += 1
        if n <= 20:
            print('%-46s centre %s  bottom %.2f m' % (r['actor'][:45], str(c), low))
print('%d outside' % n)

# ------------------------------- 6. visible actors with collision disabled
print()
print('-' * 100)
print('6. SOLID-LOOKING BUT NOT SOLID  (visible, prop-sized, no collision)')
print('-' * 100)
n = 0
for r in rows:
    if not r.get('visible') or not r.get('mesh'):
        continue
    e = r.get('extent_cm') or [0, 0, 0]
    if max(e) < 20:
        continue
    ce = str(r.get('collision_enabled', ''))
    if 'NO_COLLISION' in ce.upper() or ce.endswith('NoCollision'):
        n += 1
        if n <= 25:
            print('%-46s %-26s extent %s' % (r['actor'][:45], str(r.get('mesh'))[:25], e))
print('%d visible actors with collision off' % n)

# ----------------------------------------------- 7. per-zone density, live
print()
print('-' * 100)
print('7. PER-ZONE DENSITY from the live level (not just authored instances)')
print('-' * 100)


def zone_of(c):
    best = None
    for z in zones:
        x0, x1, y0, y1 = z['rect']
        if x0 <= c[0] <= x1 and y0 <= c[1] <= y1:
            a = (x1 - x0) * (y1 - y0)
            if best is None or a < best[1]:
                best = (z, a)
    return best[0] if best else None


cnt = defaultdict(int)
for r in rows:
    c = r.get('centre_m')
    e = r.get('extent_cm') or [0, 0, 0]
    if not c or not r.get('mesh'):
        continue
    if max(e) > 700 or max(e) < 5:
        continue            # union actors and specks
    if c[2] > 4.0:
        continue            # ceiling kit
    z = zone_of(c)
    if z:
        cnt[z['id']] += 1
print('%-18s %7s %6s %8s' % ('zone', 'area', 'actors', 'per100'))
for z in sorted(zones, key=lambda z: (cnt[z['id']] /
                                      ((z['rect'][1] - z['rect'][0]) *
                                       (z['rect'][3] - z['rect'][2])) * 100)):
    x0, x1, y0, y1 = z['rect']
    a = (x1 - x0) * (y1 - y0)
    print('%-18s %7.0f %6d %8.1f' % (z['id'], a, cnt[z['id']], cnt[z['id']] / a * 100))

# ------------------------------------------- 8. the lavatory privacy plates
print()
print('-' * 100)
print('8. LAVATORY / WC assembly, every actor in or near the amenities room')
print('-' * 100)
print('%-46s %-26s %-22s %s' % ('actor', 'centre m', 'extent cm', 'mesh'))
for r in sorted(rows, key=lambda r: (r.get('centre_m') or [0])[0]):
    c = r.get('centre_m')
    if not c:
        continue
    if not (-26.5 <= c[0] <= -13.5 and -12.5 <= c[1] <= -2.5):
        continue
    e = r.get('extent_cm') or [0, 0, 0]
    if max(e) > 600:
        continue
    print('%-46s %-26s %-22s %s' % (r['actor'][:45], str(c), str(e),
                                    str(r.get('mesh'))[:22]))
