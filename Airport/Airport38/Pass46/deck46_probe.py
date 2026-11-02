"""Pass46 / P46-017: what would enabling the gallery deck's collision actually do?

`Crafted GalleryStair35` is the whole gallery kit in one mesh: both stair
flights, the landing, the 72 m2 deck slab (z 2.87..3.15), four piers, glass
guards and handrails. flow39 registers it collision 'none' by name, and
validate39 pins that as the "retained stair collision contract"; Flow39's
REPORT gives the reason - "preserving the existing stair navigation floors".
The player's height comes from floor_at_source, not from physics.

The ledger claim "physics objects fall through it" was an inference from that
'none'. P46-014 showed what inferences from config are worth here, so this
measures it, and measures the risks of changing it, in the running game:

  physics    Drops a 30 cm physics cube onto three deck points, plus a control
             onto the check-in floor, with the deck as it is. Then turns the
             deck's collision on for this session only and drops again, plus
             one cube released under the deck that must fall to the cafe floor.

  hull       The asset may carry an auto-generated simple hull: native38
             skips auto collision for 'none' assets but native_finish38
             (collision != 'complex') generates it. A hull of this mesh would be
             one convex wedge filling the cafe under the deck. Simple and
             complex traces under the deck tell the two apart.

  pawn       Sphere sweeps of the pawn's real collision (r 0.35, centre 1.62
             above the floor) up both flights, across the landing, onto the
             deck, across the deck and under it, with simple collision - the
             kind movement uses. This is the "stair navigation floors" concern,
             tested directly.

  mounts     P46-013/P46-019: the header mounts were built to the zone's
             nominal 3.80 m ceiling and never traced. Up-traces at each hanger,
             ignoring the mount itself, give the real ceiling underside.

Read-only as far as the saved level is concerned: the collision toggle and the
cubes exist only in this game session and are undone before it ends.
"""
import unreal as u, json, time, traceback

G = None
S = {}

STAIR = 'Crafted GalleryStair35'
DECK_POINTS = [(-46.0, 30.5), (-43.2, 27.6), (-42.2, 32.6)]
UNDER_DECK = (-45.0, 29.5)
CONTROL_FLOOR = (-42.0, -13.0)
CUBE = '/Engine/BasicShapes/Cube'
PAWN_R, EYE = 0.35, 1.62

# Nav-floor heights along the stair centreline x=-46.5, from Flow35's model:
# flight 1 y 17.80..20.68 rises 0 -> 1.575, landing to 22.08, flight 2 rises
# 1.575 -> 3.15 by y 25.0, then the deck.
STAIR_PATH = [(17.0, 0.0), (17.8, 0.0), (20.68, 1.575), (22.08, 1.575),
              (25.0, 3.15), (26.6, 3.15)]

HANGERS = [('Header0', -30.307, -12.80), ('Header0', -30.307, -10.40),
           ('Header1', -30.307, -15.80), ('Header1', -30.307, -13.40)]


def save(status='RUNNING', **extra):
    out = dict(status=status, **{k: v for k, v in S.items()
                                 if k not in ('handle', 'start', 'cubes',
                                              'stage', 'stage_at', 'actors')})
    out.update(extra)
    (G.R / 'Pass46' / 'Deck46.json').write_text(json.dumps(out, indent=1),
                                                 encoding='utf-8')


def _label(t):
    for i in (9, 10):
        try:
            a = t[i]
            return a.get_actor_label() if hasattr(a, 'get_actor_label') \
                else a.get_owner().get_actor_label()
        except Exception:
            continue
    return 'unnamed'


def line(a, b, complex_=True, ignore=()):
    hit = u.SystemLibrary.line_trace_single(
        G.P.STATE['world'], G.v(a), G.v(b), u.TraceTypeQuery.TRACE_TYPE_QUERY1,
        complex_, [G.P.STATE['pawn']] + list(ignore), u.DrawDebugTrace.NONE,
        True)
    t = hit.to_tuple() if hit else None
    if not t or not t[0]:
        return dict(hit=None)
    p = G.source(t[5])
    return dict(hit=_label(t), at=[round(p[0], 3), round(p[1], 3),
                                   round(p[2], 3)])


def sweep(a, b, complex_=False):
    hit = u.SystemLibrary.sphere_trace_single(
        G.P.STATE['world'], G.v(a), G.v(b), PAWN_R * 100.0,
        u.TraceTypeQuery.TRACE_TYPE_QUERY1, complex_, [G.P.STATE['pawn']],
        u.DrawDebugTrace.NONE, True)
    t = hit.to_tuple() if hit else None
    if not t or not t[0]:
        return dict(hit=None)
    p = G.source(t[5])
    return dict(hit=_label(t), at=[round(p[0], 3), round(p[1], 3),
                                   round(p[2], 3)])


def stair_state(a):
    c = a.static_mesh_component
    row = dict(actor_collision=bool(a.get_actor_enable_collision()),
               enabled=str(c.get_collision_enabled()),
               profile=str(c.get_collision_profile_name()))
    try:
        body = c.static_mesh.get_editor_property('body_setup')
        row['trace_flag'] = str(body.get_editor_property('collision_trace_flag'))
        agg = body.get_editor_property('agg_geom')
        row['simple_shapes'] = {k: len(agg.get_editor_property(k)) for k in
                                ('box_elems', 'sphere_elems', 'sphyl_elems',
                                 'convex_elems')}
    except Exception as e:
        row['body_setup'] = 'not readable here: %s' % str(e)[:120]
    return row


def spawn_cube(p):
    t = u.Transform(location=G.v(p), rotation=u.Rotator(0, 0, 0),
                    scale=u.Vector(0.3, 0.3, 0.3))
    a = u.GameplayStatics.begin_deferred_actor_spawn_from_class(
        G.P.STATE['world'], u.StaticMeshActor, t)
    u.GameplayStatics.finish_spawning_actor(a, t)
    c = a.static_mesh_component
    c.set_mobility(u.ComponentMobility.MOVABLE)
    c.set_static_mesh(u.load_asset(CUBE))
    a.set_actor_scale3d(u.Vector(0.3, 0.3, 0.3))
    a.set_actor_location(G.v(p), False, True)
    c.set_collision_profile_name('PhysicsActor')
    c.set_simulate_physics(True)
    c.wake_all_rigid_bodies()
    return a


def drop(points):
    S['cubes'] = []
    for name, p in points:
        try:
            S['cubes'].append((name, p, spawn_cube(p)))
        except Exception as e:
            S.setdefault('spawn_errors', []).append('%s: %s' % (name, e))


def settle():
    out = []
    for name, p, a in S['cubes']:
        z = G.source(a.get_actor_location())[2]
        under = line([p[0], p[1], z], [p[0], p[1], -1.0], True, [a])
        out.append(dict(where=name, released_z=p[2], rest_z=round(z, 3),
                        fell=round(p[2] - z, 3), resting_on=under.get('hit'),
                        support_z=under.get('at', [None] * 3)[2]))
        try:
            a.destroy_actor()
        except Exception:
            pass
    S['cubes'] = []
    return out


def set_stair(a, on):
    a.set_actor_enable_collision(on)
    c = a.static_mesh_component
    c.set_collision_enabled(u.CollisionEnabled.QUERY_AND_PHYSICS if on
                            else u.CollisionEnabled.NO_COLLISION)
    if on:
        c.set_collision_profile_name('BlockAll')


def pawn_sweeps():
    rows = []
    for (y0, f0), (y1, f1) in zip(STAIR_PATH, STAIR_PATH[1:]):
        a, b = [-46.5, y0, f0 + EYE], [-46.5, y1, f1 + EYE]
        rows.append(dict(leg='stair centreline y %.2f -> %.2f' % (y0, y1),
                         simple=sweep(a, b, False), complex=sweep(a, b, True)))
    for label, a, b in (
            ('across the deck at standing height',
             [-48.4, 29.0, 3.15 + EYE], [-41.6, 29.0, 3.15 + EYE]),
            ('cafe floor under the deck at standing height',
             [-48.4, 29.5, EYE], [-41.6, 29.5, EYE])):
        rows.append(dict(leg=label, simple=sweep(a, b, False),
                         complex=sweep(a, b, True)))
    return rows


def under_deck_traces():
    rows = []
    for z in (0.6, 1.62, 2.4):
        a, b = [-48.4, 29.5, z], [-41.6, 29.5, z]
        rows.append(dict(z=z, simple=line(a, b, False), complex=line(a, b, True)))
    for x, y in DECK_POINTS:
        a, b = [x, y, 5.0], [x, y, 1.0]
        rows.append(dict(down_at=[x, y], simple=line(a, b, False),
                         complex=line(a, b, True)))
    return rows


def tick(dt):
    try:
        now = time.monotonic()
        if now - S['start'] < 3.0 or now < S.get('stage_at', 0):
            return
        stage = S.get('stage', 0)
        if stage == 0:
            S['actors'] = {}
            for q in u.GameplayStatics.get_all_actors_of_class(
                    G.P.STATE['world'], u.Actor):
                try:
                    S['actors'][q.get_actor_label()] = q
                except Exception:
                    continue
            floor = line([-42.0, -13.0, 1.4], [-42.0, -13.0, -1.0])
            S['control'] = dict(floor=floor, passed=bool(floor.get('hit')))
            if not S['control']['passed']:
                save('ABORTED', error='floor control failed; nothing measured')
                u.unregister_slate_post_tick_callback(S['handle'])
                return
            stair = S['actors'][STAIR]
            S['stair_as_built'] = stair_state(stair)
            S['traces_as_built'] = under_deck_traces()
            S['sweeps_as_built'] = pawn_sweeps()
            # Header mounts: real ceiling above each hanger.
            mounts = [S['actors'].get('P46 header mount ' + h)
                      for h in ('Header0', 'Header1')]
            S['mounts'] = []
            for h, x, y in HANGERS:
                m = S['actors'].get('P46 header mount ' + h)
                row = dict(header=h, at=[x, y])
                if m is not None:
                    o, e = m.get_actor_bounds(False)
                    row['mount_top_z'] = round((o.z + e.z) / 100.0, 3)
                    row['mount_bottom_z'] = round((o.z - e.z) / 100.0, 3)
                row['ceiling'] = line([x, y, 3.40], [x, y, 6.0], True,
                                      [q for q in mounts if q])
                row['ceiling_with_mount'] = line([x, y, 3.40], [x, y, 6.0], True)
                if row['ceiling'].get('at') and 'mount_top_z' in row:
                    row['gap_mount_top_to_ceiling_m'] = round(
                        row['ceiling']['at'][2] - row['mount_top_z'], 3)
                S['mounts'].append(row)
            pts = [('deck %d' % i, [x, y, 3.85])
                   for i, (x, y) in enumerate(DECK_POINTS)]
            pts.append(('control: check-in floor',
                        [CONTROL_FLOOR[0], CONTROL_FLOOR[1], 0.9]))
            drop(pts)
            S.update(stage=1, stage_at=now + 3.5)
            save()
            return
        if stage == 1:
            S['drop_as_built'] = settle()
            stair = S['actors'][STAIR]
            set_stair(stair, True)
            S['stair_enabled'] = stair_state(stair)
            S.update(stage=2, stage_at=now + 0.5)
            save()
            return
        if stage == 2:
            S['traces_enabled'] = under_deck_traces()
            S['sweeps_enabled'] = pawn_sweeps()
            pts = [('deck %d' % i, [x, y, 3.85])
                   for i, (x, y) in enumerate(DECK_POINTS)]
            pts.append(('released under the deck',
                        [UNDER_DECK[0], UNDER_DECK[1], 2.5]))
            pts.append(('control: check-in floor',
                        [CONTROL_FLOOR[0], CONTROL_FLOOR[1], 0.9]))
            drop(pts)
            S.update(stage=3, stage_at=now + 3.5)
            save()
            return
        if stage == 3:
            S['drop_enabled'] = settle()
            set_stair(S['actors'][STAIR], False)
            S['restored'] = stair_state(S['actors'][STAIR])
            save('SUCCESS')
            print('DECK46 SUCCESS', flush=True)
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
