"""Pass46 / P46-015: can the twelve walk-through items be made solid?

The journey's walk is physical, not a trace: journey38_review.tick drives the
pawn with add_movement_input and only passes a leg when the pawn gets within
16 cm of the goal inside 18 s. walk_obstacles() is a diagnostic printed on
failure, not the test. So the question is purely whether the pawn's collision
shape can still get down each lane.

The pawn is BP_ArtTourPawn_C, measured in the live level at z = 1.62 with a
z half-extent of 35.0 cm: a DefaultPawn sphere of radius 0.35 m, no gravity
(FloatingPawnMovement) and d.z forced to 0 in the walk operator. Its collision
therefore occupies the band z 1.27 .. 1.97 and nothing else.

That has a consequence worth stating plainly: an obstacle whose top is below
1.27 m cannot obstruct the player at all, whatever its collision setting.

This script reconstructs every walk leg of the flight journey from the two
specifications the runtime actually composes, and reports, per candidate actor,
the closest approach of any leg to its bounding box. Offline and exact; no
engine required.
"""
import json, math, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'Fixes' / '05_journey'))

PAWN_Z, PAWN_R = 1.62, 0.35
BAND = (PAWN_Z - PAWN_R, PAWN_Z + PAWN_R)
SKIN = 0.05                      # movement sweep needs a little more than r

CANDIDATES = ['X-ray scanner 01', 'X-ray scanner 02',
              'Queue post31 0', 'Queue post31 1', 'Queue post31 2',
              'Queue post31 3', 'Queue post31 4', 'Queue post31 5',
              'Stanchion24_1725', 'Stanchion24_1726',
              'Stanchion24_1738', 'Stanchion24_1739']
# Not in scope, but reported because they share the lanes and would be the
# next obvious candidates.
CONTEXT = ['Queue ribbon31 6', 'Queue ribbon31 7', 'Queue ribbon31 8',
           'Queue ribbon31 9', 'Queue entry marker29',
           'Scanner 01 front curtain38', 'Scanner 01 rear curtain38',
           'Scanner 02 front curtain38', 'Scanner 02 rear curtain38',
           'CH12COLL Queue passenger 3', 'CH12COLL Queue passenger 6']


def legs():
    """Every walk leg of the flight journey, in order, as (from, to) in metres.

    Mirrors journey38_review.start(flight=True): the contract's fresh_start,
    with the scanner specification spliced in at the 'security true only'
    assert and the bag-collection detour inserted after the registered_bags
    wait. The aircraft-cabin legs are excluded; they are 60 m away from
    anything in scope and need a live frame transform to place.
    """
    import qa_contract38, qa_scanner38
    layout = json.loads((ROOT / 'Exports' / 'airport_layout.json')
                        .read_text(encoding='utf-8'))
    raw = qa_contract38.specification(layout)['fresh_start']
    scan = qa_scanner38.specification(layout)['steps']
    first = next(i for i, s in enumerate(scan)
                 if s.get('action') == 'assert'
                 and "and not G.S['security'] and 'Physical luggage 01'"
                 in s.get('predicate', ''))
    out = []
    for q in raw:
        if q.get('action') == 'assert' and \
           q.get('predicate', '').startswith('security true only'):
            for s in scan[first:]:
                if s.get('action') == 'walk':
                    out.append(s['points'])
            continue
        if q.get('action') == 'walk':
            out.append(q['points'])
        if q.get('action') == 'wait' and 'registered_bags' in q.get('until', ''):
            out.append([[-32.1, -15.8, 1.62], [-39, -15.8, 1.62],
                        [-42, -15, 1.62], [-45.2, -15, 1.62],
                        [-46, -15.8, 1.62]])
            out.append([[-45.2, -15, 1.62], [-42, -15, 1.62], [-39, -11, 1.62]])
    # The pawn walks from wherever it is, so a leg also runs between the last
    # point of one walk block and the first of the next.
    seq, prev = [], None
    for block in out:
        for p in block:
            if prev is not None:
                seq.append((prev, p))
            prev = p
    return [((a[0], a[1]), (b[0], b[1])) for a, b in seq]


def seg_box_gap(p, q, lo, hi):
    """Shortest distance in plan from segment pq to the axis-aligned rect."""
    def point_gap(x, y):
        dx = max(lo[0] - x, 0.0, x - hi[0])
        dy = max(lo[1] - y, 0.0, y - hi[1])
        return math.hypot(dx, dy)
    best = min(point_gap(*p), point_gap(*q))
    # Walk the segment finely; 1 cm steps are far below the decision margin.
    n = max(2, int(math.dist(p, q) * 100))
    for i in range(n + 1):
        t = i / n
        best = min(best, point_gap(p[0] + (q[0] - p[0]) * t,
                                   p[1] + (q[1] - p[1]) * t))
        if best == 0.0:
            break
    return best


def main():
    inv = json.loads((ROOT / 'Pass46' / 'Inventory46.json')
                     .read_text(encoding='utf-8'))
    by_name = {a['actor']: a for a in inv['actors']}
    L = legs()
    print('flight-journey terminal walk legs: %d' % len(L))
    print('pawn collision band z %.2f .. %.2f m, radius %.2f m (+%.2f skin)\n'
          % (BAND[0], BAND[1], PAWN_R, SKIN))

    rows = []
    for name in CANDIDATES + CONTEXT:
        a = by_name.get(name)
        if a is None:
            rows.append((name, None, None, None, 'NOT IN LEVEL'))
            continue
        c, e = a['centre_m'], a['extent_cm']
        lo = (c[0] - e[0] / 100.0, c[1] - e[1] / 100.0)
        hi = (c[0] + e[0] / 100.0, c[1] + e[1] / 100.0)
        top, bot = c[2] + e[2] / 100.0, c[2] - e[2] / 100.0
        reaches = top > BAND[0] and bot < BAND[1]
        gap, where = min(((seg_box_gap(p, q, lo, hi), (p, q)) for p, q in L),
                         key=lambda t: t[0])
        if not reaches:
            verdict = 'SAFE: top %.3f m is below the pawn band' % top
        elif gap >= PAWN_R + SKIN:
            verdict = 'SAFE: %.3f m clear, needs %.2f m' % (gap, PAWN_R + SKIN)
        else:
            verdict = 'BLOCKS: only %.3f m clear, needs %.2f m' % (
                gap, PAWN_R + SKIN)
        rows.append((name, top, gap, where, verdict))

    w = max(len(r[0]) for r in rows)
    for name, top, gap, where, verdict in rows:
        scope = 'scope ' if name in CANDIDATES else '     '
        if top is None:
            print('%s%-*s  %s' % (scope, w, name, verdict))
            continue
        print('%s%-*s top=%5.3f  nearest leg gap=%6.3f m  %s'
              % (scope, w, name, top, gap, verdict))
        if 'BLOCKS' in verdict:
            print('%s%-*s   worst leg %s -> %s' % (' ' * 6, w, '', where[0],
                                                   where[1]))

    bad = [r for r in rows if r[0] in CANDIDATES and 'BLOCKS' in r[4]]
    print('\nin-scope items that would block the pawn: %d' % len(bad))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
