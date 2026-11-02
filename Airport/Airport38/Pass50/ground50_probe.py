"""Pass50: ground height and what stands at each planned planting / landmark spot (-game, read-only).

Pass50/Ground50Points.json: {"points": [[x, y], ...], "radius": r}. For every
point a trace from 40 m down gives the first surface and its actor, and four
more traces at the radius around it tell whether the spot is open (all five
land on the same ground within 0.15 m) or something stands there. Every static
mesh is made traceable for this run only, as in the Pass48 ceiling survey;
nothing is saved. Writes Pass50/Ground50.json.
"""
import unreal as u, json, math, time, traceback

G = None
S = {}
CH = u.TraceTypeQuery.TRACE_TYPE_QUERY1


def down(x, y, ignore):
    h = u.SystemLibrary.line_trace_single(G.P.STATE['world'], G.v([x, y, 40.0]), G.v([x, y, -20.0]), CH, True, ignore,
                                          u.DrawDebugTrace.NONE, True)
    t = h.to_tuple() if h else None
    if not t or not t[0]:
        return None
    return [round(G.source(t[5])[2], 3), t[9].get_actor_label() if t[9] else None]


def tick(dt):
    try:
        if time.monotonic() < S['next']:
            return
        u.unregister_slate_post_tick_callback(S['handle'])
        world = G.P.STATE['world']
        ignore = [G.P.STATE['pawn']]
        for a in u.GameplayStatics.get_all_actors_of_class(world, u.StaticMeshActor):
            c = a.static_mesh_component
            if c and c.get_collision_enabled() == u.CollisionEnabled.NO_COLLISION:
                c.set_collision_enabled(u.CollisionEnabled.QUERY_ONLY)
                c.set_collision_response_to_channel(u.CollisionChannel.ECC_VISIBILITY, u.CollisionResponseType.ECR_BLOCK)
        spec = json.loads((G.R / 'Pass50' / 'Ground50Points.json').read_text(encoding='utf-8'))
        r = spec.get('radius', 3.0)
        out = []
        for x, y in spec['points']:
            c = down(x, y, ignore)
            ring = [down(x + r * math.cos(a), y + r * math.sin(a), ignore) for a in (0, math.pi / 2, math.pi, 1.5 * math.pi)]
            ok = c is not None and all(q and q[1] == c[1] and abs(q[0] - c[0]) < .15 for q in ring)
            out.append(dict(p=[x, y], z=c[0] if c else None, on=c[1] if c else None, open=ok,
                            ring=[q[1] if q else None for q in ring]))
        (G.R / 'Pass50' / 'Ground50.json').write_text(json.dumps(dict(status='SUCCESS', points=out)), encoding='utf-8')
    except Exception:
        (G.R / 'Pass50' / 'Ground50.json').write_text(json.dumps(dict(status='ERROR', error=traceback.format_exc())),
                                                      encoding='utf-8')
    u.SystemLibrary.quit_game(G.P.STATE['world'], G.P.STATE['pc'], u.QuitPreference.QUIT, False)


def start(game):
    global G
    G = game
    (G.R / 'Pass50' / 'Ground50.json').write_text(json.dumps(dict(status='RUNNING')), encoding='utf-8')
    S['next'] = time.monotonic() + 4.0
    S['handle'] = u.register_slate_post_tick_callback(tick)
