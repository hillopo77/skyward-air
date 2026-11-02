"""Pass46 visual verification of the bridge wall-opening candidates.

Captures the places the wall probe reported open at all four heights with no
deck beyond, from inside the bridge and from outside it. Read-only.
"""
import unreal as u, json, time, hashlib, traceback

G = None
S = {}

VIEWS = [
    # Eye and target in source metres. Each is a settled still, not a gameplay
    # frame: the probe moves a detached camera, waits SETTLE seconds, then asks
    # the engine for one Shot.
    ("A1_forecourt_approach", [-58.0, -12.5, 1.62], [-49.0, -12.5, 1.80]),
    ("A2_forecourt_north", [-52.0, -4.0, 1.62], [-56.0, 12.0, 2.40]),
    ("A3_forecourt_shelter", [-53.5, -16.0, 1.62], [-57.5, -10.0, 1.40]),
    ("B1_concourse_alcove", [-29.0, 6.0, 1.62], [-29.0, -3.6, 1.60]),
    ("B2_concourse_north", [-29.0, 4.0, 1.62], [-28.0, 13.0, 1.80]),
    ("C1_cafe_approach", [-33.0, 12.0, 1.62], [-37.0, 14.5, 1.60]),
    ("D1_wc_passage", [-24.5, -2.5, 1.62], [-24.5, -11.0, 1.40]),
    ("E1_landside_corridor", [-28.0, -6.0, 1.62], [-45.0, -6.6, 1.70]),
    ("F1_arrivals", [-20.0, -14.0, 1.62], [-16.0, -20.0, 1.40]),
    ("G1_gallery", [-42.5, 26.0, 4.77], [-47.0, 31.5, 4.40]),
    ("G2_gallery_retail", [-46.0, 28.0, 4.77], [-43.5, 31.5, 4.60]),
    ("H1_checkin_headers", [-34.0, -13.1, 1.62], [-30.3, -12.6, 2.90]),
]

SETTLE = 1.4


def save(status='RUNNING', **kw):
    out = G.R / 'Pass46'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'Capture46.json').write_text(json.dumps(dict(
        status=status, step=S['i'], total=len(VIEWS),
        captures=S['captures'], **kw), indent=2), encoding='utf-8')


def stop(status, **kw):
    save(status, **kw)
    try:
        u.unregister_slate_post_tick_callback(S['handle'])
    except Exception:
        pass
    u.SystemLibrary.quit_game(G.P.STATE['world'], G.P.STATE['pc'],
                              u.QuitPreference.QUIT, False)


def tick(dt):
    try:
        now = time.monotonic()
        if now < S['next']:
            return
        pc = G.P.STATE['pc']
        cam = S['cam']
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
            cam.set_actor_rotation(
                u.MathLibrary.find_look_at_rotation(G.v(eye), G.v(target)), False)
            S['pose'] = pose
            S['next'] = now + SETTLE
            return
        p = G.R / 'Pass46' / 'Captures' / (name + '.png')
        S.update(wait=p, requested=time.time(), req_mono=now, next=now + .4)
        u.SystemLibrary.execute_console_command(
            G.P.STATE['world'], 'Shot -nosuffix filename="' + p.as_posix() + '"', pc)
    except Exception:
        stop('ERROR', error=traceback.format_exc())


def start(game):
    global G
    G = game
    try:
        (G.R / 'Pass46' / 'Captures').mkdir(parents=True, exist_ok=True)
        G.CAPTURE = True
        cam = next(iter(G.S['cameras'].values()))
        cam.camera_component.set_field_of_view(78)
        G.P.STATE['pc'].set_view_target_with_blend(cam, 0)
        S.update(cam=cam, i=0, captures=[], next=time.monotonic() + 2.5)
        S['handle'] = u.register_slate_post_tick_callback(tick)
        save()
    except Exception:
        S.setdefault('i', 0)
        S.setdefault('captures', [])
        stop('ERROR', error=traceback.format_exc())
