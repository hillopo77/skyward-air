"""Pass47 round 2b: stills of Gate 08's re-seated row, the painted airside
service road and a big-picture aerial. Read-only.

"""
import unreal as u, json, time, traceback

G = None
S = {}
EYE = 1.62
VIEWS = [
    ('G1_gate08_row', (-29.5, 13.5, EYE), (-27.0, 28.0, 0.9)),
    ('G2_gate08_window', (-28.5, 22.0, EYE), (-24.85, 18.6, 1.2)),
    ('R1_road_from_gate', (-16.0, 30.0, 1.8), (-6.4, 10.0, -3.6)),
    ('R2_road_aerial', (-32.0, -22.0, 18.0), (-6.4, 6.0, -3.6)),
    ('R3_road_low', (-6.4, -22.0, -2.0), (-6.4, 10.0, -3.4)),
    ('B1_big_picture', (-95.0, -70.0, 45.0), (-20.0, 5.0, 0.0)),
]


def save(status='RUNNING', **kw):
    (G.R / 'Pass47' / 'Verify3_47.json').write_text(json.dumps(dict(
        status=status, airside=S.get('airside'), captures=S.get('captures', []), **kw), indent=1), encoding='utf-8')


def stop(status, **kw):
    save(status, **kw)
    u.unregister_slate_post_tick_callback(S['handle'])
    u.SystemLibrary.quit_game(G.P.STATE['world'], G.P.STATE['pc'], u.QuitPreference.QUIT, False)


def hit(a, b):
    h = u.SystemLibrary.line_trace_single(G.P.STATE['world'], G.v(a), G.v(b), u.TraceTypeQuery.TRACE_TYPE_QUERY2,
                                          True, [G.P.STATE['pawn']], u.DrawDebugTrace.NONE, True)
    t = h.to_tuple() if h else None
    if not t or not t[0]:
        return None
    p = G.source(t[5])
    return [round(p[0], 3), round(p[1], 3), round(p[2], 3), t[9].get_actor_label() if t[9] else None]


def airside():
    out = dict(profiles={}, faces={})
    for y in (-21.0, -15.0, -8.0, -1.0, 6.0, 20.0, 30.0):
        out['profiles'][str(y)] = [[x, hit([x, y, 12.0], [x, y, -12.0])] for x in [-16 + 0.5 * k for k in range(57)]]
        out['faces'][str(y)] = dict(z1=hit([-16.5, y, 1.0], [12.0, y, 1.0]), zm2=hit([-16.5, y, -2.0], [12.0, y, -2.0]),
                                    from_out_z1=hit([12.0, y, 1.0], [-20.0, y, 1.0]),
                                    from_out_zm2=hit([12.0, y, -2.0], [-20.0, y, -2.0]))
    return out


def tick(dt):
    try:
        now = time.monotonic()
        if now < S['next']:
            return
        cam, pc = S['cam'], G.P.STATE['pc']
        if S.get('wait'):
            p = S['wait']
            if p.exists() and p.stat().st_mtime >= S['requested']:
                S['captures'].append(dict(name=VIEWS[S['i']][0], file=str(p)))
                S.pop('wait'); S['i'] += 1; save()
            elif now - S['req_mono'] > 25:
                raise RuntimeError('frame timeout')
            return
        if S['i'] >= len(VIEWS):
            stop('SUCCESS'); return
        name, eye, target = VIEWS[S['i']]
        if S.get('posed') != S['i']:
            cam.set_actor_location(G.v(eye), False, True)
            cam.set_actor_rotation(u.MathLibrary.find_look_at_rotation(G.v(eye), G.v(target)), False)
            S.update(posed=S['i'], next=now + 1.5); return
        p = G.R / 'Pass47' / 'After3' / (name + '.png')
        S.update(wait=p, requested=time.time(), req_mono=now, next=now + .4)
        u.SystemLibrary.execute_console_command(G.P.STATE['world'], 'Shot -nosuffix filename="' + p.as_posix() + '"', pc)
    except Exception:
        stop('ERROR', error=traceback.format_exc())


def start(game):
    global G, VIEWS
    G = game
    custom = G.R / 'Pass47' / 'Verify3Views.json'
    if custom.exists():
        VIEWS = [tuple(v) for v in json.loads(custom.read_text(encoding='utf-8'))]
    S.update(captures=[], i=0, airside=None)
    (G.R / 'Pass47' / 'After3').mkdir(parents=True, exist_ok=True)
    G.CAPTURE = True
    cam = next(iter(G.S['cameras'].values()))
    cam.camera_component.set_field_of_view(78)
    G.P.STATE['pc'].set_view_target_with_blend(cam, 0)
    S.update(cam=cam, next=time.monotonic() + 3.0)
    S['handle'] = u.register_slate_post_tick_callback(tick)
    save()
