"""Pass45 bridge wall perimeter probe.

Established so far:
  - the player is a FloatingPawnMovement pawn with no capsule; vertical support
    comes from floor polygons, then a 0.42 m physical trace, then gravity
  - the deployed bridge floor polygons tile correctly
  - deck mesh extends ~0.37 m beyond the polygons on each side, which the
    physical-trace fallback would support

So a walk-off cannot be a floor hole. It has to be horizontal: somewhere the
player can leave the polygon sideways because no wall stops them, and then run
out of deck.

This probe walks the boundary of each deployed bridge floor polygon and traces
outward, perpendicular to that edge, at several heights. A sample where
nothing blocks within the reach distance is a place the player can walk out.
Heights are chosen around the pawn: feet, knee, waist and eye.

Read-only: traces only.
"""
import unreal as u, json, time, math, traceback

G = None
S = {}

EDGE_STEP = 0.10      # m along each polygon edge
REACH = 1.10          # m outward; a wall should be within this
HEIGHTS = [0.12, 0.45, 0.95, 1.55]
INSET = 0.05          # start the trace just inside the polygon


def _polys():
    out = []
    for z in G.D['aircraft38']['bridge']['floor_polygons']:
        out.append((z.get('name', '?'), z['polygon'], float(z.get('z', z.get('height', 0)))))
    return out


def _inside(poly, x, y):
    n = len(poly)
    c = False
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            c = not c
        j = i
    return c


def _any_poly(x, y):
    for name, poly, z in S['polys']:
        if _inside(poly, x, y):
            return name
    return None


def _build():
    """Outward normal samples along every polygon edge."""
    steps = []
    for name, poly, pz in S['polys']:
        n = len(poly)
        for i in range(n):
            x0, y0 = poly[i]
            x1, y1 = poly[(i + 1) % n]
            dx, dy = x1 - x0, y1 - y0
            length = math.hypot(dx, dy)
            if length < 1e-6:
                continue
            ux, uy = dx / length, dy / length
            # two candidate normals; pick the one pointing out of this polygon
            nx, ny = -uy, ux
            mx, my = (x0 + x1) / 2.0, (y0 + y1) / 2.0
            if _inside(poly, mx + nx * 0.05, my + ny * 0.05):
                nx, ny = -nx, -ny
            count = max(1, int(length / EDGE_STEP))
            for k in range(count + 1):
                t = min(1.0, (k * EDGE_STEP) / length)
                px, py = x0 + dx * t, y0 + dy * t
                # Skip samples whose outward side is another bridge polygon:
                # those are interior joints, not the outside world.
                if _any_poly(px + nx * 0.18, py + ny * 0.18):
                    continue
                steps.append((name, i, round(px, 3), round(py, 3),
                              round(nx, 4), round(ny, 4), pz))
    return steps


def save(status='RUNNING', **kw):
    out = G.R / 'Pass45'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'WallProbe45.json').write_text(json.dumps(dict(
        status=status,
        method=dict(edge_step_m=EDGE_STEP, reach_m=REACH, heights_m=HEIGHTS,
                    rule='a sample is OPEN when no geometry blocks within reach '
                         'at that height, outward along the edge normal'),
        done=S.get('i', 0), total=len(S.get('steps', [])),
        open_samples=S.get('open', []),
        blocked_count=S.get('blocked', 0), **kw), indent=2), encoding='utf-8')


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
        while S['i'] < len(S['steps']) and n < 400:
            name, edge, px, py, nx, ny, pz = S['steps'][S['i']]
            S['i'] += 1
            n += 1
            opens = []
            for h in HEIGHTS:
                a = G.v([px - nx * INSET, py - ny * INSET, pz + h])
                b = G.v([px + nx * REACH, py + ny * REACH, pz + h])
                hit = u.SystemLibrary.line_trace_single(
                    world, a, b, u.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [],
                    u.DrawDebugTrace.NONE, True)
                blocked = False
                if hit:
                    t = hit.to_tuple()
                    blocked = bool(t[0])
                if not blocked:
                    opens.append(h)
            if opens:
                # How far does deck persist outward from here?
                deck_run = 0.0
                for d in (0.1, 0.2, 0.3, 0.4, 0.5, 0.7, 0.9):
                    dd = u.SystemLibrary.line_trace_single(
                        world, G.v([px + nx * d, py + ny * d, pz + 0.40]),
                        G.v([px + nx * d, py + ny * d, pz - 0.42]),
                        u.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [],
                        u.DrawDebugTrace.NONE, True)
                    ok = False
                    if dd:
                        tt = dd.to_tuple()
                        ok = bool(tt[0])
                    if ok:
                        deck_run = d
                    else:
                        break
                S['open'].append(dict(polygon=name, edge=edge,
                                      point=[px, py], normal=[nx, ny],
                                      open_heights=opens,
                                      deck_persists_m=deck_run))
            else:
                S['blocked'] += 1
        if S['i'] >= len(S['steps']):
            stop('SUCCESS')
        elif S['i'] % 2000 < 400:
            save()
    except Exception:
        stop('ERROR', error=traceback.format_exc())


def start(game):
    global G
    G = game
    try:
        G.CAPTURE = True
        G.QA = True
        S['polys'] = _polys()
        S.update(steps=_build(), i=0, open=[], blocked=0,
                 next=time.monotonic() + 2.0)
        S['handle'] = u.register_slate_post_tick_callback(tick)
        save()
    except Exception:
        S.setdefault('steps', [])
        stop('ERROR', error=traceback.format_exc())
