"""Pass47 round 2: stills of the posters, sign faces and facade, plus an
airside survey for the service level. Read-only.

  airside  Ground profile from the terminal's airside face out to the apron:
           down-traces every 0.5 m along x from -16 to +12 at seven y lines
           (y -21..33), and horizontal traces at z 1.0 and -2.0 eastward from
           inside the terminal to find the airside wall face and what is below
           floor level.
"""
import unreal as u, json, time, traceback

G = None
S = {}
EYE = 1.62
VIEWS = [
    ('P1_public_return_posters', (-27, -20, EYE), (-48, -20, 1.9)),
    ('P2_public_return_close', (-38.5, -20.0, EYE), (-44.0, -18.2, 1.95)),
    ('P3_landside_posters', (-29, -6, EYE), (-48, -6, 1.8)),
    ('S1_checkin_start_sign', (-47.6, -12.6, EYE), (-43.12, -12.6, 1.95)),
    ('S2_cafe_concourse_sign', (-28.4, 9.0, EYE), (-31.88, 9.0, 2.15)),
    ('F1_facade_from_road', (-66, -12.5, 1.8), (-49, -12.5, 4.0)),
    ('F2_facade_oblique', (-63, -27, 2.2), (-49, -12.5, 4.0)),
    ('F3_arrivals_exit', (-58, -22, EYE), (-49, -20, 2.8)),
    ('X1_forecourt_arrival', (-63, -25, EYE), (-49, -12.5, 2.2)),
    ('A1_airside_face', (2, -12, 2.0), (-14, -2, 0.0)),
    ('A2_airside_low', (-6, 14, -2.0), (-14, 0, -1.5)),
]


def save(status='RUNNING', **kw):
    (G.R / 'Pass47' / 'Verify2_47.json').write_text(json.dumps(dict(
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
        if S.get('airside') is None:
            S['airside'] = airside(); save()
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
        p = G.R / 'Pass47' / 'After2' / (name + '.png')
        S.update(wait=p, requested=time.time(), req_mono=now, next=now + .4)
        u.SystemLibrary.execute_console_command(G.P.STATE['world'], 'Shot -nosuffix filename="' + p.as_posix() + '"', pc)
    except Exception:
        stop('ERROR', error=traceback.format_exc())


def start(game):
    global G
    G = game
    S.update(captures=[], i=0, airside=None)
    (G.R / 'Pass47' / 'After2').mkdir(parents=True, exist_ok=True)
    G.CAPTURE = True
    cam = next(iter(G.S['cameras'].values()))
    cam.camera_component.set_field_of_view(78)
    G.P.STATE['pc'].set_view_target_with_blend(cam, 0)
    S.update(cam=cam, next=time.monotonic() + 3.0)
    S['handle'] = u.register_slate_post_tick_callback(tick)
    save()
