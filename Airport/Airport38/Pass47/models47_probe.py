"""Pass47: photograph every distinct model in the game, in place, as played.

One still per distinct mesh: static meshes and the character skeletal meshes.
Each is framed on one actor that uses it, with real materials and lighting.
The camera tries eight directions at 25 degrees elevation, traces from the
model outward along each, and takes the one with the longest clear run - a
spring arm - so a model in a furnished room is not shot through a wall.

Skipped, because other stills already cover them or they are not seen:
hidden collision proxies, anything whose bounds exceed 20 m (the shell
unions: walls, floors, roofs, ground), and cameras, lights and text.

Writes Pass47/Models47.json and Pass47/Models/<index>.png. Read-only.
"""
import unreal as u, json, time, math, hashlib, traceback

G = None
S = {}
FOV = 50.0
SETTLE = 0.7
MAX_EXTENT_M = 20.0


def save(status='RUNNING', **kw):
    (G.R / 'Pass47' / 'Models47.json').write_text(json.dumps(dict(
        status=status, total=len(S.get('jobs', [])), shots=S.get('shots', []), **kw),
        indent=1), encoding='utf-8')


def stop(status, **kw):
    save(status, **kw)
    try:
        u.unregister_slate_post_tick_callback(S['handle'])
    except Exception:
        pass
    u.SystemLibrary.quit_game(G.P.STATE['world'], G.P.STATE['pc'],
                              u.QuitPreference.QUIT, False)


def jobs():
    world = G.P.STATE['world']
    seen, out = set(), []
    for cls in (u.StaticMeshActor, u.SkeletalMeshActor):
        for a in u.GameplayStatics.get_all_actors_of_class(world, cls):
            try:
                label = a.get_actor_label()
                if label.startswith(('CH12COLL', 'COL_')):
                    continue
                if cls is u.StaticMeshActor:
                    c = a.static_mesh_component
                    m = c.static_mesh
                else:
                    c = a.skeletal_mesh_component
                    m = c.get_editor_property('skeletal_mesh_asset') if hasattr(c, 'skeletal_mesh_asset') else c.skeletal_mesh
                if m is None or not c.is_visible():
                    continue
                name = m.get_name()
                if name in seen or name == 'Cube':
                    continue
                o, e = a.get_actor_bounds(False)
                if max(e.x, e.y, e.z) / 100.0 > MAX_EXTENT_M:
                    continue
                seen.add(name)
                out.append(dict(mesh=name, actor=label, kind=cls.__name__,
                                centre=[o.x, o.y, o.z], extent=[e.x, e.y, e.z], ref=a))
            except Exception:
                continue
    out.sort(key=lambda q: q['mesh'])
    return out


def pose(job):
    world = G.P.STATE['world']
    c = u.Vector(*job['centre'])
    r = max(8.0, math.sqrt(sum(v * v for v in job['extent'])))
    want = r * 1.15 / math.tan(math.radians(FOV / 2))
    best = None
    for k in range(8):
        az = math.radians(45 * k + 22.5)
        el = math.radians(25)
        d = u.Vector(math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el))
        end = c + d * want
        hit = u.SystemLibrary.line_trace_single(
            world, c, end, u.TraceTypeQuery.TRACE_TYPE_QUERY1, True,
            [job['ref'], G.P.STATE['pawn']], u.DrawDebugTrace.NONE, True)
        t = hit.to_tuple() if hit else None
        run = want
        if t and t[0]:
            run = max(0.0, (t[4] - c).length() - 15.0)
        if best is None or run > best[0]:
            best = (run, d)
    run, d = best
    eye = c + d * max(run, min(want, r * 1.05))
    return eye, c, round(run / want, 2)


def tick(dt):
    try:
        now = time.monotonic()
        if now < S['next']:
            return
        if 'jobs' not in S:
            S['jobs'] = jobs()
            save()
            S['next'] = now + 0.3
            return
        cam, pc = S['cam'], G.P.STATE['pc']
        if S.get('wait'):
            p = S['wait']
            if p.exists() and p.stat().st_mtime >= S['requested']:
                j = S['jobs'][S['i']]
                S['shots'].append(dict(index=S['i'], mesh=j['mesh'], actor=j['actor'],
                                       kind=j['kind'], file=str(p), clear=S['clear'],
                                       size_m=[round(2 * v / 100, 2) for v in j['extent']]))
                S.pop('wait')
                S['i'] += 1
                if S['i'] % 20 == 0:
                    save()
            elif now - S['req_mono'] > 25:
                raise RuntimeError('frame timeout at %s' % S['jobs'][S['i']]['mesh'])
            return
        if S['i'] >= len(S['jobs']):
            stop('SUCCESS')
            return
        j = S['jobs'][S['i']]
        if S.get('posed') != S['i']:
            eye, target, clear = pose(j)
            cam.set_actor_location(eye, False, True)
            cam.set_actor_rotation(u.MathLibrary.find_look_at_rotation(eye, target), False)
            S.update(posed=S['i'], clear=clear, next=now + SETTLE)
            return
        p = G.R / 'Pass47' / 'Models' / ('%03d.png' % S['i'])
        S.update(wait=p, requested=time.time(), req_mono=now, next=now + .3)
        u.SystemLibrary.execute_console_command(
            G.P.STATE['world'], 'Shot -nosuffix filename="' + p.as_posix() + '"', pc)
    except Exception:
        stop('ERROR', error=traceback.format_exc())


def start(game):
    global G
    G = game
    S.update(shots=[], i=0)
    try:
        (G.R / 'Pass47' / 'Models').mkdir(parents=True, exist_ok=True)
        G.CAPTURE = True
        cam = next(iter(G.S['cameras'].values()))
        cam.camera_component.set_field_of_view(FOV)
        G.P.STATE['pc'].set_view_target_with_blend(cam, 0)
        S.update(cam=cam, next=time.monotonic() + 3.0)
        S['handle'] = u.register_slate_post_tick_callback(tick)
        save()
    except Exception:
        stop('ERROR', error=traceback.format_exc())
