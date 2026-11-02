"""Pass45 collision diagnostic.

The containment audit recorded 418/436 lateral escapes, every one travelling
the full 4.0 m push. A capsule that is never blocked anywhere, in any
direction, is either a catastrophic collision failure or a flawed test. This
decides which, before anything is reported as a defect.

Decisive experiment: run the SAME capsule trace twice against the same
geometry, once with trace_complex=False and once with trace_complex=True.

  both hit            -> simple collision present; the actor-sweep test was wrong
  only complex hits   -> no simple collision; shape sweeps pass through, which
                         means character movement passes through too
  neither hits        -> nothing there at all

Control meshes are included so the bridge result can be compared against
geometry the player demonstrably collides with (terminal walls, ground).
"""
import unreal as u, json, time, traceback

G = None
S = {}

# (label, start_source, end_source) - each crosses a wall or deck we care about.
PROBES = [
    # Across bank A, mid-sleeve, at chest height. Should hit the sleeve wall.
    ('bridgeA_lateral_left', [-9.61, -0.33, 1.20], [-9.61, 3.67, 1.20]),
    ('bridgeA_lateral_right', [-9.61, -0.33, 1.20], [-9.61, -4.33, 1.20]),
    # Across bank B.
    ('bridgeB_lateral_left', [2.92, -2.03, 1.20], [2.92, 1.97, 1.20]),
    ('bridgeB_lateral_right', [2.92, -2.03, 1.20], [2.92, -6.03, 1.20]),
    # Down onto the bridge deck.
    ('bridgeA_deck_down', [-9.61, -0.33, 1.60], [-9.61, -0.33, -2.40]),
    # Controls: terminal west wall, and the terminal floor.
    ('terminal_west_wall', [-48.0, -4.25, 1.20], [-50.5, -4.25, 1.20]),
    ('terminal_floor_down', [-46.0, -13.0, 1.60], [-46.0, -13.0, -1.40]),
    ('checkin_floor_down', [-35.0, -13.0, 1.60], [-35.0, -13.0, -1.40]),
]

# Meshes to report collision configuration for.
MESH_PREFIXES = ('SM_AP_P38B_', 'SM_AP_Walls', 'SM_AP_Floors', 'SM_AP_Ground',
                 'SM_AP_Roofs', 'SM_AP_Shell')

CAPSULE_RADIUS = 34.0      # cm, typical UE character
CAPSULE_HALF = 88.0        # cm


def _cap_trace(world, a, b, complex_flag):
    hit = u.SystemLibrary.capsule_trace_single(
        world, a, b, CAPSULE_RADIUS, CAPSULE_HALF,
        u.TraceTypeQuery.TRACE_TYPE_QUERY1, complex_flag, [],
        u.DrawDebugTrace.NONE, True)
    if not hit:
        return None
    t = hit.to_tuple()
    if not t[0]:
        return None
    name = None
    mesh = None
    try:
        name = t[9].get_actor_label() if t[9] else None
    except Exception:
        pass
    try:
        c = t[10] if len(t) > 10 else None
        mesh = c.static_mesh.get_name() if c and c.static_mesh else None
    except Exception:
        pass
    return dict(actor=name, mesh=mesh, impact=[round(q, 3) for q in G.source(t[4])])


def _line_trace(world, a, b, complex_flag):
    hit = u.SystemLibrary.line_trace_single(
        world, a, b, u.TraceTypeQuery.TRACE_TYPE_QUERY1, complex_flag, [],
        u.DrawDebugTrace.NONE, True)
    if not hit:
        return None
    t = hit.to_tuple()
    if not t[0]:
        return None
    mesh = None
    try:
        c = t[10] if len(t) > 10 else None
        mesh = c.static_mesh.get_name() if c and c.static_mesh else None
    except Exception:
        pass
    return dict(mesh=mesh, impact=[round(q, 3) for q in G.source(t[4])])


def _mesh_config(world):
    """Collision configuration of representative meshes, from the live level."""
    seen = {}
    for a in u.GameplayStatics.get_all_actors_of_class(world, u.StaticMeshActor):
        try:
            c = a.static_mesh_component
            m = c.static_mesh
            if not m:
                continue
            name = m.get_name()
        except Exception:
            continue
        if not name.startswith(MESH_PREFIXES) or name in seen:
            continue
        row = dict(mesh=name, actor=a.get_actor_label())
        try:
            row['collision_enabled'] = str(c.get_collision_enabled())
        except Exception as e:
            row['collision_enabled'] = str(e)
        try:
            row['collision_profile'] = str(c.get_collision_profile_name())
        except Exception as e:
            row['collision_profile'] = str(e)
        try:
            row['collision_object_type'] = str(c.get_collision_object_type())
        except Exception as e:
            row['collision_object_type'] = str(e)
        try:
            bs = m.get_editor_property('body_setup')
            row['collision_trace_flag'] = str(bs.get_editor_property('collision_trace_flag'))
            agg = bs.get_editor_property('agg_geom')
            counts = {}
            for key in ('convex_elems', 'box_elems', 'sphere_elems', 'sphyl_elems'):
                try:
                    counts[key] = len(agg.get_editor_property(key))
                except Exception:
                    counts[key] = None
            row['simple_primitives'] = counts
            row['simple_primitive_total'] = sum(v for v in counts.values() if v)
        except Exception as e:
            row['body_setup'] = str(e)
        seen[name] = row
    return sorted(seen.values(), key=lambda q: q['mesh'])


def save(status='RUNNING', **kw):
    out = G.R / 'Pass45'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'Collision45.json').write_text(json.dumps(dict(
        status=status,
        question='does the same capsule trace block with simple collision, or only with complex?',
        capsule=dict(radius_cm=CAPSULE_RADIUS, half_height_cm=CAPSULE_HALF),
        pawn=S.get('pawn_info'),
        traces=S.get('traces', []),
        mesh_config=S.get('mesh_config', []), **kw), indent=2), encoding='utf-8')


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
        rows = []
        for label, a, b in PROBES:
            va, vb = G.v(a), G.v(b)
            rows.append(dict(
                probe=label, start=a, end=b,
                capsule_simple=_cap_trace(world, va, vb, False),
                capsule_complex=_cap_trace(world, va, vb, True),
                line_simple=_line_trace(world, va, vb, False),
                line_complex=_line_trace(world, va, vb, True)))
        S['traces'] = rows
        S['mesh_config'] = _mesh_config(world)
        stop('SUCCESS')
    except Exception:
        stop('ERROR', error=traceback.format_exc())


def start(game):
    global G
    G = game
    try:
        G.CAPTURE = True
        G.QA = True
        pawn = G.P.STATE['pawn']
        info = {}
        try:
            cap = pawn.get_component_by_class(u.CapsuleComponent)
            info['capsule_radius_cm'] = cap.get_scaled_capsule_radius()
            info['capsule_half_height_cm'] = cap.get_scaled_capsule_half_height()
            info['collision_enabled'] = str(cap.get_collision_enabled())
            info['collision_profile'] = str(cap.get_collision_profile_name())
        except Exception as e:
            info['error'] = str(e)
        try:
            mv = pawn.get_component_by_class(u.CharacterMovementComponent)
            info['movement_mode'] = str(mv.get_editor_property('movement_mode'))
        except Exception:
            pass
        S.update(pawn_info=info, traces=[], mesh_config=[],
                 next=time.monotonic() + 2.0)
        S['handle'] = u.register_slate_post_tick_callback(tick)
        save()
    except Exception:
        stop('ERROR', error=traceback.format_exc())
