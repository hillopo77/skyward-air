"""Pass45 unsupported-object audit, corrected.

The first version traced from 1 cm OUTSIDE each bounding face outward, which
starts below the floor for anything resting on it, so floor-standing furniture
read as floating. This version traces from 3 cm INSIDE the face outward to the
tolerance, ignoring the actor itself, so contact with a supporting surface is
detected regardless of which side of the face it sits on.

For every placed static mesh it records the distance to the nearest geometry
in each of six directions. An object with no contact within the tolerance in
ANY direction is unsupported. The per-direction distances are kept so results
can be ranked and re-triaged without another engine run.

Excludes: invisible collision proxies, simulating physics bodies (their
position at scan time is not authored), and anything attached to a moving
parent, since those are judged against their pose rather than the world.

Read-only: traces only.
"""
import unreal as u, json, time, traceback

G = None
S = {}

INSET_CM = 3.0
TOLERANCE_CM = 12.0
PER_TICK = 120
SKIP_PREFIX = ('CH12COLL ', 'AP Tow joint ')
SKIP_CONTAINS = ('Physical luggage', 'Security tray', 'Cafe cup', 'Coffee cup')
DIRS = [('down', 0, 0, -1), ('east', 1, 0, 0), ('west', -1, 0, 0),
        ('north', 0, 1, 0), ('south', 0, -1, 0), ('up', 0, 0, 1)]


def save(status='RUNNING', **kw):
    out = G.R / 'Pass45'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'Support45.json').write_text(json.dumps(dict(
        status=status,
        method=dict(inset_cm=INSET_CM, tolerance_cm=TOLERANCE_CM,
                    rule='unsupported = no geometry within tolerance in any of '
                         'six directions, traced from inside each bounding face'),
        checked=S.get('checked', 0), total=len(S.get('actors', [])),
        skipped=S.get('skipped', 0), simulating=S.get('simulating', 0),
        unsupported=S.get('bad', []), **kw), indent=2), encoding='utf-8')


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
        if time.monotonic() < S['next']:
            return
        world = G.P.STATE['world']
        n = 0
        while S['i'] < len(S['actors']) and n < PER_TICK:
            a = S['actors'][S['i']]
            S['i'] += 1
            n += 1
            if not u.SystemLibrary.is_valid(a):
                continue
            label = a.get_actor_label()
            if label.startswith(SKIP_PREFIX) or any(k in label for k in SKIP_CONTAINS):
                S['skipped'] += 1
                continue
            try:
                c = a.static_mesh_component
                if c.is_simulating_physics():
                    S['simulating'] += 1
                    continue
                if a.get_attach_parent_actor() is not None:
                    S['skipped'] += 1
                    continue
            except Exception:
                pass
            try:
                origin, extent = a.get_actor_bounds(False)
            except Exception:
                continue
            ex, ey, ez = extent.x, extent.y, extent.z
            if max(ex, ey, ez) < 2.0 or max(ex, ey, ez) > 1500.0:
                S['skipped'] += 1
                continue
            S['checked'] += 1
            ext = {'down': ez, 'up': ez, 'east': ex, 'west': ex,
                   'north': ey, 'south': ey}
            dists = {}
            supported = False
            for name, dx, dy, dz in DIRS:
                e = ext[name]
                sx = origin.x + dx * (e - INSET_CM)
                sy = origin.y + dy * (e - INSET_CM)
                sz = origin.z + dz * (e - INSET_CM)
                tx = origin.x + dx * (e + TOLERANCE_CM)
                ty = origin.y + dy * (e + TOLERANCE_CM)
                tz = origin.z + dz * (e + TOLERANCE_CM)
                hit = u.SystemLibrary.line_trace_single(
                    world, u.Vector(sx, sy, sz), u.Vector(tx, ty, tz),
                    u.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [a],
                    u.DrawDebugTrace.NONE, True)
                d = None
                if hit:
                    t = hit.to_tuple()
                    if t[0]:
                        d = round(float(t[2]) - INSET_CM, 2)
                        supported = True
                dists[name] = d
            if not supported:
                # how far to the nearest thing at all, looking further down
                far = None
                hit = u.SystemLibrary.line_trace_single(
                    world, u.Vector(origin.x, origin.y, origin.z - ez + INSET_CM),
                    u.Vector(origin.x, origin.y, origin.z - ez - 400.0),
                    u.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [a],
                    u.DrawDebugTrace.NONE, True)
                if hit:
                    t = hit.to_tuple()
                    if t[0]:
                        far = round(float(t[2]) - INSET_CM, 1)
                S['bad'].append(dict(
                    actor=label,
                    mesh=(a.static_mesh_component.static_mesh.get_name()
                          if a.static_mesh_component.static_mesh else None),
                    centre=[round(q, 2) for q in G.source(origin)],
                    extent_cm=[round(ex, 1), round(ey, 1), round(ez, 1)],
                    drop_to_floor_cm=far))
        if S['i'] >= len(S['actors']):
            stop('SUCCESS')
        elif S['i'] % 600 < PER_TICK:
            save()
    except Exception:
        stop('ERROR', error=traceback.format_exc())


def start(game):
    global G
    G = game
    try:
        G.CAPTURE = True
        G.QA = True
        actors = list(u.GameplayStatics.get_all_actors_of_class(
            G.P.STATE['world'], u.StaticMeshActor))
        S.update(actors=actors, i=0, checked=0, skipped=0, simulating=0, bad=[],
                 next=time.monotonic() + 2.0)
        S['handle'] = u.register_slate_post_tick_callback(tick)
        save()
    except Exception:
        S.setdefault('actors', [])
        stop('ERROR', error=traceback.format_exc())
