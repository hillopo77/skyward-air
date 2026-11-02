"""Pass45 bridge deck raster.

The runtime stands the player on floor POLYGONS, not on engine collision --
the player pawn has no capsule component, so engine collision never contains
them. A walk-off therefore happens wherever real bridge deck exists but no
floor polygon covers it: the player walks onto visible deck and the runtime
finds no floor under them.

Rasterising the polygons alone cannot find this, because the shortfall is at
the polygon BOUNDARY, not an enclosed hole. This probe supplies the other
half: trace down over the whole bridge footprint and record where real deck
geometry is. The comparison against polygon coverage is done offline.

Read-only: traces only, no actor is moved or changed.
"""
import unreal as u, json, time, traceback

G = None
S = {}

X0, X1 = -14.60, 14.50
Y0, Y1 = -5.40, 2.70
STEP = 0.10
Z_TOP = 1.60       # above the deck, below the bridge roof
Z_BOTTOM = -1.20   # below the deck, above the apron
PER_TICK = 2500
DECK_PREFIX = 'SM_AP_P38B_'


def save(status='RUNNING', **kw):
    out = G.R / 'Pass45'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'DeckRaster45.json').write_text(json.dumps(dict(
        status=status,
        grid=dict(x0=X0, x1=X1, y0=Y0, y1=Y1, step=STEP,
                  z_top=Z_TOP, z_bottom=Z_BOTTOM),
        note='deck cells list only cells whose downward trace hit a '
             + DECK_PREFIX + ' mesh between z_top and z_bottom',
        done=S.get('i', 0), total=S.get('total', 0),
        deck=S.get('deck', []), **kw), indent=2), encoding='utf-8')


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
        while S['i'] < S['total'] and n < PER_TICK:
            idx = S['i']
            S['i'] += 1
            n += 1
            ix = idx // S['ny']
            iy = idx % S['ny']
            x = X0 + ix * STEP
            y = Y0 + iy * STEP
            hit = u.SystemLibrary.line_trace_single(
                world, G.v([x, y, Z_TOP]), G.v([x, y, Z_BOTTOM]),
                u.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [],
                u.DrawDebugTrace.NONE, True)
            if not hit:
                continue
            t = hit.to_tuple()
            if not t[0]:
                continue
            try:
                c = t[10] if len(t) > 10 else None
                mesh = c.static_mesh.get_name() if c and c.static_mesh else None
            except Exception:
                mesh = None
            if mesh and mesh.startswith(DECK_PREFIX):
                S['deck'].append([round(x, 3), round(y, 3),
                                  round(G.source(t[4])[2], 3), mesh])
        if S['i'] >= S['total']:
            stop('SUCCESS')
        elif S['i'] % 10000 < PER_TICK:
            save()
    except Exception:
        stop('ERROR', error=traceback.format_exc())


def start(game):
    global G
    G = game
    try:
        G.CAPTURE = True
        G.QA = True
        nx = int((X1 - X0) / STEP) + 1
        ny = int((Y1 - Y0) / STEP) + 1
        S.update(i=0, nx=nx, ny=ny, total=nx * ny, deck=[],
                 next=time.monotonic() + 2.0)
        S['handle'] = u.register_slate_post_tick_callback(tick)
        save()
    except Exception:
        stop('ERROR', error=traceback.format_exc())
