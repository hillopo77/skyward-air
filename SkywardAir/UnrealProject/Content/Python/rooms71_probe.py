"""Pass71: where the walls and ceilings of security, the WC passage and the washrooms really are (read-only).

Pass70 hung its fit-out 0.09 m inside the layout wall lines; in the photos some of it never showed, so
the real faces differ. Here the game decides: along every wall of each room, every 0.5 m, a horizontal
trace from 1.6 m inside the line to 0.6 m beyond it at 0.6, 1.4, 2.2 and 2.9 m, ignoring the Pass70 kits
(the thing being replaced) and the people. And a vertical trace up from 2.0 m on a 1 m grid for the ceiling.
Writes Pass48/Rooms71.json: {rooms: {name: {walls: {S/N/W/E: [[along, z, inset, actor], ...]},
ceiling: [[x, y, z, actor], ...]}}}, inset = how far the face stands inside the layout line (m).
Run: Run-GameProbe48.ps1 -Flag P48_rooms71_probe -Probe rooms71_probe.py -Report Rooms71.json
"""
import unreal as u, json, time, traceback

G = None
S = {}
ROOMS = {'security': (-49, -36, -4, 10), 'wc_passage': (-26, -23, -12, -1), 'wc': (-23, -14, -12, -3)}
SKIP = ('Airport70 security', 'Airport70 room', 'CH12', 'Usable extinguisher', 'Safety station')


def hit(world, a, b, ignore):
    h = u.SystemLibrary.line_trace_single(world, a, b, u.TraceTypeQuery.TRACE_TYPE_QUERY1, True, ignore, u.DrawDebugTrace.NONE, True)
    t = h.to_tuple() if h else None
    return t if t and t[0] else None


def ue(x, y, z):
    return u.Vector(x * 100, -y * 100, z * 100)


def tick(dt):
    try:
        if time.monotonic() < S['next']:
            return
        u.unregister_slate_post_tick_callback(S['handle'])
        world = G.P.STATE['world']
        ignore = [G.P.STATE['pawn']] + [a for a in u.GameplayStatics.get_all_actors_of_class(world, u.Actor)
                                        if a.get_actor_label().startswith(SKIP) or isinstance(a, (u.Character, u.SkeletalMeshActor))]
        out = {}
        for name, (x0, x1, y0, y1) in ROOMS.items():
            walls = {}
            # (wall, fixed line, inward sign, along range, axis)
            for key, ax, k, sgn, a0, a1 in (('S', 'y', y0, 1, x0, x1), ('N', 'y', y1, -1, x0, x1),
                                             ('W', 'x', x0, 1, y0, y1), ('E', 'x', x1, -1, y0, y1)):
                rows = []
                n = int((a1 - a0) / .5)
                for i in range(1, n):
                    al = a0 + i * .5
                    for z in (.6, 1.4, 2.2, 2.9):
                        if ax == 'y':
                            p, q = ue(al, k + sgn * 1.6, z), ue(al, k - sgn * .6, z)
                        else:
                            p, q = ue(k + sgn * 1.6, al, z), ue(k - sgn * .6, al, z)
                        t = hit(world, p, q, ignore)
                        if t:
                            src = G.source(t[5])
                            face = src[1] if ax == 'y' else src[0]
                            rows.append([round(al, 2), z, round((face - k) * sgn, 3), t[9].get_actor_label() if t[9] else None])
                        else:
                            rows.append([round(al, 2), z, None, None])
                walls[key] = rows
            ceil = []
            for xi in range(int(x0) + 1, int(x1)):
                for yi in range(int(y0) + 1, int(y1)):
                    t = hit(world, ue(xi + .5, yi + .5, 2.0), ue(xi + .5, yi + .5, 8.0), ignore)
                    ceil.append([xi + .5, yi + .5, round(G.source(t[5])[2], 3) if t else None, t[9].get_actor_label() if t and t[9] else None])
            out[name] = dict(walls=walls, ceiling=ceil)
        (G.R / 'Pass48' / 'Rooms71.json').write_text(json.dumps(dict(status='SUCCESS', rooms=out)), encoding='utf-8')
    except Exception:
        (G.R / 'Pass48' / 'Rooms71.json').write_text(json.dumps(dict(status='ERROR', error=traceback.format_exc())), encoding='utf-8')
    u.SystemLibrary.quit_game(G.P.STATE['world'], G.P.STATE['pc'], u.QuitPreference.QUIT, False)


def start(game):
    global G
    G = game
    (G.R / 'Pass48' / 'Rooms71.json').write_text(json.dumps(dict(status='RUNNING')), encoding='utf-8')
    S['next'] = time.monotonic() + 6.0
    S['handle'] = u.register_slate_post_tick_callback(tick)
