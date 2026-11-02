"""Pass45 entrance exposure boundary probe.

Read-only evidence collection. Changes no actor, material, asset or setting;
the only writes are PNG captures under Pass45/Captures and one JSON report.

Why this exists: the existing capture set photographs settled stills at fixed
viewpoints and never crosses a post-process volume boundary, so an exposure
discontinuity at a threshold is structurally invisible to it. This probe walks
the PLAYER camera across the entrance volume edge and holds at each sample
long enough for auto-exposure to settle, so any step in the resulting
luminance curve is attributable to the grade boundary rather than to
adaptation lag or changing scene content.

Entrance geometry from airport_layout.json:
  portal forecourt -> entrancefoyer at x=-49.0, y=-12.5, width 2.7 m
  zone entrancefoyer rect x in [-49,-43], y in [-18,-8]
  AP38 warm grade volume is inset 0.02 m per side, so its west face sits at
  x = -48.98. That is the boundary under test.
"""
import unreal as u, json, time, hashlib, traceback

G = None
S = {}

# Fixed look target well inside the foyer. Every sweep sample aims here, so the
# framing changes only slightly across the sweep and the exposure step is not
# confounded by a change of subject.
SWEEP_TARGET = [-43.0, -12.5, 1.55]
EYE_Z = 1.62

# Sample positions along y=-12.5, centred on the volume face at x=-48.98.
SWEEP_X = [
    -53.0, -52.0, -51.0, -50.0, -49.6, -49.4, -49.2, -49.1,
    -49.05, -49.0, -48.98, -48.96, -48.9, -48.8, -48.6, -48.4,
    -48.0, -47.0, -46.0, -45.0,
]

# Paired stills: the "looks different from outside" half of the complaint, plus
# two frames reproducing the existing gallery viewpoints for comparison.
STILLS = [
    ('A1_OutsideLookingIn',    [-53.0, -12.5, 1.62], [-44.0, -12.5, 1.60]),
    ('A2_InsideLookingOut',    [-46.0, -12.5, 1.62], [-56.0, -12.5, 1.62]),
    ('A3_InsideGalleryView',   [-46.8, -13.0, 1.62], [-43.2, -15.0, 1.60]),
    ('A4_ForecourtGalleryView', [-57.0, -15.0, 1.70], [-48.0, -12.5, 1.70]),
    ('A5_DoorwayStraddleOut',  [-49.3, -12.5, 1.62], [-43.0, -12.5, 1.55]),
    ('A6_DoorwayStraddleIn',   [-48.7, -12.5, 1.62], [-43.0, -12.5, 1.55]),
]

SETTLE_SECONDS = 2.2  # auto-exposure needs real time to converge; do not shorten


def _zone_of(D, x, y):
    """Which authored zone rect contains this point, and which grade volume."""
    inside_zone = None
    inside_volume = None
    for z in D['zones']:
        x0, x1, y0, y1 = z['rect']
        if x0 <= x <= x1 and y0 <= y <= y1:
            inside_zone = z['id']
        # The spawned volume is inset 0.02 m per side of the authored rect.
        if (x0 + .02) <= x <= (x1 - .02) and (y0 + .02) <= y <= (y1 - .02):
            inside_volume = z['id']
    return inside_zone, inside_volume


def _cvars():
    """Live console variable values, not what the ini or the profile claim."""
    names = ['r.ScreenPercentage', 'r.Tonemapper.Sharpen', 'r.SSGI.Quality',
             'r.DynamicGlobalIlluminationMethod', 'r.AntiAliasingMethod',
             'r.TemporalAASamples', 'r.TemporalAACurrentFrameWeight',
             'r.Shadow.MaxResolution', 'r.DefaultFeature.AutoExposure.ExtendDefaultLuminanceRange']
    out = {}
    for n in names:
        for getter in (u.SystemLibrary.get_console_variable_float_value,
                       u.SystemLibrary.get_console_variable_int_value):
            try:
                out[n] = getter(n)
                break
            except Exception as e:
                out[n] = dict(unavailable=str(e))
    return out


def _volumes(world):
    """Every post-process volume and the exposure/GI settings it actually holds."""
    rows = []
    for a in u.GameplayStatics.get_all_actors_of_class(world, u.PostProcessVolume):
        s = a.get_editor_property('settings')

        def g(prop):
            try:
                return s.get_editor_property(prop)
            except Exception as e:
                return dict(unavailable=str(e))

        gi = g('dynamic_global_illumination_method')
        # u.Vector is not iterable in this engine build; read components.
        sc = a.get_actor_scale3d()
        rows.append(dict(
            label=a.get_actor_label(),
            unbound=bool(a.get_editor_property('unbound')),
            priority=float(a.get_editor_property('priority')),
            blend_radius=float(a.get_editor_property('blend_radius')),
            blend_weight=float(a.get_editor_property('blend_weight')),
            location=list(G.source(a.get_actor_location())),
            scale=[float(sc.x), float(sc.y), float(sc.z)],
            override_exposure_min=bool(g('override_auto_exposure_min_brightness')),
            exposure_min=g('auto_exposure_min_brightness'),
            override_exposure_max=bool(g('override_auto_exposure_max_brightness')),
            exposure_max=g('auto_exposure_max_brightness'),
            exposure_method=str(g('auto_exposure_method')),
            exposure_speed_up=g('auto_exposure_speed_up'),
            exposure_speed_down=g('auto_exposure_speed_down'),
            override_gi_method=bool(g('override_dynamic_global_illumination_method')),
            gi_method=str(gi),
            ambient_cubemap_intensity=g('ambient_cubemap_intensity'),
            ao_intensity=g('ambient_occlusion_intensity'),
            bloom_intensity=g('bloom_intensity'),
        ))
    rows.sort(key=lambda q: q['label'])
    return rows


def save(status='RUNNING', **kw):
    out = G.R / 'Pass45'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'ExposureProbe45.json').write_text(json.dumps(dict(
        status=status,
        purpose='entrance exposure boundary evidence; no repair applied',
        boundary_under_test=dict(portal_x=-49.0, volume_west_face_x=-48.98,
                                 zone='entrancefoyer', y=-12.5),
        settle_seconds=SETTLE_SECONDS,
        camera='player pawn camera, default view target (not the detached capture camera)',
        step=S['i'], total=len(S['steps']),
        cvars=S.get('cvars'), volumes=S.get('volumes'),
        captures=S['captures'], **kw), indent=2), encoding='utf-8')


def stop(status, **kw):
    save(status, **kw)
    try:
        u.unregister_slate_post_tick_callback(S['handle'])
    except Exception:
        pass
    u.SystemLibrary.quit_game(G.P.STATE['world'], G.P.STATE['pc'], u.QuitPreference.QUIT, False)


def tick(dt):
    try:
        now = time.monotonic()
        if now < S['next']:
            return
        pc = G.P.STATE['pc']
        pawn = G.P.STATE['pawn']

        # Waiting on a requested frame to land on disk.
        if S.get('wait'):
            p = S['wait']
            if p.exists() and p.stat().st_mtime >= S['requested']:
                name, eye, target = S['steps'][S['i']]
                zone, volume = _zone_of(G.D, eye[0], eye[1])
                S['captures'].append(dict(
                    name=name, file=str(p),
                    sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                    eye=eye, target=target,
                    inside_zone=zone, inside_grade_volume=volume,
                    settled_seconds=SETTLE_SECONDS, kind='native_player_camera'))
                S.pop('wait')
                S['i'] += 1
                save()
            elif now - S['requested_mono'] > 25:
                raise RuntimeError('Native frame timeout at step %d' % S['i'])
            return

        if S['i'] >= len(S['steps']):
            stop('SUCCESS')
            return

        name, eye, target = S['steps'][S['i']]
        pose = (tuple(eye), tuple(target))

        # Move, then hold for the full settle before asking for a frame.
        if S.get('pose') != pose:
            pawn.set_actor_location(G.v(eye), False, True)
            pc.set_control_rotation(
                u.MathLibrary.find_look_at_rotation(G.v(eye), G.v(target)))
            S['pose'] = pose
            S['next'] = now + SETTLE_SECONDS
            return

        p = G.R / 'Pass45' / 'Captures' / (name + '.png')
        S.update(wait=p, requested=time.time(), requested_mono=now, next=now + .4)
        u.SystemLibrary.execute_console_command(
            G.P.STATE['world'], 'Shot -nosuffix filename="' + p.as_posix() + '"', pc)
    except Exception:
        stop('ERROR', error=traceback.format_exc())


def start(game):
    global G
    G = game
    # Any failure in here must still produce a report, otherwise the launcher
    # waits on a file that will never appear while the engine idles.
    try:
        (G.R / 'Pass45' / 'Captures').mkdir(parents=True, exist_ok=True)
        # Hide first-person hands so the frames are comparable; the player
        # camera itself is unchanged, which is the point of this probe.
        G.CAPTURE = True

        steps = list(STILLS)
        for x in SWEEP_X:
            steps.append(('B_sweep_x%+08.3f' % x, [x, -12.5, EYE_Z], list(SWEEP_TARGET)))

        S.update(steps=steps, i=0, captures=[],
                 cvars=_cvars(), volumes=_volumes(G.P.STATE['world']),
                 begun=time.monotonic(), next=time.monotonic() + 3.0)
        S['handle'] = u.register_slate_post_tick_callback(tick)
        save()
    except Exception:
        S.setdefault('steps', [])
        S.setdefault('i', 0)
        S.setdefault('captures', [])
        stop('ERROR', error=traceback.format_exc())
