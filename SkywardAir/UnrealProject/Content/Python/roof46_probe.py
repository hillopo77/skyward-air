"""Pass46 / P46-006, P46-007: survey the real roof and look at it from above.

Two things, read-only.

  survey   A 1 m grid of down-traces over the whole terminal footprint, from
           25 m. Records the first surface hit and its actor, so rooftop plant
           can be placed on measured roof tops, not on heights inferred from
           ceiling_m or the roof_steps face list.

  stills   Aerial views of the roof and the ground plane - the vantage of the
           flight mode the defects were raised against - plus one at the
           security entry to check the moved greeter faces the people coming
           in. The same views run again after the rooftop plant is imported.

Set ROOF46_SUFFIX in Roof46Suffix.txt beside this file to tag the stills
(e.g. 'before' / 'after'); the default is 'before'.
"""
import unreal as u, json, time, hashlib, traceback

G = None
S = {}

GRID_X = (-50.0, -13.0)
GRID_Y = (-23.0, 35.0)
STEP = 1.0

VIEWS = [
    ('R1_roof_southeast', [-8.0, -42.0, 34.0], [-31.0, 5.0, 4.0]),
    ('R2_roof_northwest', [-64.0, 46.0, 24.0], [-32.0, 6.0, 4.5]),
    ('R3_flight_vantage', [45.0, 70.0, 110.0], [-30.0, 4.0, 0.0]),
    ('R4_ground_wide', [-30.0, -150.0, 240.0], [-30.0, 80.0, 0.0]),
    ('S1_security_greeter', [-41.6, -6.2, 1.62], [-43.6, -2.3, 1.25]),
]
SETTLE = 1.6


def _suffix():
    p = G.R / 'Pass46' / 'Roof46Suffix.txt'
    try:
        return p.read_text(encoding='utf-8-sig').strip() or 'before'
    except Exception:
        return 'before'


def save(status='RUNNING', **kw):
    (G.R / 'Pass46' / ('Roof46_%s.json' % S['suffix'])).write_text(json.dumps(dict(
        status=status, suffix=S['suffix'], survey=S.get('survey'),
        captures=S.get('captures', []), **kw), indent=1), encoding='utf-8')


def stop(status, **kw):
    save(status, **kw)
    try:
        u.unregister_slate_post_tick_callback(S['handle'])
    except Exception:
        pass
    u.SystemLibrary.quit_game(G.P.STATE['world'], G.P.STATE['pc'],
                              u.QuitPreference.QUIT, False)


def _label(t):
    for i in (9, 10):
        try:
            return t[i].get_actor_label()
        except Exception:
            try:
                return t[i].get_owner().get_actor_label()
            except Exception:
                continue
    return 'unnamed'


def survey():
    world = G.P.STATE['world']
    pts = []
    nx = int(round((GRID_X[1] - GRID_X[0]) / STEP)) + 1
    ny = int(round((GRID_Y[1] - GRID_Y[0]) / STEP)) + 1
    for i in range(nx):
        for j in range(ny):
            x, y = GRID_X[0] + i * STEP, GRID_Y[0] + j * STEP
            hit = u.SystemLibrary.line_trace_single(
                world, G.v([x, y, 25.0]), G.v([x, y, -2.0]),
                u.TraceTypeQuery.TRACE_TYPE_QUERY1, True,
                [G.P.STATE['pawn']], u.DrawDebugTrace.NONE, True)
            t = hit.to_tuple() if hit else None
            if t and t[0]:
                pts.append([x, y, round(G.source(t[5])[2], 3), _label(t)])
            else:
                pts.append([x, y, None, None])
    return dict(grid_x=GRID_X, grid_y=GRID_Y, step=STEP, points=pts)


def tick(dt):
    try:
        now = time.monotonic()
        if now < S['next']:
            return
        if S.get('survey') is None:
            S['survey'] = survey()
            save()
            S['next'] = now + 0.5
            return
        pc = G.P.STATE['pc']
        cam = S['cam']
        if S.get('wait'):
            p = S['wait']
            if p.exists() and p.stat().st_mtime >= S['requested']:
                name, eye, target = VIEWS[S['i']]
                S['captures'].append(dict(name=name, file=str(p), eye=eye,
                                          target=target,
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
            cam.set_actor_rotation(
                u.MathLibrary.find_look_at_rotation(G.v(eye), G.v(target)), False)
            S['pose'] = pose
            S['next'] = now + SETTLE
            return
        p = G.R / 'Pass46' / 'Captures' / ('%s_%s.png' % (name, S['suffix']))
        S.update(wait=p, requested=time.time(), req_mono=now, next=now + .4)
        u.SystemLibrary.execute_console_command(
            G.P.STATE['world'], 'Shot -nosuffix filename="' + p.as_posix() + '"', pc)
    except Exception:
        stop('ERROR', error=traceback.format_exc())


def start(game):
    global G
    G = game
    S.update(suffix=_suffix(), survey=None, captures=[])
    try:
        (G.R / 'Pass46' / 'Captures').mkdir(parents=True, exist_ok=True)
        G.CAPTURE = True
        cam = next(iter(G.S['cameras'].values()))
        cam.camera_component.set_field_of_view(70)
        G.P.STATE['pc'].set_view_target_with_blend(cam, 0)
        S.update(cam=cam, i=0, next=time.monotonic() + 3.0)
        S['handle'] = u.register_slate_post_tick_callback(tick)
        save()
    except Exception:
        S.setdefault('i', 0)
        stop('ERROR', error=traceback.format_exc())
