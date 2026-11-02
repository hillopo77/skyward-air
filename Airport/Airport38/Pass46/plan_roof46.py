"""Pass46 / P46-006: place rooftop plant on measured, flat roof.

Input is the -game roof survey (Roof46_before.json): a 1 m grid of down-traces
over the terminal, each recording the first surface and its actor. Output is
Roof46Spec.json for build_roof46.py.

Rules, so nothing reads as dropped on from above:
  - a unit goes only where every survey point under its footprint plus a
    margin hit the roof at one height (within 3 cm), so it never overhangs a
    roof step, an edge, a rooflight or the glazing
  - units keep 1.2 m clear of each other
  - each unit serves a room: air-handling over the big public rooms, kitchen
    extract over the cafe, WC extract over the amenities, and so on, placed as
    near that room's centre as the rules allow
  - walkways and cable trays only run on one roof level, so a paver or tray
    never spans a step

Offline; no engine.
"""
import json, math, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAYOUT = HERE.parent / 'Exports' / 'airport_layout.json'

# Local footprints at yaw 0: (x_min, x_max, y_min, y_max), from build_roof46.
FOOT = dict(ahu=(-2.75, 2.10, -0.82, 0.82), condenser=(-1.30, 1.30, -0.62, 0.62),
            exhaust=(-0.36, 0.36, -0.36, 0.36), gooseneck=(-0.18, 0.40, -0.18, 0.18),
            hatch=(-0.82, 0.82, -0.64, 0.82))
MARGIN = dict(ahu=1.0, condenser=0.9, exhaust=0.6, gooseneck=0.5, hatch=0.9)
CLEAR = 1.2
FLAT_TOL = 0.03

# What each room's roof carries. Order matters: big units first.
WANT = [
    ('checkin', 'ahu'), ('gate08', 'ahu'), ('security', 'ahu'),
    ('cafe', 'condenser'), ('cafe', 'exhaust'), ('cafe', 'exhaust'),
    ('concourse', 'condenser'), ('gate07', 'condenser'), ('arrivals', 'condenser'),
    ('amenities', 'exhaust'), ('amenities', 'exhaust'), ('amenities', 'exhaust'),
    ('checkin', 'gooseneck'), ('security', 'gooseneck'), ('gate08', 'gooseneck'),
    ('entrancefoyer', 'gooseneck'),
    # The access hatch goes on a roof level that also carries plant, so a
    # paver walkway can reach it without crossing a step.
    ('security', 'hatch'),
]


def footprint(kind, x, y, yaw, margin):
    x0, x1, y0, y1 = FOOT[kind]
    if yaw == 90:
        x0, x1, y0, y1 = -y1, -y0, x0, x1
    return (x + x0 - margin, x + x1 + margin, y + y0 - margin, y + y1 + margin)


def main():
    survey_path = HERE / (sys.argv[1] if len(sys.argv) > 1 else 'Roof46_before.json')
    S = json.loads(survey_path.read_text(encoding='utf-8'))['survey']
    zones = {z['id']: z for z in json.loads(LAYOUT.read_text(encoding='utf-8'))['zones']}
    pts = {}
    for x, y, z, actor in S['points']:
        pts[(round(x), round(y))] = (z, actor)
    # The roof is whatever is hit from above inside the terminal; report it.
    roof_actors = {}
    for (x, y), (z, a) in pts.items():
        if z is not None and z > 3.0:
            roof_actors[a] = roof_actors.get(a, 0) + 1
    roof_names = {a for a, n in roof_actors.items() if n >= 20}

    def flat_z(rect):
        x0, x1, y0, y1 = rect
        zs = []
        cells = [(xi, yi) for xi in range(math.floor(x0), math.ceil(x1) + 1)
                 for yi in range(math.floor(y0), math.ceil(y1) + 1)]
        inside = [(xi, yi) for xi, yi in cells
                  if x0 - 1e-6 <= xi <= x1 + 1e-6 and y0 - 1e-6 <= yi <= y1 + 1e-6]
        # A rect smaller than the 1 m survey pitch can hold no samples at all;
        # then judge it by every corner of the cells it touches, which is the
        # conservative reading rather than an automatic rejection.
        for xi, yi in (inside if len(inside) >= 4 else cells):
            if True:
                z, a = pts.get((xi, yi), (None, None))
                if z is None or a not in roof_names:
                    return None
                zs.append(z)
        if len(zs) < 2 or max(zs) - min(zs) > FLAT_TOL:
            return None
        return sum(zs) / len(zs)

    placed, rejected = [], []
    for zone_id, kind in WANT:
        zx0, zx1, zy0, zy1 = zones[zone_id]['rect']
        cx, cy = (zx0 + zx1) / 2, (zy0 + zy1) / 2
        best = None
        for i in range(int((zx1 - zx0) * 2) + 1):
            for j in range(int((zy1 - zy0) * 2) + 1):
                x, y = zx0 + i * 0.5, zy0 + j * 0.5
                for yaw in (0, 90):
                    core = footprint(kind, x, y, yaw, 0.0)
                    # The unit itself must sit over its own room.
                    if core[0] < zx0 or core[1] > zx1 or core[2] < zy0 or core[3] > zy1:
                        continue
                    z = flat_z(footprint(kind, x, y, yaw, MARGIN[kind]))
                    if z is None:
                        continue
                    ok = True
                    for q in placed:
                        a = footprint(kind, x, y, yaw, CLEAR / 2)
                        b = footprint(q['type'], q['x'], q['y'], q['yaw'], CLEAR / 2)
                        if a[0] < b[1] and b[0] < a[1] and a[2] < b[3] and b[2] < a[3]:
                            ok = False
                            break
                    if not ok:
                        continue
                    d = math.hypot(x - cx, y - cy)
                    if best is None or d < best[0]:
                        best = (d, dict(type=kind, x=x, y=y, z=round(z, 3), yaw=yaw,
                                        zone=zone_id))
        if best:
            placed.append(best[1])
        else:
            rejected.append(dict(zone=zone_id, type=kind,
                                 reason='no flat roof for its footprint plus margin'))

    # Walkway from the hatch to the nearest unit on the same roof level, and a
    # cable tray between same-level big units, as dog-leg polylines that are
    # checked flat along their whole run.
    def run_flat(points, z, half):
        """Flat at one level along the whole run, and through no unit at all -
        including the two it connects, whose faces it must stop short of."""
        for (x0, y0), (x1, y1) in zip(points, points[1:]):
            n = max(1, int(math.hypot(x1 - x0, y1 - y0) / 0.25))
            for k in range(n + 1):
                x, y = x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n
                zz = flat_z((x - half, x + half, y - half, y + half))
                if zz is None or abs(zz - z) > FLAT_TOL:
                    return 'not flat at (%.2f, %.2f)' % (x, y)
                for q in placed:
                    f = footprint(q['type'], q['x'], q['y'], q['yaw'], 0.05)
                    if f[0] < x < f[1] and f[2] < y < f[3]:
                        return 'crosses %s %s at (%.2f, %.2f)' % (q['zone'], q['type'], x, y)
        return None

    def routes(start, end, target):
        f = footprint(target['type'], target['x'], target['y'], target['yaw'], 0.0)
        yield [start, [start[0], end[1]], end]
        yield [start, [end[0], start[1]], end]
        for xw in (f[0] - 0.9, f[1] + 0.9):
            yield [start, [xw, start[1]], [xw, end[1]], end]

    walkways, trays, notes = [], [], []
    hatch = next((q for q in placed if q['type'] == 'hatch'), None)
    if hatch:
        same = sorted((q for q in placed if q is not hatch and q['type'] in ('ahu', 'condenser')
                       and abs(q['z'] - hatch['z']) < FLAT_TOL),
                      key=lambda q: math.hypot(q['x'] - hatch['x'], q['y'] - hatch['y']))
        for q in same[:2]:
            # From the hatch's open (-y) side to the unit's service (-y) side.
            start = [hatch['x'], hatch['y'] - 1.0]
            end = [q['x'], q['y'] - (1.6 if q['yaw'] == 0 else 3.3)]
            for path in routes(start, end, q):
                why = run_flat(path, hatch['z'], 0.32)
                if why is None:
                    walkways.append(dict(z=hatch['z'], points=path, to=q['zone']))
                    break
                notes.append('walkway to %s rejected: %s' % (q['zone'], why))
    big = [q for q in placed if q['type'] in ('ahu', 'condenser')]
    for a in big:
        for b in big:
            if a is b or abs(a['z'] - b['z']) > FLAT_TOL or a['zone'] >= b['zone']:
                continue
            if math.hypot(a['x'] - b['x'], a['y'] - b['y']) > 18:
                continue
            start, end = [a['x'], a['y'] + 1.3], [b['x'], b['y'] + 1.3]
            for path in routes(start, end, b):
                why = run_flat(path, a['z'], 0.2)
                if why is None:
                    trays.append(dict(z=a['z'], points=path, between=[a['zone'], b['zone']]))
                    break
                notes.append('tray %s-%s rejected: %s' % (a['zone'], b['zone'], why))

    spec = dict(units=placed, walkways=walkways, trays=trays,
                roof_actors=roof_actors, rejected=rejected, notes=notes,
                survey=str(survey_path.name))
    (HERE / 'Roof46Spec.json').write_text(json.dumps(spec, indent=1), encoding='utf-8')
    print('roof actors (>=20 hits):', sorted(roof_names))
    for q in placed:
        print('  %-10s %-14s at (%.1f, %.1f) z=%.3f yaw=%d' % (q['type'], q['zone'], q['x'],
                                                             q['y'], q['z'], q['yaw']))
    for r in rejected:
        print('  REJECTED', r)
    for n in notes:
        print('  note', n)
    print('walkways %d  trays %d' % (len(walkways), len(trays)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
