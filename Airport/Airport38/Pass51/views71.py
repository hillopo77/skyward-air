"""Pass71/72: the photo sets, written into Pass50/Views50.json (entries replaced by name; re-runnable).

  S71_*   security, washrooms and WC passage from many angles
  P72_*   the cabin normal (_n) and in a panic (_p), from the same eyes; the flight deck and close-ups of
          its lit buttons. Panic photos use cabin68.S['force_panic'] = 'photo' (full panic, fixed phase)
  E71_*   every extinguisher cabinet from the front and from the side, from Pass48/Walls71.json
Usage: python views71.py
"""
import json, math
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIEWS = HERE.parent / 'Pass50' / 'Views50.json'
WALLS = HERE.parent / 'Pass48' / 'Walls71.json'
NORMAL = ["py import cabin68;cabin68.S['force_panic']=False"]
PANIC = ["py import cabin68;cabin68.S['force_panic']='photo'"]

new = [
    ['S71_sec_entry', [-42.0, -3.4, 1.65], [-42.0, 6.0, 1.3]],
    ['S71_sec_feature', [-38.0, 8.6, 1.7], [-48.8, 1.5, 1.7]],
    ['S71_sec_wall', [-46.4, 0.0, 1.6], [-49.0, 2.4, 1.95]],
    ['S71_sec_blade', [-44.3, -3.3, 1.6], [-44.3, 0.0, 2.2]],
    ['S71_sec_lane', [-45.5, -1.5, 1.6], [-45.5, 8.0, 1.2]],
    ['S71_sec_tunnel', [-43.15, 0.9, 1.4], [-43.15, 4.0, 1.3]],
    ['S71_sec_north', [-41.6, 5.8, 1.6], [-42.0, 10.0, 1.5]],
    ['S71_sec_back', [-37.2, 9.0, 1.7], [-44.0, -3.0, 1.1]],
    ['S71_sec_bench', [-37.6, -3.2, 1.6], [-37.0, -1.0, 1.2]],
    ['S71_wc_entry', [-22.4, -8.5, 1.6], [-16.0, -10.8, 1.3]],
    ['S71_wc_vanity', [-18.7, -8.1, 1.6], [-18.7, -12.0, 1.4]],
    ['S71_wc_basin', [-19.4, -10.5, 1.55], [-19.4, -11.7, 1.0]],
    ['S71_wc_fronts', [-18.6, -11.1, 1.6], [-18.6, -7.3, 1.7]],
    ['S71_wc_east', [-20.5, -9.5, 1.6], [-14.0, -9.5, 1.3]],
    ['S71_wc_west', [-15.0, -8.6, 1.6], [-23.0, -10.5, 1.4]],
    ['S71_wc_stall1', [-20.8, -7.0, 1.6], [-21.7, -5.4, .75]],
    ['S71_wc_stall4', [-17.12, -6.98, 1.62], [-17.12, -5.4, .7]],
    ['S71_wcp_n', [-24.5, -1.6, 1.6], [-24.5, -11.5, 1.1]],
    ['S71_wcp_s', [-24.5, -11.4, 1.6], [-24.5, -1.5, 1.1]],
    ['S71_wcp_bench', [-23.6, -6.3, 1.5], [-26.0, -6.3, 0.8]],
]
cabin = [('eco', [17.1, 27.0, 1.6], [17.1, 12.0, 1.4]), ('eco_back', [14.9, 13.0, 1.6], [14.9, 27.0, 1.5]),
         ('bus', [16.0, 2.6, 1.62], [16.0, 26.0, 1.4]), ('ceiling', [14.9, 15.5, 1.6], [15.8, 22.5, 2.75]),
         ('seated', [15.75, 20.0, 1.2], [16.1, 14.0, 1.45]), ('deck', [16.0, -0.6, 1.62], [16.0, -5.2, 1.25])]
for name, eye, target in cabin:
    new.append(['P72_%s_n' % name, eye, target, NORMAL])
    new.append(['P72_%s_p' % name, eye, target, PANIC])
new += [['P72_deck_close', [16.0, -2.9, 1.5], [16.05, -4.55, 1.08], NORMAL],
        ['P72_deck_pedestal', [16.1, -3.6, 1.45], [16.3, -4.47, 1.08], NORMAL],
        ['P72_deck_side', [15.3, -3.6, 1.35], [14.63, -4.37, 1.0], NORMAL],
        ['P72_deck_seat', [15.4, -3.2, 1.25], [15.9, -4.8, 1.15], NORMAL]]
if WALLS.exists():
    w = json.loads(WALLS.read_text(encoding='utf-8'))
    for st in w.get('stations', []):
        if 'wall_point' not in st:
            continue
        n = st['station'].split()[-1]
        (x, y, _), (nx, ny), f = st['wall_point'], st['normal'], st['floor']
        new.append(['E71_ext%s' % n, [x + nx * 1.7, y + ny * 1.7, f + 1.55], [x, y, f + .85]])
        sx, sy = -ny, nx                                                    # along the wall
        new.append(['E71_ext%s_side' % n, [x + nx * 1.1 + sx * 1.2, y + ny * 1.1 + sy * 1.2, f + 1.4], [x + nx * .15, y + ny * .15, f + .8]])
d = json.loads(VIEWS.read_text(encoding='utf-8'))
names = {v[0] for v in new}
d['views'] = [v for v in d['views'] if v[0] not in names] + new
VIEWS.write_text(json.dumps(d, indent=1), encoding='utf-8')
groups = {}
for v in new:
    groups.setdefault(v[0].split('_')[0], []).append(v[0])
(HERE / 'Views71.json').write_text(json.dumps(groups, indent=1), encoding='utf-8')
print('VIEWS71', {k: len(v) for k, v in groups.items()})
