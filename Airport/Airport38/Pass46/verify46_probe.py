"""Pass46 / P46-015: prove in -game which items actually block.

Setting a component to QUERY_AND_PHYSICS/BlockAll does not by itself make a
mesh solid - if the mesh carries no usable collision data the setting has no
effect, and body_setup cannot be reached from Python in this engine build to
check or fix that. So the setting has to be tested, not trusted.

It cannot be tested where it is set: under -run=pythonscript -NullRHI no
physics query answers at all, proven by a control trace onto the check-in hall
floor coming back empty. This probe runs in -game, the mode the journey itself
traces in, behind its own read-only flag.

Three things are measured.

  control    A downward trace onto the check-in floor and a trace into a
             terminal wall. Both must hit. If they do not, this probe reports
             nothing else, because an empty trace would then mean nothing.

  solidity   For each of the twelve, a trace across the actor at a height
             inside it, starting clear of its own bounds. Hitting that actor is
             the pass. Also run for the ten plants P46-014 claimed to fix and
             never checked.

  tunnel     Along the scanned bag's own path through each X-ray scanner at
             z=1.375, the release height qa_scanner38 records. This must stay
             clear, or the registered bag jams inside the scanner and the scan
             never completes.

Read-only. No actor is modified and nothing is saved.
"""
import unreal as u, json, time, traceback

G = None
S = {}

TARGETS = [
    ('Queue post31 0', 'queue post'), ('Queue post31 1', 'queue post'),
    ('Queue post31 2', 'queue post'), ('Queue post31 3', 'queue post'),
    ('Queue post31 4', 'queue post'), ('Queue post31 5', 'queue post'),
    ('Stanchion24_1725', 'stanchion'), ('Stanchion24_1726', 'stanchion'),
    ('Stanchion24_1738', 'stanchion'), ('Stanchion24_1739', 'stanchion'),
    ('X-ray scanner 01', 'scanner'), ('X-ray scanner 02', 'scanner'),
]

# P46-014 set these to block and never tested the result. Same question.
PLANTS = ['Plant1224_1761', 'Plant1224_1771', 'Plant1224_1772',
          'Plant1224_1773', 'Plant1224_1824', 'Plant1224_1825',
          'Plant1224_1826', 'Plant1224_1827', 'Plant1224_1828',
          'Plant1224_1829']

TUNNELS = [('X-ray scanner 01', -43.15), ('X-ray scanner 02', -38.05)]
BAG_Z = 1.375


def save(status='RUNNING', **extra):
    (G.R / 'Pass46' / 'Verify46.json').write_text(
        json.dumps(dict(status=status, control=S.get('control'),
                        solidity=S.get('solidity', []),
                        tunnels=S.get('tunnels', []),
                        missing=S.get('missing', []),
                        elapsed_s=time.monotonic() - S['start'], **extra),
                   indent=2), encoding='utf-8')


def trace(a, b):
    """Label of the first blocking actor from a to b in source coordinates."""
    hit = u.SystemLibrary.line_trace_single(
        G.P.STATE['world'], G.v(a), G.v(b), u.TraceTypeQuery.TRACE_TYPE_QUERY1,
        True, [G.P.STATE['pawn']], u.DrawDebugTrace.NONE, True)
    if not hit:
        return None
    t = hit.to_tuple()
    if not t[0]:
        return None
    for k in t:
        try:
            return k.get_actor_label()
        except Exception:
            continue
    return 'unnamed'


def bounds(actor):
    o, e = actor.get_actor_bounds(False)
    return ([o.x / 100.0, -o.y / 100.0, o.z / 100.0],
            [e.x / 100.0, e.y / 100.0, e.z / 100.0])


def tick(dt):
    try:
        # Let the level settle before asking the physics scene anything.
        if time.monotonic() - S['start'] < 3.0:
            return
        actors = {}
        for q in u.GameplayStatics.get_all_actors_of_class(G.P.STATE['world'],
                                                           u.Actor):
            try:
                actors[q.get_actor_label()] = q
            except Exception:
                continue

        floor = trace([-42.0, -13.0, 1.40], [-42.0, -13.0, -1.00])
        wall = trace([-45.5, -6.0, 1.40], [-52.0, -6.0, 1.40])
        S['control'] = dict(floor_below_checkin=floor, wall_to_the_west=wall,
                            passed=bool(floor) and bool(wall))
        save()
        if not S['control']['passed']:
            save('ABORTED', error='Trace control failed in -game too: floor=%r '
                                  'wall=%r. Reporting nothing further, because '
                                  'an empty trace would not mean anything.'
                                  % (floor, wall))
            u.unregister_slate_post_tick_callback(S['handle'])
            return

        S['solidity'] = []
        S['missing'] = []
        for name, kind in TARGETS + [(p, 'plant (P46-014)') for p in PLANTS]:
            a = actors.get(name)
            if a is None:
                S['missing'].append(name)
                continue
            c, e = bounds(a)
            # A height inside the actor, low enough that the floor is not in
            # the way and high enough to be real geometry.
            z = max(0.35, min(c[2] + e[2] * 0.3, 1.40))
            # Fire from four sides with a short standoff. One ray is not
            # enough: a wall or a pane within the standoff stops the ray
            # before the actor and the result says nothing either way. Pass if
            # any ray reaches this actor; only report a failure when every ray
            # had a clear run at it.
            rays = []
            for tag, dx, dy in (('from -x', -1, 0), ('from +x', 1, 0),
                                ('from -y', 0, -1), ('from +y', 0, 1)):
                off = (e[0] if dx else e[1]) + 0.45
                start = [c[0] + dx * off, c[1] + dy * off, z]
                end = [c[0] - dx * off, c[1] - dy * off, z]
                rays.append(dict(dir=tag, start=[round(v, 3) for v in start],
                                 end=[round(v, 3) for v in end],
                                 hit=trace(start, end)))
            reached = [r for r in rays if r['hit'] == name]
            clear_run = [r for r in rays if r['hit'] is None]
            hit = reached[0]['hit'] if reached else (
                next((r['hit'] for r in rays if r['hit']), None))
            row = dict(actor=name, kind=kind, trace_z=round(z, 3), rays=rays,
                       reached_from=[r['dir'] for r in reached], hit=hit,
                       solid=bool(reached),
                       conclusive=bool(reached) or bool(clear_run))
            try:
                comp = a.static_mesh_component
                row['collision_enabled'] = str(comp.get_collision_enabled())
                row['profile'] = str(comp.get_collision_profile_name())
            except Exception:
                pass
            if not row['solid'] and not row['conclusive']:
                row['note'] = ('every ray was stopped by other geometry (%s) '
                               'before reaching this actor, so this run says '
                               'nothing about whether it is solid'
                               % ', '.join(sorted({r['hit'] for r in rays
                                                   if r['hit']})))
            elif not row['solid']:
                row['note'] = ('at least one ray had a clear run at this '
                               'actor and passed straight through it, so it '
                               'is not solid')
            S['solidity'].append(row)
        save()

        S['tunnels'] = []
        for name, x in TUNNELS:
            if name not in actors:
                continue
            hit = trace([x, 1.20, BAG_Z], [x, 4.90, BAG_Z])
            S['tunnels'].append(dict(
                actor=name, x=x, z=BAG_Z, hit_along_bag_path=hit,
                open=hit != name,
                means=('clear for the scanned bag' if hit != name else
                       'the scanner body now blocks the bag path; the bag '
                       'would jam inside and the scan would never complete')))
        save('SUCCESS')
        print('VERIFY46 SUCCESS solid=%d of %d'
              % (sum(1 for q in S['solidity'] if q['solid']),
                 len(S['solidity'])), flush=True)
        u.unregister_slate_post_tick_callback(S['handle'])
    except Exception:
        save('ERROR', error=traceback.format_exc())
        u.unregister_slate_post_tick_callback(S['handle'])
        raise


def start(game):
    global G
    G = game
    S.update(start=time.monotonic())
    S['handle'] = u.register_slate_post_tick_callback(tick)
    save()
