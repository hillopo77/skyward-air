"""Pass47 verification stills, plus the ground along the forecourt road's line.

Stills of everything this pass changed, from the same eyes as the critique
where one exists, so before and after compare directly. Then a down-trace
every 10 m along the road's centreline (x=-65) beyond both of its ends,
y -600..+800, to see whether the ground there is flat enough to carry the
road on to the edge of the map without floating or burying it.

Writes Pass47/Final47.json and Pass47/After/*.png. Read-only.
"""
import unreal as u, json, time, hashlib, traceback

G = None
S = {}
EYE = 1.62
VIEWS = [
    ('X1_forecourt_arrival', (-63, -25, EYE), (-49, -12.5, 2.2)),
    ('X2_terminal_facade', (-60, -2, EYE), (-49, -14, 3.0)),
    ('X3_overview_landside', (-78, -48, 32), (-31, 6, 2)),
    ('X6_forecourt_road', (-66, -30, 2.2), (-66, 10, 2.0)),
    ('Z03_checkin_in', (-42.3, -15, EYE), (-27, -12, 1.7)),
    ('Z05_publicreturn_w', (-27, -20, EYE), (-48, -20, 1.7)),
    ('Z07_landside_w', (-29, -6, EYE), (-48, -6, 1.7)),
    ('Z07b_landside_board', (-39, -5.0, EYE), (-39, -7.9, 2.1)),
    ('Z13b_concourse_board', (-29, 4.5, EYE), (-29, -3.9, 2.1)),
    ('Z13_concourse_n', (-29, -3.3, EYE), (-29, 13.5, 1.8)),
    ('Z21_cafe_in', (-34.5, 16.6, EYE), (-46, 30, 2.5)),
    ('Z31_arrivals_in', (-21.6, -20, EYE), (-15, -13.5, 1.6)),
    ('Z31b_arrivals_board', (-18, -15.5, EYE), (-18, -12.1, 2.1)),
]


def save(status='RUNNING', **kw):
    (G.R / 'Pass47' / 'Final47.json').write_text(json.dumps(dict(
        status=status, road=S.get('road'), captures=S.get('captures', []), **kw), indent=1),
        encoding='utf-8')


def stop(status, **kw):
    save(status, **kw)
    u.unregister_slate_post_tick_callback(S['handle'])
    u.SystemLibrary.quit_game(G.P.STATE['world'], G.P.STATE['pc'], u.QuitPreference.QUIT, False)


def road():
    rows = []
    for k in range(141):
        y = -600.0 + 10.0 * k
        hit = u.SystemLibrary.line_trace_single(
            G.P.STATE['world'], G.v([-65.0, y, 40.0]), G.v([-65.0, y, -30.0]),
            u.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [G.P.STATE['pawn']],
            u.DrawDebugTrace.NONE, True)
        t = hit.to_tuple() if hit else None
        if t and t[0]:
            rows.append([y, round(G.source(t[5])[2], 3), t[9].get_actor_label() if t[9] else None])
        else:
            rows.append([y, None, None])
    return rows


def tick(dt):
    try:
        now = time.monotonic()
        if now < S['next']:
            return
        if S.get('road') is None:
            S['road'] = road()
            save()
        cam, pc = S['cam'], G.P.STATE['pc']
        if S.get('wait'):
            p = S['wait']
            if p.exists() and p.stat().st_mtime >= S['requested']:
                name, eye, target = VIEWS[S['i']]
                S['captures'].append(dict(name=name, file=str(p), eye=list(eye), target=list(target)))
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
        p = G.R / 'Pass47' / 'After' / (name + '.png')
        S.update(wait=p, requested=time.time(), req_mono=now, next=now + .4)
        u.SystemLibrary.execute_console_command(G.P.STATE['world'], 'Shot -nosuffix filename="' + p.as_posix() + '"', pc)
    except Exception:
        stop('ERROR', error=traceback.format_exc())


def start(game):
    global G
    G = game
    S.update(captures=[], i=0, road=None)
    (G.R / 'Pass47' / 'After').mkdir(parents=True, exist_ok=True)
    G.CAPTURE = True
    cam = next(iter(G.S['cameras'].values()))
    cam.camera_component.set_field_of_view(84)
    G.P.STATE['pc'].set_view_target_with_blend(cam, 0)
    S.update(cam=cam, next=time.monotonic() + 3.0)
    S['handle'] = u.register_slate_post_tick_callback(tick)
    save()
