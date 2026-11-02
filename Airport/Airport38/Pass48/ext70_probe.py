"""Pass70: which side of each fire-extinguisher station is the wall? (read-only)

For every 'Safety station N' (and its 'Usable extinguisher N'), traces out 1.6 m
in the four horizontal directions at 1.0 m, ignoring the station, the
extinguisher and the player, and records the nearest hit (distance, point,
normal, actor). props70_editor.py turns each new stand to face away from it.
Writes Pass48/Ext70.json.
Run: Run-GameProbe48.ps1 -Flag P48_ext70_probe -Probe ext70_probe.py -Report Ext70.json
"""
import unreal as u, json, time, traceback

G = None
S = {}


def tick(dt):
    try:
        if time.monotonic() < S['next']:
            return
        u.unregister_slate_post_tick_callback(S['handle'])
        world = G.P.STATE['world']
        acts = {a.get_actor_label(): a for a in u.GameplayStatics.get_all_actors_of_class(world, u.StaticMeshActor)}
        out = []
        for lab, a in sorted(acts.items()):
            if not lab.startswith('Safety station'):
                continue
            n = lab.split()[-1]
            ext = acts.get('Usable extinguisher ' + n)
            ignore = [G.P.STATE['pawn'], a] + ([ext] if ext else [])
            p = a.get_actor_location(); o, e = a.get_actor_bounds(False)
            c = u.Vector(o.x, o.y, p.z + 100 if p.z < 50 else 100)
            hits = []
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                end = c + u.Vector(dx, dy, 0) * 160
                h = u.SystemLibrary.line_trace_single(world, c, end, u.TraceTypeQuery.TRACE_TYPE_QUERY1, True, ignore,
                                                      u.DrawDebugTrace.NONE, True)
                t = h.to_tuple() if h else None
                if t and t[0]:
                    hits.append(dict(dir=[dx, dy], dist=round(t[3], 1), point=G.source(t[5]), normal=[round(t[7].x, 2), round(t[7].y, 2)],
                                     actor=t[9].get_actor_label() if t[9] else None))
            r = a.get_actor_rotation()
            out.append(dict(station=lab, extinguisher=ext.get_actor_label() if ext else None, at=G.source(p), centre=G.source(o),
                            yaw=round(r.yaw, 1), ext_at=G.source(ext.get_actor_location()) if ext else None, hits=hits,
                            floor=G.source(p)[2]))
        (G.R / 'Pass48' / 'Ext70.json').write_text(json.dumps(dict(status='SUCCESS', stations=out), indent=1), encoding='utf-8')
    except Exception:
        (G.R / 'Pass48' / 'Ext70.json').write_text(json.dumps(dict(status='ERROR', error=traceback.format_exc())), encoding='utf-8')
    u.SystemLibrary.quit_game(G.P.STATE['world'], G.P.STATE['pc'], u.QuitPreference.QUIT, False)


def start(game):
    global G
    G = game
    (G.R / 'Pass48' / 'Ext70.json').write_text(json.dumps(dict(status='RUNNING')), encoding='utf-8')
    S['next'] = time.monotonic() + 6.0
    S['handle'] = u.register_slate_post_tick_callback(tick)
