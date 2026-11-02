"""Pass66: cabin ceiling and floor heights above/below each aisle, traced in -game (read-only).

The editor commandlet has no collision to trace against, so plane66_editor.py
reads these instead. For each aisle (x) every 0.5 m along y, one trace up from
1.3 m to 4 m (first ceiling surface) and one down from 1.3 m to -0.5 m (the
floor). Writes Pass48/Ceil66.json: {aisles: [[x, [[y, ceiling_z, label], ...], [[y, floor_z], ...]], ...]}.
Run: Run-GameProbe48.ps1 -Flag P48_ceil66_probe -Probe ceil66_probe.py -Report Ceil66.json
"""
import unreal as u, json, time, traceback

G = None
S = {}
AISLES = [(14.895, 12.0, 28.2), (17.105, 12.0, 28.2), (16.0, 3.0, 10.0)]


def hit(a, b, ignore):
    h = u.SystemLibrary.line_trace_single(G.P.STATE['world'], G.v(a), G.v(b), u.TraceTypeQuery.TRACE_TYPE_QUERY1, True, ignore,
                                          u.DrawDebugTrace.NONE, True)
    t = h.to_tuple() if h else None
    if not t or not t[0]:
        return None, None
    return round(G.source(t[5])[2], 3), (t[9].get_actor_label() if t[9] else None)


def tick(dt):
    try:
        if time.monotonic() < S['next']:
            return
        u.unregister_slate_post_tick_callback(S['handle'])
        ignore = [G.P.STATE['pawn']]
        out = []
        for x, y0, y1 in AISLES:
            ceil, floor = [], []
            y = y0
            while y <= y1 + 1e-6:
                c, lab = hit([x, y, 1.3], [x, y, 4.0], ignore)
                f, _ = hit([x, y, 1.3], [x, y, -.5], ignore)
                ceil.append([round(y, 2), c, lab]); floor.append([round(y, 2), f])
                y += .5
            out.append([x, ceil, floor])
        (G.R / 'Pass48' / 'Ceil66.json').write_text(json.dumps(dict(status='SUCCESS', aisles=out), indent=1), encoding='utf-8')
    except Exception:
        (G.R / 'Pass48' / 'Ceil66.json').write_text(json.dumps(dict(status='ERROR', error=traceback.format_exc())), encoding='utf-8')
    u.SystemLibrary.quit_game(G.P.STATE['world'], G.P.STATE['pc'], u.QuitPreference.QUIT, False)


def start(game):
    global G
    G = game
    (G.R / 'Pass48' / 'Ceil66.json').write_text(json.dumps(dict(status='RUNNING')), encoding='utf-8')
    S['next'] = time.monotonic() + 6.0
    S['handle'] = u.register_slate_post_tick_callback(tick)
