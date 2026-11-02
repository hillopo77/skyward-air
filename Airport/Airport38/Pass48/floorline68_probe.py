"""Pass68: what draws the thin line down the middle of each cabin aisle? (read-only)

Traces straight down across each aisle centre in 5 mm steps at a few rows and
records the actor, component, mesh, material and height of every hit, plus
every actor whose bounds straddle the aisle centreline near the floor.
Writes Pass48/FloorLine68.json.
Run: Run-GameProbe48.ps1 -Flag P48_floorline68_probe -Probe floorline68_probe.py -Report FloorLine68.json
"""
import unreal as u, json, time, traceback

G = None
S = {}
AISLES = (14.895, 17.105, 16.0)
ROWS = {14.895: (15.0, 20.0, 25.0), 17.105: (15.0, 20.0, 25.0), 16.0: (5.0, 8.0)}


def hits(a, b, ignore):
    out = []
    hs = u.SystemLibrary.line_trace_multi(G.P.STATE['world'], G.v(a), G.v(b), u.TraceTypeQuery.TRACE_TYPE_QUERY1, True, ignore,
                                          u.DrawDebugTrace.NONE, True)
    for h in hs or []:
        t = h.to_tuple()
        act, comp = t[9], t[10] if len(t) > 10 else None
        mesh = mat = None
        try:
            mesh = comp.static_mesh.get_name() if comp and hasattr(comp, 'static_mesh') and comp.static_mesh else None
            mat = comp.get_material(t[13] if len(t) > 13 and isinstance(t[13], int) else 0)
            mat = mat.get_name() if mat else None
        except Exception:
            pass
        out.append(dict(z=round(G.source(t[5])[2], 4), actor=act.get_actor_label() if act else None,
                        comp=comp.get_name() if comp else None, mesh=mesh, mat=mat))
    return out


def tick(dt):
    try:
        if time.monotonic() < S['next']:
            return
        u.unregister_slate_post_tick_callback(S['handle'])
        ignore = [G.P.STATE['pawn']]
        R = dict(status='SUCCESS', traces=[], straddle=[])
        for ax in AISLES:
            for y in ROWS[ax]:
                for k in range(-8, 9):
                    x = ax + k * .005
                    R['traces'].append(dict(x=round(x, 4), y=y, hits=hits([x, y, .6], [x, y, -.3], ignore)))
        for a in u.GameplayStatics.get_all_actors_of_class(G.P.STATE['world'], u.Actor):
            try:
                o, e = a.get_actor_bounds(False)
            except Exception:
                continue
            sx, sy, sz = o.x / 100, -o.y / 100, o.z / 100
            if 12 < sx < 20 and e.x < 12 and e.y > 50 and sz - e.z / 100 < .08 and sz + e.z / 100 > -.05:
                for ax in AISLES:
                    if abs(sx - ax) < .03:
                        R['straddle'].append(dict(actor=a.get_actor_label(), cls=a.get_class().get_name(), x=round(sx, 4),
                                                  y=round(sy, 2), half=[round(e.x / 100, 4), round(e.y / 100, 2), round(e.z / 100, 4)]))
        (G.R / 'Pass48' / 'FloorLine68.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
    except Exception:
        (G.R / 'Pass48' / 'FloorLine68.json').write_text(json.dumps(dict(status='ERROR', error=traceback.format_exc())), encoding='utf-8')
    u.SystemLibrary.quit_game(G.P.STATE['world'], G.P.STATE['pc'], u.QuitPreference.QUIT, False)


def start(game):
    global G
    G = game
    (G.R / 'Pass48' / 'FloorLine68.json').write_text(json.dumps(dict(status='RUNNING')), encoding='utf-8')
    S['next'] = time.monotonic() + 6.0
    S['handle'] = u.register_slate_post_tick_callback(tick)
