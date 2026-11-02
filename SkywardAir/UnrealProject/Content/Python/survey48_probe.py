"""Pass48: ceiling survey for the baffle ceilings (-game, read-only).

For every room in Ceilings48.json:
  ceiling   upward traces on a 0.5 m grid from z 2.2: the ceiling union's
            height, and anything else hit first (boards, signs, rods) with
            its height and label.
  lines     for each planned baffle line, horizontal traces along it at the
            middle of the baffle band, restarted past every hit, giving the
            free intervals a baffle can occupy without touching anything.
            Rooms with a 'wave' (Pass49) are also traced at the depths the
            wave baffles reach ('bands', metres below the ceiling), so a
            wave only deepens where nothing stands at that height.

So that nothing is missed, every static mesh in the level is made to block
the trace channel for the length of this run only (NoCollision parts such as
signs included); nothing is saved. The old light fittings are ignored, since
the makeover replaces them.
"""
import unreal as u, json, time, traceback

G = None
S = {}
CEILING = 'Airport38 coherent ceiling union'
IGNORE = ('Airport38 role-based down-facing practical fixtures', 'Airport48 oak baffle ceilings and lighting')
CH = u.TraceTypeQuery.TRACE_TYPE_QUERY1


def trace(a, b, ignore):
    h = u.SystemLibrary.line_trace_single(G.P.STATE['world'], G.v(a), G.v(b), CH, True, ignore,
                                          u.DrawDebugTrace.NONE, True)
    t = h.to_tuple() if h else None
    if not t or not t[0]:
        return None
    return list(G.source(t[5])), (t[9].get_actor_label() if t[9] else None)


def survey(room, ignore):
    x0, x1, y0, y1 = room['rect']
    out = dict(name=room['name'], ceiling=[], others=[], lines=[])
    k = 0.5
    xs = [x0 + .25 + k * i for i in range(int((x1 - x0) / k))]
    ys = [y0 + .25 + k * i for i in range(int((y1 - y0) / k))]
    for x in xs:
        for y in ys:
            r = trace([x, y, room.get('trace_from', 2.2)], [x, y, 9.0], ignore)
            if not r:
                continue
            p, lab = r
            if lab == room.get('ceiling_label', CEILING):
                out['ceiling'].append([round(x, 2), round(y, 2), round(p[2], 3)])
            else:
                out['others'].append([round(x, 2), round(y, 2), round(p[2], 3), lab])
    cz = [c[2] for c in out['ceiling']]
    c = min(cz) if cz else room['ceiling']
    out['ceiling_min'], out['ceiling_max'] = round(c, 3), round(max(cz) if cz else c, 3)
    zb = room.get('ceiling', c) - room.get('band_mid', .08)     # the declared ceiling the baffles hang from
    axis = room['axis']
    a0, a1 = (x0, x1) if axis == 'x' else (y0, y1)
    b0, b1 = (y0, y1) if axis == 'x' else (x0, x1)
    pitch = room['pitch']
    n = int((b1 - b0) / pitch)
    off = (b1 - b0 - (n - 1) * pitch) / 2

    def free_along(b, z):
        free, s, hits = [], a0 - .6, []
        start = s
        for _ in range(60):
            pa = [s, b, z] if axis == 'x' else [b, s, z]
            pb = [a1 + .6, b, z] if axis == 'x' else [b, a1 + .6, z]
            r = trace(pa, pb, ignore)
            if not r:
                free.append([round(start, 3), round(a1 + .6, 3)])
                break
            p, lab = r
            h = p[0] if axis == 'x' else p[1]
            if h - start > .05:
                free.append([round(start, 3), round(h, 3)])
            hits.append([round(h, 3), lab])
            s = h + .02
            start = s
        return free, hits
    c_decl = room.get('ceiling', c)
    for i in range(n):
        b = b0 + off + i * pitch
        free, hits = free_along(b, zb)
        line = dict(at=round(b, 3), z=round(zb, 3), free=free, hits=hits)
        if room.get('wave'):
            line['bands'] = {str(d): free_along(b, c_decl - d)[0] for d in room['wave']['bands']}
        out['lines'].append(line)
    return out


def tick(dt):
    try:
        if time.monotonic() < S['next']:
            return
        u.unregister_slate_post_tick_callback(S['handle'])
        world = G.P.STATE['world']
        ignore = [G.P.STATE['pawn']]
        made = 0
        for a in u.GameplayStatics.get_all_actors_of_class(world, u.StaticMeshActor):
            lab = a.get_actor_label()
            if lab in IGNORE:
                ignore.append(a); continue
            c = a.static_mesh_component
            if c and c.get_collision_enabled() == u.CollisionEnabled.NO_COLLISION:
                c.set_collision_enabled(u.CollisionEnabled.QUERY_ONLY)
                c.set_collision_response_to_channel(u.CollisionChannel.ECC_VISIBILITY, u.CollisionResponseType.ECR_BLOCK)
                made += 1
        spec = json.loads((G.R / 'Pass48' / 'Ceilings48.json').read_text(encoding='utf-8'))
        res = [survey(r, ignore) for r in spec['rooms']]
        (G.R / 'Pass48' / 'Survey48.json').write_text(json.dumps(dict(status='SUCCESS', made_traceable=made,
                                                                       rooms=res)), encoding='utf-8')
    except Exception:
        (G.R / 'Pass48' / 'Survey48.json').write_text(json.dumps(dict(status='ERROR', error=traceback.format_exc())),
                                                      encoding='utf-8')
    u.SystemLibrary.quit_game(G.P.STATE['world'], G.P.STATE['pc'], u.QuitPreference.QUIT, False)


def start(game):
    global G
    G = game
    (G.R / 'Pass48' / 'Survey48.json').write_text(json.dumps(dict(status='RUNNING')), encoding='utf-8')
    S['next'] = time.monotonic() + 4.0
    S['handle'] = u.register_slate_post_tick_callback(tick)
