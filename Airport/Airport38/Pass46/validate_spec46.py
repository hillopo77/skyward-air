"""Pass46: check the spec offline, before any engine session.

Every placement is tested for: staying inside its room, overlapping an existing
authored instance, overlapping another new placement, intruding on the 1.9 m
route corridor, blocking an authored portal mouth, and standing on a seated NPC
anchor. Failures print and set a non-zero exit, so a bad number never reaches
the engine.
"""
import json, sys, math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
D = json.loads((ROOT / 'Airport/Airport38/Exports/airport_layout.json').read_text(encoding='utf-8'))
B = json.loads((HERE / 'asset_bounds46.json').read_text(encoding='utf-8'))
SPEC = json.loads((HERE / 'Spec46.json').read_text(encoding='utf-8'))

CLEAR = SPEC['route_clear_width_m']
WALL_GAP = -0.02          # allow 2 cm of intentional contact with a wall plane
zones = {z['id']: z for z in D['zones']}
floors = {f['name']: f for f in D['floors']}


def foot(asset, yaw, scale):
    """Axis-aligned half-extents in world x,y and the height, after yaw."""
    s = B[asset]['size']
    sx, sy = s[0] * scale[0], s[1] * scale[1]
    r = math.radians(yaw)
    hx = (abs(sx * math.cos(r)) + abs(sy * math.sin(r))) / 2.0
    hy = (abs(sx * math.sin(r)) + abs(sy * math.cos(r))) / 2.0
    return hx, hy, s[2] * scale[2]


def rect(loc, asset, yaw, scale):
    hx, hy, _ = foot(asset, yaw, scale)
    return (loc[0] - hx, loc[0] + hx, loc[1] - hy, loc[1] + hy)


def overlap(a, b, pad=0.0):
    return (a[0] < b[1] - pad and b[0] < a[1] - pad
            and a[2] < b[3] - pad and b[2] < a[3] - pad)


def area(a):
    return max(0.0, a[1] - a[0]) * max(0.0, a[3] - a[2])


# Existing geometry comes from the LIVE level, not the authored layout: the
# two differ by 1504 removed instances. Validating against the layout invents
# collisions with props the game does not have and misses ones it does.
INV = HERE / 'Inventory46.json'
assert INV.exists(), 'run Run-Inventory46.ps1 first; the live level is the truth here'
inv = json.loads(INV.read_text(encoding='utf-8'))['actors']

SKIP_PREFIX = ('Airport38 coherent', 'Airport38 complete', 'Airport38 role-based',
               'Airport38 verified', 'Airport38 exterior glazing',
               'Airport38 mounted', 'Airport38 retained', 'Airport39 fitted',
               'Airport39 restrained', 'Airport43 fitted', 'Airport43 baggage',
               'Finished Grounds34', 'SkyCloudDome', 'Apron service details34',
               'Crafted GalleryStair35', 'Asphalt12_', 'CAM_', 'PH_',
               'Airport clean daylight', 'Airport26 journey', 'PostProcessVolume')

existing = []
for r in inv:
    if not r.get('mesh'):
        continue
    if r['actor'].startswith(SKIP_PREFIX):
        continue
    c, e = r.get('centre_m'), r.get('extent_cm')
    if not c or not e:
        continue
    if max(e) > 700:            # union actors and the shell
        continue
    existing.append((r['actor'], c[2],
                     (c[0] - e[0] / 100.0, c[0] + e[0] / 100.0,
                      c[1] - e[1] / 100.0, c[1] + e[1] / 100.0)))

# anything this spec moves is counted at its NEW place, not its old one
moved_names = {m['actor'] for m in SPEC['move']}
existing = [q for q in existing if q[0] not in moved_names]
for m in SPEC['move']:
    src = next((r for r in inv if r['actor'] == m['actor']), None)
    if src is None or not m.get('to'):
        continue
    e = src['extent_cm']
    existing.append((m['actor'], m['to'][2],
                     (m['to'][0] - e[0] / 100.0, m['to'][0] + e[0] / 100.0,
                      m['to'][1] - e[1] / 100.0, m['to'][1] + e[1] / 100.0)))

# route corridors to protect
corridors = []
for path, label in ((D['detail36']['main_route'], 'main route'),
                    (D['wayfinding26']['gold_route'], 'gold route'),
                    (D['wayfinding26']['blue_route'], 'blue route')):
    for i in range(len(path) - 1):
        corridors.append((label, path[i], path[i + 1]))

seated = [(c['name'], c['location']) for c in D['character_placements']
          if 'Seated' in str(c.get('animation', ''))]
# NPC collision proxies are solid in the level but a chair tucked under a
# table legitimately touches them, so they are not treated as obstacles.
existing = [q for q in existing if not q[0].startswith('CH12COLL ')]

portal_mouths = []
for p in D['portals']:
    x, y = p['point']
    w = p['width_m'] / 2.0
    if p['axis'] == 'y':          # opening in a wall at x = const, spans y
        portal_mouths.append((p['kind'], (x - 0.65, x + 0.65, y - w, y + w)))
    else:
        portal_mouths.append((p['kind'], (x - w, x + w, y - 0.65, y + 0.65)))


def seg_rect_dist(p0, p1, r):
    """Shortest distance from a segment to an axis-aligned rect, 0 if touching."""
    best = 1e9
    n = 40
    for i in range(n + 1):
        t = i / n
        x = p0[0] + (p1[0] - p0[0]) * t
        y = p0[1] + (p1[1] - p0[1]) * t
        dx = max(r[0] - x, 0.0, x - r[1])
        dy = max(r[2] - y, 0.0, y - r[3])
        best = min(best, math.hypot(dx, dy))
    return best


fail, warn = [], []
new = []
for q in SPEC['place']:
    name, asset = q['name'], q['asset']
    loc, yaw, sc = q['location'], q['rotation_degrees'], q['scale']
    r = rect(loc, asset, yaw, sc)
    hx, hy, h = foot(asset, yaw, sc)
    z = loc[2]

    # 1. inside its room
    if q['room'] == 'forecourt':
        # covered forecourt slab, plus the asphalt road west of it
        zr = [-70.0, -49.0, -40.0, 36.0]
    else:
        zr = zones[q['room']]['rect']
    if q['room'] == 'cafe' and z > 1.0:
        zr = floors['Gallery35 deck']['rect']
    if not (zr[0] - 0.05 <= r[0] and r[1] <= zr[1] + 0.05
            and zr[2] - 0.05 <= r[2] and r[3] <= zr[3] + 0.05):
        fail.append('%-34s leaves %s: rect [%.2f %.2f %.2f %.2f] vs [%.1f %.1f %.1f %.1f]'
                    % (name, q['room'], r[0], r[1], r[2], r[3], *zr))

    # 2. ceiling
    if q['room'] == 'forecourt':
        # open sky, except under the canopy: x -61..-52.95, y -21..-3.5, z<3.85
        CX, CY, CZ = (-61.0, -52.95), (-21.0, -3.5), 3.85
        under = (r[0] < CX[1] and CX[0] < r[1]
                 and r[2] < CY[1] and CY[0] < r[3])
        ceil = CZ if under else 1e9
    else:
        ceil = zones[q['room']]['ceiling_m']
    if q['room'] == 'cafe' and z > 1.0:
        ceil = 6.8          # absolute: z is absolute on the gallery deck too
    top = (h if asset != 'SM_AP_ScreenBoard' else z + B[asset]['size'][2] / 2.0)
    if asset == 'SM_AP_ScreenBoard':
        if top > ceil - 0.05:
            fail.append('%-34s board top %.2f exceeds ceiling %.2f' % (name, top, ceil))
    elif z + h > ceil - 0.05:
        fail.append('%-34s height %.2f exceeds ceiling %.2f' % (name, z + h, ceil))

    # 3. against existing instances at the same level
    for (en, ez, er) in existing:
        if abs(ez - z) > 1.2:
            continue
        if overlap(r, er, 0.01):
            fail.append('%-34s overlaps existing %-28s by %.2f m2'
                        % (name, en, area((max(r[0], er[0]), min(r[1], er[1]),
                                           max(r[2], er[2]), min(r[3], er[3])))))

    # 4. against each other
    for (nn, nz, nr) in new:
        if abs(nz - z) > 1.2:
            continue
        if overlap(r, nr, 0.01):
            fail.append('%-34s overlaps new %-32s by %.2f m2'
                        % (name, nn, area((max(r[0], nr[0]), min(r[1], nr[1]),
                                           max(r[2], nr[2]), min(r[3], nr[3])))))

    # 5. route clearance - a wall-mounted board does not stand on the floor,
    #    and the authored routes are all inside the terminal
    if asset != 'SM_AP_ScreenBoard' and z < 1.0 and q['room'] != 'forecourt':
        for label, p0, p1 in corridors:
            d = seg_rect_dist(p0, p1, r)
            if d < CLEAR / 2.0:
                fail.append('%-34s is %.2f m from the %s, inside the %.2f m half-corridor'
                            % (name, d, label, CLEAR / 2.0))

    # 6. portal mouths
    if asset != 'SM_AP_ScreenBoard' and q['room'] != 'forecourt':
        for kind, pm in portal_mouths:
            if overlap(r, pm, 0.01):
                fail.append('%-34s blocks the %s portal mouth' % (name, kind))

    # 7. seated NPC anchors
    for cn, cl in seated:
        if abs(cl[2] - z) > 1.2:
            continue
        if r[0] - 0.3 <= cl[0] <= r[1] + 0.3 and r[2] - 0.3 <= cl[1] <= r[3] + 0.3:
            fail.append('%-34s stands on seated anchor %s' % (name, cn))

    new.append((name, z, r))

# moved actors get the same treatment, except the ones mounted off the floor
for m in SPEC['move']:
    if m.get('snap') is False:
        continue          # a wall/door-mounted plate is not a floor placement
    src = next((q for q in D['instances'] if q['name'] == m['actor']), None)
    if src is None:
        fail.append('move target not in the layout: %s' % m['actor'])
        continue
    r = rect(m['to'], src['asset'], m['yaw'], src.get('scale') or [1, 1, 1])
    z = m['to'][2]
    for (en, ez, er) in existing:
        if en == m['actor'] or abs(ez - z) > 1.2:
            continue
        if overlap(r, er, 0.01):
            fail.append('moved %-28s overlaps %-28s by %.2f m2'
                        % (m['actor'], en, area((max(r[0], er[0]), min(r[1], er[1]),
                                                 max(r[2], er[2]), min(r[3], er[3])))))
    for (nn, nz, nr) in new:
        if abs(nz - z) > 1.2:
            continue
        if overlap(r, nr, 0.01):
            fail.append('moved %-28s overlaps new %-28s' % (m['actor'], nn))
    for cn, cl in seated:
        if abs(cl[2] - z) > 1.2:
            continue
        if r[0] - 0.3 <= cl[0] <= r[1] + 0.3 and r[2] - 0.3 <= cl[1] <= r[3] + 0.3:
            fail.append('moved %-28s stands on seated anchor %s' % (m['actor'], cn))

# The player spawns at the authored start and walks east to the entrance
# portal. Nothing placed outdoors may stand in that approach.
START = D['start']
ENTRY = [-49.0, -12.5]
for q in SPEC['place']:
    if q['room'] != 'forecourt':
        continue
    r = rect(q['location'], q['asset'], q['rotation_degrees'], q['scale'])
    d = seg_rect_dist([START[0], START[1]], ENTRY, r)
    if d < CLEAR / 2.0:
        fail.append('%-34s is %.2f m from the start-to-entrance walk, inside the '
                    '%.2f m half-corridor' % (q['name'], d, CLEAR / 2.0))

print('checked %d placements, %d moves, %d variations, %d collision fixes'
      % (len(SPEC['place']), len(SPEC['move']), len(SPEC['vary']),
         len(SPEC.get('collide', []))))
if warn:
    print()
    for w in warn:
        print('  warn  ' + w)
if fail:
    print()
    print('%d FAILURES' % len(fail))
    for f in fail:
        print('  FAIL  ' + f)
    sys.exit(1)
print('all clear')
