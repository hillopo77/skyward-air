"""Pass47: map the aircraft's floor collision around the cockpit doorway.

In the Pass47 journey the in-flight dropped bag fell through the floor near
local (15.5, -2.5): its height went to -0.22 m, it left the aircraft frame and
was re-caught 13.8 m aft. Earlier runs released it a little elsewhere and
passed. Physics bodies collide with SIMPLE collision, so this traces down with
simple collision (and complex, for comparison) on a 10 cm grid over the
cockpit and forward cabin of the parked aircraft, from 1.5 m to -1.0 m, and
records the first floor-level hit. A cell with no simple hit near 0 is a hole
a dropped body can fall through.

Read-only.
"""
import unreal as u, json, time, traceback

G = None
S = {}
X = (13.6, 18.4)
Y = (-5.4, 1.6)
STEP = 0.1


def trace(x, y, cx):
    world = G.P.STATE['world']
    frame = G.flight39['frame']
    a = frame.world(G.v([x, y, 1.5]))
    b = frame.world(G.v([x, y, -1.0]))
    # Camera channel: the aircraft's COL_ proxies ignore Visibility by design
    # (aim and interaction traces pass through them) but block everything
    # else, physics bodies included.
    hit = u.SystemLibrary.line_trace_single(world, a, b, u.TraceTypeQuery.TRACE_TYPE_QUERY2, cx,
                                            [G.P.STATE['pawn']], u.DrawDebugTrace.NONE, True)
    t = hit.to_tuple() if hit else None
    if not t or not t[0]:
        return None, None
    p = G.source(frame.reference(t[5]))
    return round(p[2], 3), (t[9].get_actor_label() if t[9] else None)


def tick(dt):
    try:
        if time.monotonic() - S['start'] < 4.0:
            return
        u.unregister_slate_post_tick_callback(S['handle'])
        proxy = None
        for a in u.GameplayStatics.get_all_actors_of_class(G.P.STATE['world'], u.StaticMeshActor):
            if a.get_actor_label() == 'COL_CockpitFloor47':
                c = a.static_mesh_component
                o, e = a.get_actor_bounds(False)
                proxy = dict(found=True, actor_collision=bool(a.get_actor_enable_collision()),
                             enabled=str(c.get_collision_enabled()), profile=str(c.get_collision_profile_name()),
                             object_type=str(c.get_collision_object_type()),
                             parent=a.get_attach_parent_actor().get_actor_label() if a.get_attach_parent_actor() else None,
                             centre=list(G.source(o)), extent_cm=[e.x, e.y, e.z],
                             visibility_response=str(c.get_collision_response_to_channel(u.CollisionChannel.ECC_VISIBILITY)))
        rows = []
        nx = int(round((X[1] - X[0]) / STEP)) + 1
        ny = int(round((Y[1] - Y[0]) / STEP)) + 1
        for i in range(nx):
            for j in range(ny):
                x, y = round(X[0] + i * STEP, 2), round(Y[0] + j * STEP, 2)
                zs, as_ = trace(x, y, False)
                zc, ac = trace(x, y, True)
                rows.append([x, y, zs, as_, zc, ac])
        (G.R / 'Pass47' / 'Floor47.json').write_text(json.dumps(dict(
            status='SUCCESS', proxy=proxy, grid=dict(x=X, y=Y, step=STEP),
            columns=['x', 'y', 'simple_z', 'simple_actor', 'complex_z', 'complex_actor'],
            rows=rows), indent=0), encoding='utf-8')
        u.SystemLibrary.quit_game(G.P.STATE['world'], G.P.STATE['pc'], u.QuitPreference.QUIT, False)
    except Exception:
        (G.R / 'Pass47' / 'Floor47.json').write_text(json.dumps(dict(status='ERROR', error=traceback.format_exc())), encoding='utf-8')


def start(game):
    global G
    G = game
    S.update(start=time.monotonic())
    (G.R / 'Pass47' / 'Floor47.json').write_text('{"status": "RUNNING"}', encoding='utf-8')
    S['handle'] = u.register_slate_post_tick_callback(tick)
