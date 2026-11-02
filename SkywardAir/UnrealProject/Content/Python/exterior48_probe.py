"""Pass48: exterior survey for the facade, canopy and site makeover (-game, read-only).

  facades  For each facade, traces from 7 m outside straight at the wall at
           five heights every 0.3 m along it: what is hit first and where
           (wall, glazing, door, planter, post), and the parapet top from a
           down-trace just inside the face.
  canopy   Down-traces (roof top) and up-traces (soffit) on a 0.5 m grid over
           the covered forecourt.
  ground   Down-traces on a 1 m grid west of the road (car park site) and
           along the terminal's north and south sides (planting beds),
           with the first thing hit.

Every static mesh is made traceable for this run only; nothing is saved.
"""
import unreal as u, json, time, traceback

G = None
S = {}
CH = u.TraceTypeQuery.TRACE_TYPE_QUERY1
HEIGHTS = (0.3, 1.2, 2.2, 3.0, 3.4)   # interior walls also use these (above the wainscot: 1.2..3.0)


def trace(a, b, ignore):
    h = u.SystemLibrary.line_trace_single(G.P.STATE['world'], G.v(a), G.v(b), CH, True, ignore,
                                          u.DrawDebugTrace.NONE, True)
    t = h.to_tuple() if h else None
    if not t or not t[0]:
        return None
    p = G.source(t[5])
    return [round(p[0], 3), round(p[1], 3), round(p[2], 3), t[9].get_actor_label() if t[9] else None]


def facade(f, ig):
    # f: name, axis ('x' = face normal along x), plane, out (+1/-1), span [a, b]
    out = dict(name=f['name'], samples=[])
    a = f['span'][0]
    while a <= f['span'][1] + 1e-6:
        row = dict(at=round(a, 2), hits={})
        for h in HEIGHTS:
            if f['axis'] == 'x':
                p0 = [f['plane'] + f.get('reach', 7) * f['out'], a, h]; p1 = [f['plane'] - f.get('depth', 14) * f['out'], a, h]
            else:
                p0 = [a, f['plane'] + f.get('reach', 7) * f['out'], h]; p1 = [a, f['plane'] - f.get('depth', 14) * f['out'], h]
            row['hits'][str(h)] = trace(p0, p1, ig)
        inside = [f['plane'] - .15 * f['out'], a, 14] if f['axis'] == 'x' else [a, f['plane'] - .15 * f['out'], 14]
        row['top'] = trace(inside, inside[:2] + [-1], ig)
        out['samples'].append(row)
        a += .3
    return out


def grid(rect, step, z0, z1, ig):
    x0, x1, y0, y1 = rect
    pts = []
    x = x0
    while x <= x1 + 1e-6:
        y = y0
        while y <= y1 + 1e-6:
            pts.append([round(x, 2), round(y, 2), trace([x, y, z0], [x, y, z1], ig)])
            y += step
        x += step
    return pts


def tick(dt):
    try:
        if time.monotonic() < S['next']:
            return
        u.unregister_slate_post_tick_callback(S['handle'])
        world = G.P.STATE['world']
        ig = [G.P.STATE['pawn']]
        for a in u.GameplayStatics.get_all_actors_of_class(world, u.StaticMeshActor):
            c = a.static_mesh_component
            if a.get_actor_label().startswith('Airport48 ') or a.get_editor_property('hidden'):
                ig.append(a); continue
            if c and c.get_collision_enabled() == u.CollisionEnabled.NO_COLLISION:
                c.set_collision_enabled(u.CollisionEnabled.QUERY_ONLY)
                c.set_collision_response_to_channel(u.CollisionChannel.ECC_VISIBILITY, u.CollisionResponseType.ECR_BLOCK)
        mode = (G.R / 'Pass48' / 'Exterior48Mode.txt').read_text(encoding='utf-8').strip()             if (G.R / 'Pass48' / 'Exterior48Mode.txt').exists() else 'exterior'
        if mode == 'walls':
            spec = json.loads((G.R / 'Pass48' / 'Walls48Spec.json').read_text(encoding='utf-8'))
            res = dict(status='SUCCESS', facades=[facade(f, ig) for f in spec['facades']])
            (G.R / 'Pass48' / 'Walls48.json').write_text(json.dumps(res), encoding='utf-8')
        else:
            spec = json.loads((G.R / 'Pass48' / 'Exterior48Spec.json').read_text(encoding='utf-8'))
            res = dict(status='SUCCESS', facades=[facade(f, ig) for f in spec['facades']])
            res['canopy_top'] = grid(spec['canopy'], .5, 9.0, 0.5, ig)
            res['canopy_soffit'] = grid(spec['canopy'], .5, 1.0, 9.0, ig)
            res['ground'] = {k: grid(r, 1.0, 12.0, -6.0, ig) for k, r in spec['ground'].items()}
            (G.R / 'Pass48' / 'Exterior48.json').write_text(json.dumps(res), encoding='utf-8')
    except Exception:
        (G.R / 'Pass48' / 'Exterior48.json').write_text(json.dumps(dict(status='ERROR', error=traceback.format_exc())),
                                                       encoding='utf-8')
    u.SystemLibrary.quit_game(G.P.STATE['world'], G.P.STATE['pc'], u.QuitPreference.QUIT, False)


def start(game):
    global G
    G = game
    walls = (G.R / 'Pass48' / 'Exterior48Mode.txt').exists() and         (G.R / 'Pass48' / 'Exterior48Mode.txt').read_text(encoding='utf-8').strip() == 'walls'
    (G.R / 'Pass48' / ('Walls48.json' if walls else 'Exterior48.json')).write_text(json.dumps(dict(status='RUNNING')), encoding='utf-8')
    S['next'] = time.monotonic() + 4.0
    S['handle'] = u.register_slate_post_tick_callback(tick)
