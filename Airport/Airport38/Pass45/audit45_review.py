"""Pass45 whole-scene audit: bridge containment and unsupported objects.

Read-only. Moves the player pawn to probe containment and restores it at the
end; changes no actor transform, material, asset or setting.

Test 1 - bridge containment by real swept capsule movement.
  The existing perimeter_probes (7) and flow39_probes (48) contain NO jetbridge
  probe at all; bridge containment rests on a single centreline walk in the
  journey test. This samples the whole articulated centreline and attempts
  swept lateral and diagonal moves from each sample, then asks whether the
  pawn still has deck beneath it. A pawn with no deck under it has left the
  bridge, which is the defect the user reported.

Test 2 - unsupported object audit.
  For every placed static mesh, trace outward from its bounds in six
  directions. An object that contacts nothing in any direction within the
  tolerance is floating. Targets the recurring floating screen / sign /
  fitting / fastener complaint class.
"""
import unreal as u, json, time, math, traceback

G = None
S = {}

# Articulated centreline, source metres, from the placed sleeve instances.
BRIDGE_NODES = [
    ('terminal_neck', -14.00, 0.68),
    ('pivot_chamber', -12.10, 0.68),
    ('bankA_03', -4.62, -2.34),
    ('elbow_chamber', -1.50, -3.60),
    ('bankB_04', 7.33, -0.45),
    ('cab_mitre', 10.50, 0.68),
    ('docking_cab', 12.40, 0.68),
]

SAMPLE_SPACING = 0.25
LATERAL_PUSH = 4.0
DECK_TOLERANCE = 0.60
DOWN_PROBE = 6.0
FLOAT_TOLERANCE_CM = 12.0
MAX_SWEEPS_PER_TICK = 10
MAX_SUPPORT_PER_TICK = 40


def _centreline():
    pts = []
    for i in range(len(BRIDGE_NODES) - 1):
        n0, x0, y0 = BRIDGE_NODES[i]
        n1, x1, y1 = BRIDGE_NODES[i + 1]
        dx, dy = x1 - x0, y1 - y0
        seg = math.hypot(dx, dy)
        if seg < 1e-6:
            continue
        steps = max(1, int(seg / SAMPLE_SPACING))
        for s in range(steps):
            t = float(s) / steps
            pts.append((n0 + '->' + n1, x0 + dx * t, y0 + dy * t, dx / seg, dy / seg))
    return pts


def _trace(world, a, b, ignore):
    hit = u.SystemLibrary.line_trace_single(
        world, a, b, u.TraceTypeQuery.TRACE_TYPE_QUERY1, True, ignore,
        u.DrawDebugTrace.NONE, True)
    if not hit:
        return None
    t = hit.to_tuple()
    if not t[0]:
        return None
    return t


def _mesh_name(t):
    try:
        c = t[10] if len(t) > 10 else None
        return c.static_mesh.get_name() if c and c.static_mesh else None
    except Exception:
        return None


def _deck_z(world, x, y):
    t = _trace(world, G.v([x, y, 4.0]), G.v([x, y, -DOWN_PROBE]), [])
    if t is None:
        return None, None
    return G.source(t[4])[2], _mesh_name(t)


def _floor_below_pawn(world, pawn):
    sx, sy, sz = G.source(pawn.get_actor_location())
    feet = sz - S['half_height']
    t = _trace(world, G.v([sx, sy, feet + 0.10]),
               G.v([sx, sy, feet - DOWN_PROBE]), [pawn])
    if t is None:
        return None, None
    return feet - G.source(t[4])[2], _mesh_name(t)


def save(status='RUNNING', **kw):
    out = G.R / 'Pass45'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'Audit45.json').write_text(json.dumps(dict(
        status=status,
        method=dict(
            containment='swept player capsule, lateral and 45 degree diagonal; '
                        'escape = no deck within %.2f m beneath feet after move'
                        % DECK_TOLERANCE,
            support='six-direction trace from bounds, floating = no contact '
                    'within %.0f cm' % FLOAT_TOLERANCE_CM,
            sample_spacing_m=SAMPLE_SPACING, lateral_push_m=LATERAL_PUSH),
        phase=S.get('phase'),
        containment=dict(samples=S.get('c_done', 0),
                         total=len(S.get('c_steps', [])),
                         escapes=S.get('escapes', [])),
        support=dict(checked=S.get('s_done', 0),
                     total=len(S.get('s_actors', [])),
                     floating=S.get('floating', [])),
        **kw), indent=2), encoding='utf-8')


def stop(status, **kw):
    try:
        if S.get('restore'):
            p, r = S['restore']
            G.P.STATE['pawn'].set_actor_location(p, False, True)
            G.P.STATE['pc'].set_control_rotation(r)
    except Exception:
        pass
    save(status, **kw)
    try:
        u.unregister_slate_post_tick_callback(S['handle'])
    except Exception:
        pass
    u.SystemLibrary.quit_game(G.P.STATE['world'], G.P.STATE['pc'],
                              u.QuitPreference.QUIT, False)


def _containment_tick(world, pawn):
    done = 0
    while S['c_i'] < len(S['c_steps']) and done < MAX_SWEEPS_PER_TICK:
        seg, x, y, fx, fy, label, ox, oy = S['c_steps'][S['c_i']]
        S['c_i'] += 1
        S['c_done'] += 1
        done += 1
        deck, deck_mesh = S['deck_cache'].get((round(x, 3), round(y, 3)), (None, None))
        if deck is None:
            continue
        pawn.set_actor_location(G.v([x, y, deck + S['half_height'] + 0.05]), False, True)
        pawn.set_actor_location(G.v([x + ox * LATERAL_PUSH, y + oy * LATERAL_PUSH,
                                     deck + S['half_height'] + 0.05]), True, False)
        gap, mesh = _floor_below_pawn(world, pawn)
        ex, ey, ez = G.source(pawn.get_actor_location())
        moved = math.hypot(ex - x, ey - y)
        if gap is None or gap > DECK_TOLERANCE:
            S['escapes'].append(dict(
                segment=seg, direction=label,
                start=[round(x, 3), round(y, 3), round(deck, 3)],
                ended=[round(ex, 3), round(ey, 3), round(ez, 3)],
                lateral_travel_m=round(moved, 3),
                deck_gap_m=(None if gap is None else round(gap, 3)),
                surface_below=mesh, deck_mesh=deck_mesh))
    return S['c_i'] >= len(S['c_steps'])


def _support_tick(world):
    done = 0
    DIRS = [(0, 0, -1), (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1)]
    while S['s_i'] < len(S['s_actors']) and done < MAX_SUPPORT_PER_TICK:
        a = S['s_actors'][S['s_i']]
        S['s_i'] += 1
        S['s_done'] += 1
        done += 1
        if not u.SystemLibrary.is_valid(a):
            continue
        try:
            origin, extent = a.get_actor_bounds(False)
        except Exception:
            continue
        ex, ey, ez = extent.x, extent.y, extent.z
        if max(ex, ey, ez) < 2.0 or max(ex, ey, ez) > 1500.0:
            continue
        supported = False
        for dx, dy, dz in DIRS:
            start = u.Vector(origin.x + dx * (ex + 1.0),
                             origin.y + dy * (ey + 1.0),
                             origin.z + dz * (ez + 1.0))
            end = u.Vector(origin.x + dx * (ex + FLOAT_TOLERANCE_CM + 1.0),
                           origin.y + dy * (ey + FLOAT_TOLERANCE_CM + 1.0),
                           origin.z + dz * (ez + FLOAT_TOLERANCE_CM + 1.0))
            if _trace(world, start, end, [a]) is not None:
                supported = True
                break
        if not supported:
            S['floating'].append(dict(
                actor=a.get_actor_label(),
                centre=[round(q, 2) for q in G.source(origin)],
                extent_cm=[round(ex, 1), round(ey, 1), round(ez, 1)]))
    return S['s_i'] >= len(S['s_actors'])


def tick(dt):
    try:
        now = time.monotonic()
        if now < S['next']:
            return
        world = G.P.STATE['world']
        pawn = G.P.STATE['pawn']

        if S['phase'] == 'deck_scan':
            n = 0
            while S['d_i'] < len(S['c_pts']) and n < 60:
                seg, x, y, fx, fy = S['c_pts'][S['d_i']]
                S['deck_cache'][(round(x, 3), round(y, 3))] = _deck_z(world, x, y)
                S['d_i'] += 1
                n += 1
            if S['d_i'] >= len(S['c_pts']):
                steps = []
                for seg, x, y, fx, fy in S['c_pts']:
                    px, py = -fy, fx
                    for label, ox, oy in (
                            ('left', px, py), ('right', -px, -py),
                            ('left_forward_45', (px + fx) / 1.4142, (py + fy) / 1.4142),
                            ('right_forward_45', (-px + fx) / 1.4142, (-py + fy) / 1.4142)):
                        steps.append((seg, x, y, fx, fy, label, ox, oy))
                S.update(c_steps=steps, c_i=0, phase='containment')
                save()
            return

        if S['phase'] == 'containment':
            if _containment_tick(world, pawn):
                S.update(phase='support', s_i=0)
            save()
            return

        if S['phase'] == 'support':
            if _support_tick(world):
                S.update(phase='done')
                stop('SUCCESS')
            return
    except Exception:
        stop('ERROR', error=traceback.format_exc())


def start(game):
    global G
    G = game
    try:
        G.CAPTURE = True
        G.QA = True
        pawn = G.P.STATE['pawn']
        pc = G.P.STATE['pc']
        try:
            cap = pawn.get_component_by_class(u.CapsuleComponent)
            half = cap.get_scaled_capsule_half_height() / 100.0
        except Exception:
            half = 0.9
        actors = list(u.GameplayStatics.get_all_actors_of_class(
            G.P.STATE['world'], u.StaticMeshActor))
        S.update(phase='deck_scan', c_pts=_centreline(), d_i=0, deck_cache={},
                 c_steps=[], c_i=0, c_done=0, escapes=[],
                 s_actors=actors, s_i=0, s_done=0, floating=[],
                 half_height=half,
                 restore=(pawn.get_actor_location(), pc.get_control_rotation()),
                 next=time.monotonic() + 2.0)
        S['handle'] = u.register_slate_post_tick_callback(tick)
        save()
    except Exception:
        S.setdefault('phase', 'start')
        stop('ERROR', error=traceback.format_exc())
