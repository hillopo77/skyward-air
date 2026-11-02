"""Pass71: the real wall nearest each fire extinguisher (read-only).

The Pass70 stands were placed from the layout file's wall lines, which are out of date since the hall was
rebuilt, so some stood by walls that are not there. Here the game decides: from each 'Usable extinguisher N'
(and its 'Safety station N'), 16 horizontal traces out to 7 m at 1.0 m and at 2.6 m. A direction counts as a
wall only if both heights hit within 4 cm of each other on a vertical face (furniture, signs and benches
stop at one height or the other). The nearest such wall wins. Writes Pass48/Walls71.json:
{stations: [{station, extinguisher, from, wall_point, normal, dist}]}.
Run: Run-GameProbe48.ps1 -Flag P48_walls71_probe -Probe walls71_probe.py -Report Walls71.json
"""
import unreal as u, json, math, time, traceback

G = None
S = {}


def hit(world, a, b, ignore):
    h = u.SystemLibrary.line_trace_single(world, a, b, u.TraceTypeQuery.TRACE_TYPE_QUERY1, True, ignore, u.DrawDebugTrace.NONE, True)
    t = h.to_tuple() if h else None
    return t if t and t[0] else None


def tick(dt):
    try:
        if time.monotonic() < S['next']:
            return
        u.unregister_slate_post_tick_callback(S['handle'])
        world = G.P.STATE['world']
        acts = {a.get_actor_label(): a for a in u.GameplayStatics.get_all_actors_of_class(world, u.StaticMeshActor)}
        KITS = [a for a in acts.values() if a.get_actor_label().startswith(('Airport70 security', 'Airport70 room'))]   # being replaced
        out = []
        for lab in sorted(l for l in acts if l.startswith('Safety station')):
            n = lab.split()[-1]
            st, ext = acts[lab], acts.get('Usable extinguisher ' + n)
            ignore = [G.P.STATE['pawn'], st] + ([ext] if ext else []) + KITS
            p = (ext or st).get_actor_location()
            floor = st.get_actor_location().z
            best = None; near = None
            for k in range(16):
                ang = 2 * math.pi * k / 16
                d = u.Vector(math.cos(ang), math.sin(ang), 0)
                lo = hit(world, u.Vector(p.x, p.y, floor + 100), u.Vector(p.x, p.y, floor + 100) + d * 700, ignore)
                hi = hit(world, u.Vector(p.x, p.y, floor + 260), u.Vector(p.x, p.y, floor + 260) + d * 700, ignore)
                if lo and abs(lo[7].z) < .2 and lo[3] < 200 and (near is None or lo[3] < near[0]):
                    near = (lo[3], lo, d)                                    # fallback: a flat face at 1 m within 2 m
                if not lo or not hi or abs(lo[3] - hi[3]) > 4 or abs(lo[7].z) > .2:
                    continue
                if best is None or lo[3] < best[0]:
                    best = (lo[3], lo, d)
            rec = dict(station=lab, extinguisher=ext.get_actor_label() if ext else None, at=G.source(p), floor=round(floor / 100, 3))
            if best is None and near is not None:
                best = near; rec['fallback'] = True
            if best:
                dist, t, d = best
                nrm = u.Vector(t[7].x, t[7].y, 0); nrm = nrm * (1.0 / max(nrm.length(), 1e-4))
                rec.update(wall_point=G.source(t[5]), normal=[round(nrm.x, 3), round(-nrm.y, 3)], dist=round(dist / 100, 3),
                           actor=t[9].get_actor_label() if t[9] else None)
            out.append(rec)
        (G.R / 'Pass48' / 'Walls71.json').write_text(json.dumps(dict(status='SUCCESS', stations=out), indent=1), encoding='utf-8')
    except Exception:
        (G.R / 'Pass48' / 'Walls71.json').write_text(json.dumps(dict(status='ERROR', error=traceback.format_exc())), encoding='utf-8')
    u.SystemLibrary.quit_game(G.P.STATE['world'], G.P.STATE['pc'], u.QuitPreference.QUIT, False)


def start(game):
    global G
    G = game
    (G.R / 'Pass48' / 'Walls71.json').write_text(json.dumps(dict(status='RUNNING')), encoding='utf-8')
    S['next'] = time.monotonic() + 6.0
    S['handle'] = u.register_slate_post_tick_callback(tick)
