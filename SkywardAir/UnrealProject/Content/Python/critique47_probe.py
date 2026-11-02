"""Pass47: look at the airport the way a player meets it, and measure its flow.

Two read-only parts.

  reach    Flood-fill the ground floor from the spawn point on a 0.5 m grid,
           moving between neighbours only where a sphere sweep with the
           player's real collision (r 0.35 m at eye height 1.62) is clear.
           Reports, per room, how much of its floor a player can reach. A room
           at 0% is cut off; doors that were shut at sampling time count as
           walls, so a 0% room next to a door is checked by eye before it is
           called a defect.

  stills   ~40 eye-level views: the forecourt, every room from its entrance
           and from the far side, the gallery, the apron, the cabin and the
           flight deck.

Writes Pass47/Critique47.json and Pass47/Captures/*.png.
"""
import unreal as u, json, time, hashlib, traceback, math
from collections import deque

G = None
S = {}
EYE, R = 1.62, 0.35
GRID = (-52.0, -12.0, -24.0, 36.0)
STEP = 0.5

V = lambda name, e, t: (name, list(e), list(t))
VIEWS = [
    V('X1_forecourt_arrival', (-63, -25, 1.62), (-49, -12.5, 2.2)),
    V('X2_terminal_facade', (-60, -2, 1.62), (-49, -14, 3.0)),
    V('X3_overview_landside', (-78, -48, 32), (-31, 6, 2)),
    V('X4_apron_from_stand', (6, -10, 1.62), (-14, 4, 3.0)),
    V('X5_aircraft_bridge', (28, -16, 2.0), (14, 4, 3.0)),
    V('Z01_foyer_in', (-48.3, -12.5, EYE), (-43, -15, 1.7)),
    V('Z02_foyer_back', (-43.6, -15, EYE), (-48.5, -9.5, 1.7)),
    V('Z03_checkin_in', (-42.3, -15, EYE), (-27, -12, 1.7)),
    V('Z04_checkin_back', (-27.2, -9, EYE), (-42, -16.5, 1.6)),
    V('Z05_publicreturn_w', (-27, -20, EYE), (-48, -20, 1.7)),
    V('Z06_publicreturn_e', (-48, -20.5, EYE), (-27, -19.5, 1.7)),
    V('Z07_landside_w', (-29, -6, EYE), (-48, -6, 1.7)),
    V('Z08_landside_e', (-47.5, -6, EYE), (-27, -6, 1.7)),
    V('Z09_security_in', (-42, -3.4, EYE), (-41.5, 8, 1.5)),
    V('Z10_security_back', (-37, 9.2, EYE), (-46.5, -2, 1.5)),
    V('Z11_recovery_in', (-35.4, 6.5, EYE), (-33, 1, 1.5)),
    V('Z12_recovery_back', (-32.6, 1, EYE), (-35.5, 9.5, 1.6)),
    V('Z13_concourse_n', (-29, -3.3, EYE), (-29, 13.5, 1.8)),
    V('Z14_concourse_s', (-29, 13.4, EYE), (-29, -3.5, 1.6)),
    V('Z15_gate07entry', (-25.6, 4, EYE), (-23, 7, 1.6)),
    V('Z16_gate07_in', (-22.6, 4, EYE), (-14.5, 1.5, 1.7)),
    V('Z17_gate07_back', (-14.6, 8.8, EYE), (-22.5, -2, 1.5)),
    V('Z18_gate08_in', (-28, 14.6, EYE), (-28, 33.5, 1.8)),
    V('Z19_gate08_back', (-28, 33.3, EYE), (-28, 15, 1.6)),
    V('Z20_cafefoyer', (-32.6, 12, EYE), (-36.5, 15.5, 1.7)),
    V('Z21_cafe_in', (-34.5, 16.6, EYE), (-46, 30, 2.5)),
    V('Z22_cafe_back', (-48.2, 33.2, EYE), (-35, 18, 2.0)),
    V('Z23_gallery', (-46.4, 26.4, 4.77), (-42, 32.5, 4.4)),
    V('Z24_gallery_down', (-41.6, 32.8, 4.77), (-46, 22, 2.0)),
    V('Z25_wc_passage', (-25.9, -3.6, EYE), (-24.4, -11.3, 1.5)),
    V('Z26_wc_in', (-22.6, -8.5, EYE), (-15, -6, 1.5)),
    V('Z27_wc_back', (-14.6, -11.4, EYE), (-22.5, -3.6, 1.5)),
    V('Z28_operations_in', (-46, 9.6, EYE), (-41.5, 14.5, 1.5)),
    V('Z29_operations_back', (-38.6, 15.4, EYE), (-48.5, 10.5, 1.5)),
    V('Z30_baggage_service', (-22.4, -17.65, EYE), (-25.5, -13, 1.5)),
    V('Z31_arrivals_in', (-21.6, -20, EYE), (-15, -13.5, 1.6)),
    V('Z32_arrivals_back', (-14.6, -12.6, EYE), (-21.5, -21.5, 1.4)),
    V('Z33_arrivals_exit', (-22.4, -20, EYE), (-25.6, -20, 1.6)),
    V('C1_cabin_aisle', (16.0, 2.6, EYE), (16.0, 26, 1.4)),
    V('C2_flight_deck', (16.0, -0.6, EYE), (16.0, -5.2, 1.25)),
]
SETTLE = 1.4


def save(status='RUNNING', **kw):
    (G.R / 'Pass47' / ('Critique47%s.json' % ('_reach' if S.get('mode') == 'reach' else ''))).write_text(json.dumps(dict(
        status=status, reach=S.get('reach'), captures=S.get('captures', []), **kw),
        indent=1), encoding='utf-8')


def stop(status, **kw):
    save(status, **kw)
    try:
        u.unregister_slate_post_tick_callback(S['handle'])
    except Exception:
        pass
    u.SystemLibrary.quit_game(G.P.STATE['world'], G.P.STATE['pc'],
                              u.QuitPreference.QUIT, False)


def clear(a, b):
    hit = u.SystemLibrary.sphere_trace_single(
        G.P.STATE['world'], G.v([a[0], a[1], EYE]), G.v([b[0], b[1], EYE]),
        R * 100.0, u.TraceTypeQuery.TRACE_TYPE_QUERY1, False,
        [G.P.STATE['pawn']] + S.get('ignore', []), u.DrawDebugTrace.NONE, True)
    t = hit.to_tuple() if hit else None
    return not (t and t[0])


def standing(p):
    """A cell is standable if the sphere fits there at all."""
    hit = u.SystemLibrary.sphere_trace_single(
        G.P.STATE['world'], G.v([p[0], p[1], EYE + 0.01]), G.v([p[0], p[1], EYE]),
        R * 100.0, u.TraceTypeQuery.TRACE_TYPE_QUERY1, False,
        [G.P.STATE['pawn']], u.DrawDebugTrace.NONE, True)
    t = hit.to_tuple() if hit else None
    return not (t and t[0])


def reach():
    x0, x1, y0, y1 = GRID
    nx, ny = int((x1 - x0) / STEP) + 1, int((y1 - y0) / STEP) + 1
    cell = lambda i, j: (x0 + i * STEP, y0 + j * STEP)
    start = G.D['start']
    si, sj = round((start[0] - x0) / STEP), round((start[1] - y0) / STEP)
    seen = {(si, sj)}
    q = deque([(si, sj)])
    while q:
        i, j = q.popleft()
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            k = (i + di, j + dj)
            if k in seen or not (0 <= k[0] < nx and 0 <= k[1] < ny):
                continue
            if clear(cell(i, j), cell(*k)):
                seen.add(k)
                q.append(k)
    zones = {}
    for z in G.D['zones']:
        zx0, zx1, zy0, zy1 = z['rect']
        inside = [(i, j) for i in range(nx) for j in range(ny)
                  if zx0 + .3 < cell(i, j)[0] < zx1 - .3 and zy0 + .3 < cell(i, j)[1] < zy1 - .3]
        got = sum(1 for c in inside if c in seen)
        zones[z['id']] = dict(cells=len(inside), reached=got,
                              pct=round(100.0 * got / max(1, len(inside)), 1))
    return dict(grid=GRID, step=STEP, reached=len(seen), zones=zones,
                cells=[list(cell(i, j)) for i, j in sorted(seen)])


def tick(dt):
    try:
        now = time.monotonic()
        if now < S['next']:
            return
        if S.get('reach') is None:
            if S.get('mode') == 'reach':
                # Layout question, not door state: every door leaf counts as
                # open, so a 0% room really has no way in.
                S['ignore'] = [d['actor'] for d in G.S.get('doors', {}).values() if d.get('actor')]
                S['doors_open'] = sorted(G.S.get('doors', {}))
            S['reach'] = reach()
            save(doors_treated_open=S.get('doors_open'))
            if S.get('mode') == 'reach':
                stop('SUCCESS', doors_treated_open=S.get('doors_open'))
                return
            S['next'] = now + 0.5
            return
        pc, cam = G.P.STATE['pc'], S['cam']
        if S.get('wait'):
            p = S['wait']
            if p.exists() and p.stat().st_mtime >= S['requested']:
                name, eye, target = VIEWS[S['i']]
                S['captures'].append(dict(name=name, file=str(p), eye=eye, target=target,
                                          sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
                S.pop('wait')
                S['i'] += 1
                save()
            elif now - S['req_mono'] > 25:
                raise RuntimeError('frame timeout')
            return
        if S['i'] >= len(VIEWS):
            stop('SUCCESS')
            return
        name, eye, target = VIEWS[S['i']]
        pose = (tuple(eye), tuple(target))
        if S.get('pose') != pose:
            cam.set_actor_location(G.v(eye), False, True)
            cam.set_actor_rotation(u.MathLibrary.find_look_at_rotation(G.v(eye), G.v(target)), False)
            S['pose'] = pose
            S['next'] = now + SETTLE
            return
        p = G.R / 'Pass47' / 'Captures' / (name + '.png')
        S.update(wait=p, requested=time.time(), req_mono=now, next=now + .4)
        u.SystemLibrary.execute_console_command(
            G.P.STATE['world'], 'Shot -nosuffix filename="' + p.as_posix() + '"', pc)
    except Exception:
        stop('ERROR', error=traceback.format_exc())


def start(game):
    global G
    G = game
    S.update(captures=[], reach=None, i=0)
    try:
        S['mode'] = (G.R / 'Pass47' / 'Critique47Mode.txt').read_text(encoding='utf-8-sig').strip()
    except Exception:
        S['mode'] = 'full'
    try:
        (G.R / 'Pass47' / 'Captures').mkdir(parents=True, exist_ok=True)
        G.CAPTURE = True
        cam = next(iter(G.S['cameras'].values()))
        cam.camera_component.set_field_of_view(84)
        G.P.STATE['pc'].set_view_target_with_blend(cam, 0)
        S.update(cam=cam, next=time.monotonic() + 3.0)
        S['handle'] = u.register_slate_post_tick_callback(tick)
        save()
    except Exception:
        stop('ERROR', error=traceback.format_exc())
