"""Pass46 / P46-020: measure the ground's outer edge so a skirt can meet it.

From the flight vantage the world visibly ends: the Flight39 graded airfield
slab (source x -200..500, y -2600..800) stops in a straight edge with the sky
dome's lower half showing beyond it, about 150 m west of the forecourt.

A skirt that is to meet that edge without a lip or a gap needs the edge's real
height, not the slab's bounding-box top. This traces down at 25 m steps, 3 m
inside each of the four edges, and records the surface height and actor.

Read-only.
"""
import unreal as u, json, time, traceback

G = None
S = {}
RECT = (-200.0, 500.0, -2600.0, 800.0)
INSET, STEP = 3.0, 25.0


def _label(t):
    for i in (9, 10):
        try:
            return t[i].get_actor_label()
        except Exception:
            try:
                return t[i].get_owner().get_actor_label()
            except Exception:
                continue
    return 'unnamed'


def down(x, y):
    hit = u.SystemLibrary.line_trace_single(
        G.P.STATE['world'], G.v([x, y, 60.0]), G.v([x, y, -20.0]),
        u.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [G.P.STATE['pawn']],
        u.DrawDebugTrace.NONE, True)
    t = hit.to_tuple() if hit else None
    if not t or not t[0]:
        return None, None
    return round(G.source(t[5])[2], 3), _label(t)


def tick(dt):
    try:
        if time.monotonic() - S['start'] < 3.0:
            return
        x0, x1, y0, y1 = RECT
        edges = dict(west=[], east=[], south=[], north=[])
        y = y0
        while y <= y1 + 1e-6:
            for side, x in (('west', x0 + INSET), ('east', x1 - INSET)):
                z, a = down(x, y)
                edges[side].append([x, y, z, a])
            y += STEP
        x = x0
        while x <= x1 + 1e-6:
            for side, yy in (('south', y0 + INSET), ('north', y1 - INSET)):
                z, a = down(x, yy)
                edges[side].append([x, yy, z, a])
            x += STEP
        # And just outside each edge, to confirm there is nothing beyond.
        outside = dict(west=down(x0 - 20, -12.0), east=down(x1 + 20, -12.0),
                       south=down(150.0, y0 - 20), north=down(150.0, y1 + 20))
        (G.R / 'Pass46' / 'Edge46.json').write_text(json.dumps(dict(
            status='SUCCESS', rect=RECT, inset=INSET, step=STEP, edges=edges,
            outside=outside), indent=1), encoding='utf-8')
        print('EDGE46 SUCCESS', flush=True)
        u.unregister_slate_post_tick_callback(S['handle'])
        u.SystemLibrary.quit_game(G.P.STATE['world'], G.P.STATE['pc'],
                                  u.QuitPreference.QUIT, False)
    except Exception:
        (G.R / 'Pass46' / 'Edge46.json').write_text(json.dumps(dict(
            status='ERROR', error=traceback.format_exc())), encoding='utf-8')
        u.unregister_slate_post_tick_callback(S['handle'])


def start(game):
    global G
    G = game
    S.update(start=time.monotonic())
    (G.R / 'Pass46' / 'Edge46.json').write_text('{"status": "RUNNING"}', encoding='utf-8')
    S['handle'] = u.register_slate_post_tick_callback(tick)
