"""Pass45 definitive bridge walk-off test.

Converts the wall probe's 124 candidates into confirmed or cleared, by asking
the game's OWN floor resolver rather than inferring from geometry.

For each candidate the probe steps outward from the bridge in 5 cm increments
and at each step asks:

  reachable  - is a horizontal path from just inside the polygon to this point
               unblocked at waist height? If a wall stops the player, the point
               is irrelevant however unsupported it is.
  floor      - what does airport_journey38.floor_at_source return here? That is
               the real resolver, including its polygon floors and priorities.
  physical   - does update_floor's 0.42 m physical fallback trace find support?

A point that is reachable, has no authored floor and no physical support is a
confirmed walk-off: the player walks there and update_floor starts applying
gravity.

Read-only: traces and function calls only, no actor is moved.
"""
import unreal as u, json, time, traceback

G = None
S = {}

OUT_STEPS = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.65, 0.80, 1.00]
WAIST = 0.95
FEET_EPS = 0.02
PER_TICK = 60


def save(status='RUNNING', **kw):
    out = G.R / 'Pass45'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'Walkoff45.json').write_text(json.dumps(dict(
        status=status,
        method='per candidate: reachability trace at waist height, then the '
               'real airport_journey38.floor_at_source, then the update_floor '
               'physical fallback trace',
        out_steps_m=OUT_STEPS,
        done=S.get('i', 0), total=len(S.get('cands', [])),
        confirmed=S.get('confirmed', []),
        blocked_by_wall=S.get('blocked', 0),
        supported=S.get('supported', 0), **kw), indent=2), encoding='utf-8')


def stop(status, **kw):
    save(status, **kw)
    try:
        u.unregister_slate_post_tick_callback(S['handle'])
    except Exception:
        pass
    u.SystemLibrary.quit_game(G.P.STATE['world'], G.P.STATE['pc'],
                              u.QuitPreference.QUIT, False)


def _blocked(world, a, b):
    hit = u.SystemLibrary.line_trace_single(
        world, a, b, u.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [],
        u.DrawDebugTrace.NONE, True)
    if not hit:
        return False
    return bool(hit.to_tuple()[0])


def _physical(world, x, y, feet):
    hit = u.SystemLibrary.line_trace_single(
        world, G.v([x, y, feet + .25]), G.v([x, y, feet - .42]),
        u.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [G.P.STATE['pawn']],
        u.DrawDebugTrace.NONE, True)
    if not hit:
        return None
    t = hit.to_tuple()
    if not t[0]:
        return None
    return G.source(t[5])[2]


def tick(dt):
    try:
        if time.monotonic() < S['next']:
            return
        world = G.P.STATE['world']
        J = S['J']
        n = 0
        while S['i'] < len(S['cands']) and n < PER_TICK:
            c = S['cands'][S['i']]
            S['i'] += 1
            n += 1
            px, py = c['point']
            nx, ny = c['normal']
            deck_z = c.get('deck_z', 0.0)
            inside = (px - nx * 0.18, py - ny * 0.18)
            reach_from = G.v([inside[0], inside[1], deck_z + WAIST])
            first_fall = None
            wall_at = None
            for d in OUT_STEPS:
                qx, qy = px + nx * d, py + ny * d
                if _blocked(world, reach_from, G.v([qx, qy, deck_z + WAIST])):
                    wall_at = d
                    break
                floor, name = J.floor_at_source(qx, qy, deck_z + FEET_EPS)
                if floor is not None:
                    continue
                phys = _physical(world, qx, qy, deck_z + FEET_EPS)
                if phys is None:
                    first_fall = dict(distance_m=d, point=[round(qx, 3), round(qy, 3)])
                    break
            if wall_at is not None and first_fall is None:
                S['blocked'] += 1
            elif first_fall is None:
                S['supported'] += 1
            else:
                S['confirmed'].append(dict(
                    polygon=c['polygon'], edge_point=[px, py],
                    normal=[nx, ny], deck_z=deck_z,
                    wall_blocked_at_m=wall_at, **first_fall))
        if S['i'] >= len(S['cands']):
            stop('SUCCESS')
        elif S['i'] % 300 < PER_TICK:
            save()
    except Exception:
        stop('ERROR', error=traceback.format_exc())


def start(game):
    global G
    G = game
    try:
        G.CAPTURE = True
        G.QA = True
        import airport_journey38 as J
        src = json.loads((G.R / 'Pass45' / 'WallProbe45.json').read_text(encoding='utf-8'))
        polyz = {z.get('name'): float(z.get('z', z.get('height', 0)))
                 for z in G.D['aircraft38']['bridge']['floor_polygons']}
        cands = []
        for q in src['open_samples']:
            if len(q['open_heights']) < 4:
                continue
            cands.append(dict(polygon=q['polygon'], point=q['point'],
                              normal=q['normal'],
                              deck_z=polyz.get(q['polygon'], 0.0)))
        S.update(J=J, cands=cands, i=0, confirmed=[], blocked=0, supported=0,
                 next=time.monotonic() + 2.0)
        S['handle'] = u.register_slate_post_tick_callback(tick)
        save()
    except Exception:
        S.setdefault('cands', [])
        stop('ERROR', error=traceback.format_exc())
