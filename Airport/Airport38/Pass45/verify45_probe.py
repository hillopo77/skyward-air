"""Pass45 visual verification of the bridge wall-opening candidates.

Captures the places the wall probe reported open at all four heights with no
deck beyond, from inside the bridge and from outside it. Read-only.
"""
import unreal as u, json, time, hashlib, traceback

G = None
S = {}

VIEWS = [
    # Elbow outer corner, the largest cluster. Inside looking at the corner.
    ('E1_elbow_outer_inside', [-1.60, -3.40, 1.50], [-2.30, -4.80, 0.15]),
    ('E2_elbow_outer_low', [-1.60, -3.80, 0.55], [-2.40, -4.75, 0.05]),
    # Same corner from outside and below the bridge.
    ('E3_elbow_outer_exterior', [-3.20, -8.00, 1.20], [-1.90, -4.55, 0.10]),
    ('E4_elbow_outer_under', [-1.00, -7.00, -1.80], [-2.00, -4.60, 0.00]),
    # Bank B outer corner at the elbow.
    ('E5_bankB_outer_corner', [-0.20, -3.60, 1.20], [-1.20, -4.70, 0.10]),
    # Bank B inner edge approaching the cab mitre.
    ('E6_bankB_inner_cab', [8.60, 0.40, 1.50], [10.00, 1.72, 0.20]),
    # Docking cab north side.
    ('E7_cab_north', [11.60, 0.30, 1.50], [10.80, 2.00, 0.25]),
    ('E8_cab_north_exterior', [11.00, 4.50, 1.60], [10.90, 1.95, 0.20]),
    # Context: the whole dogleg from outside.
    ('E9_bridge_context', [2.00, -12.00, 6.00], [-1.50, -3.60, 0.50]),
]

SETTLE = 1.4


def save(status='RUNNING', **kw):
    out = G.R / 'Pass45'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'Verify45.json').write_text(json.dumps(dict(
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
        p = G.R / 'Pass45' / 'Captures' / (name + '.png')
        S.update(wait=p, requested=time.time(), req_mono=now, next=now + .4)
        u.SystemLibrary.execute_console_command(
            G.P.STATE['world'], 'Shot -nosuffix filename="' + p.as_posix() + '"', pc)
    except Exception:
        stop('ERROR', error=traceback.format_exc())


def start(game):
    global G
    G = game
    try:
        (G.R / 'Pass45' / 'Captures').mkdir(parents=True, exist_ok=True)
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
