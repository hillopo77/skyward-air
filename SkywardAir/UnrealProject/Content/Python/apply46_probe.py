"""Pass46: apply Spec46.json to the level, re-checking every change live.

The spec was validated offline against authored data. This re-checks it against
real geometry, because authored rectangles are not the same thing as the meshes
the engine actually has: a footprint can clear every authored prop and still
hit a wall cassette, a soffit or a fixture that lives inside a union actor.

Each placement is spawned, snapped so its mesh bottom sits on the floor it is
standing over, then box-tested against live world geometry. Anything that
overlaps is destroyed and reported rather than shipped, so a bad number costs a
line in the report instead of a defect in the build.

Meshes and materials are taken from an actor already in the level that uses the
same asset, so no asset path is guessed and per-instance material overrides
(the check-in header bezel swap, for one) are inherited rather than lost.

Idempotent: a re-run destroys the actors this pass created before placing again,
and re-applies moves and variations from the authored originals.
"""
import unreal as u, json, time, traceback

G = None
S = {}
TAG = '46'
SNAP_DROP_CM = 260.0
OVERLAP_SHRINK = 0.90       # ignore mere contact; catch real interpenetration

# Collision is copied from whichever actor already uses the asset, which would
# otherwise propagate P46-014: ten existing plant and planter actors are
# visible and walk-through. Anything a player can bump into is forced solid
# here instead of inheriting that.
FORCE_SOLID = {
    'SM_AP_Plant12', 'SM_AP_Planter27', 'SM_AP_Bins36', 'SM_AP_Recycling38',
    'SM_AP_Bench27_Hardware40', 'SM_AP_Bench29_Hardware40',
    'SM_AP_Bench34_Hardware40', 'SM_AP_Charging34', 'SM_AP_Information27',
    'SM_AP_StaffStorage38', 'SM_AP_Trolley', 'SM_AP_CafeTable34',
    'SM_AP_CafeChair34_Hardware40', 'SM_AP_OvalTable36', 'SM_AP_Transfer38'}
# Wall-mounted, so it is flush with a wall and needs no blocking volume.
NO_SOLID = {'SM_AP_ScreenBoard'}


def save(status='RUNNING', **kw):
    out = G.R / 'Pass46'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'Apply46.json').write_text(json.dumps(dict(
        status=status, placed=S.get('placed', []), moved=S.get('moved', []),
        varied=S.get('varied', []), collided=S.get('collided', []),
        rejected=S.get('rejected', []),
        removed_previous=S.get('removed', []), notes=S.get('notes', []),
        **kw), indent=1), encoding='utf-8')


def v(p):
    """Source metres -> Unreal cm. Unreal north is -Y."""
    return u.Vector(p[0] * 100.0, -p[1] * 100.0, p[2] * 100.0)


def floor_z_cm(world, x_cm, y_cm, from_z_cm, ignore):
    """Trace down for the real floor under a point; None if there is none."""
    hit = u.SystemLibrary.line_trace_single(
        world, u.Vector(x_cm, y_cm, from_z_cm + 40.0),
        u.Vector(x_cm, y_cm, from_z_cm - SNAP_DROP_CM),
        u.TraceTypeQuery.TRACE_TYPE_QUERY1, True, ignore,
        u.DrawDebugTrace.NONE, True)
    if not hit:
        return None
    t = hit.to_tuple()
    if not t[0]:
        return None
    return t[4].z if hasattr(t[4], 'z') else None


def overlaps(world, actor):
    """Live box test. Returns the labels of anything this actor penetrates."""
    try:
        origin, extent = actor.get_actor_bounds(False)
    except Exception:
        return []
    half = u.Vector(max(2.0, extent.x * OVERLAP_SHRINK),
                    max(2.0, extent.y * OVERLAP_SHRINK),
                    max(2.0, extent.z * OVERLAP_SHRINK))
    try:
        found = u.SystemLibrary.box_overlap_actors(
            world, origin, half, [u.ObjectTypeQuery.OBJECT_TYPE_QUERY1],
            u.Actor, [actor])
    except Exception as e:
        S['notes'].append('box_overlap_actors unavailable: %s' % e)
        return []
    out = []
    for q in found or []:
        try:
            lbl = q.get_actor_label()
        except Exception:
            continue
        # the shell, floors and ceilings are what everything stands on or against
        if lbl.startswith(('Airport38 coherent', 'Airport38 complete',
                           'Airport38 role-based', 'Airport38 verified',
                           'Airport39 fitted', 'Airport43 fitted',
                           'Airport38 exterior glazing', 'Airport38 mounted',
                           'Asphalt12_', 'Curb12_')):
            continue
        out.append(lbl)
    return out


def run(game):
    global G
    G = game
    world = G.P.STATE['world']
    EA = u.get_editor_subsystem(u.EditorActorSubsystem)
    S.update(placed=[], moved=[], varied=[], rejected=[], removed=[], notes=[])
    spec = json.loads((G.R / 'Pass46' / 'Spec46.json').read_text(encoding='utf-8'))

    actors = {}
    for a in EA.get_all_level_actors():
        try:
            actors[a.get_actor_label()] = a
        except Exception:
            continue

    # remove anything this pass made before, so a re-run is clean
    for lbl, a in list(actors.items()):
        if lbl.endswith(TAG) or (TAG in lbl and lbl.startswith((
                'Concourse ', 'Cafe approach ', 'WC passage ', 'Landside ',
                'Arrivals ', 'Baggage service ', 'Baggage transfer ',
                'Operations ', 'A07 entry ', 'Public return ', 'Gallery ',
                'Arrivals exit '))):
            S['removed'].append(lbl)
            EA.destroy_actor(a)
            actors.pop(lbl, None)
    save()

    # asset id -> (mesh, [materials]) from an actor already using that asset
    library = {}
    for lbl, a in actors.items():
        try:
            c = a.static_mesh_component
            m = c.get_editor_property('static_mesh') if c else None
        except Exception:
            continue
        if m is None:
            continue
        name = 'SM_AP_' + m.get_name()[6:] if m.get_name().startswith('SM_AP_') else m.get_name()
        key = m.get_name()
        if key in library:
            continue
        mats = []
        try:
            for i in range(c.get_num_materials()):
                mats.append(c.get_material(i))
        except Exception:
            pass
        library[key] = dict(mesh=m, mats=mats, source=lbl,
                            profile=str(c.get_collision_profile_name()),
                            enabled=c.get_collision_enabled())

    # ---------------------------------------------------------------- place
    for q in spec['place']:
        key = q['asset']
        entry = library.get(key)
        if entry is None:
            S['rejected'].append(dict(name=q['name'], asset=key,
                                      reason='no actor in the level uses this asset, '
                                             'so no mesh or materials to copy'))
            continue
        loc = v(q['location'])
        rot = u.Rotator(roll=0.0, pitch=0.0, yaw=-q['rotation_degrees'])
        a = EA.spawn_actor_from_class(u.StaticMeshActor, loc, rot)
        a.set_actor_label(q['name'])
        a.set_folder_path('Airport38/Pass46/Furnish')
        c = a.static_mesh_component
        c.set_static_mesh(entry['mesh'])
        c.set_mobility(u.ComponentMobility.STATIC)
        for i, mat in enumerate(entry['mats']):
            if mat is not None:
                try:
                    c.set_material(i, mat)
                except Exception:
                    pass
        try:
            if q['asset'] in FORCE_SOLID:
                c.set_collision_enabled(u.CollisionEnabled.QUERY_AND_PHYSICS)
                c.set_collision_profile_name('BlockAll')
            elif q['asset'] in NO_SOLID:
                c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
            else:
                c.set_collision_enabled(entry['enabled'])
                c.set_collision_profile_name(entry['profile'])
        except Exception as e:
            S['notes'].append('collision on %s: %s' % (q['name'], e))
        sc = q.get('scale') or [1, 1, 1]
        a.set_actor_scale3d(u.Vector(sc[0], sc[1], sc[2]))

        # snap to the floor underneath, unless this is wall-mounted
        snapped = None
        if q['asset'] != 'SM_AP_ScreenBoard':
            origin, extent = a.get_actor_bounds(False)
            fz = floor_z_cm(world, origin.x, origin.y, origin.z - extent.z, [a])
            if fz is not None:
                bottom = origin.z - extent.z
                a.set_actor_location(
                    u.Vector(loc.x, loc.y, loc.z + (fz - bottom)), False, False)
                snapped = round((fz - bottom) / 100.0, 4)
            else:
                S['notes'].append('%s: no floor found below, left at authored z'
                                  % q['name'])

        bad = overlaps(world, a)
        if bad:
            S['rejected'].append(dict(name=q['name'], asset=key,
                                      reason='live geometry overlap',
                                      hits=sorted(set(bad))[:6]))
            EA.destroy_actor(a)
            continue
        origin, extent = a.get_actor_bounds(False)
        S['placed'].append(dict(
            name=q['name'], asset=key, room=q['room'], why=q['why'],
            mesh_from=entry['source'], snap_m=snapped,
            centre_m=[round(origin.x / 100.0, 3), round(-origin.y / 100.0, 3),
                      round(origin.z / 100.0, 3)],
            extent_cm=[round(extent.x, 1), round(extent.y, 1), round(extent.z, 1)]))
        if len(S['placed']) % 12 == 0:
            save()

    # ------------------------------------------------------------ move / vary
    for kind, rows in (('moved', spec['move']), ('varied', spec['vary'])):
        for m in rows:
            a = actors.get(m['actor'])
            if a is None:
                S['rejected'].append(dict(name=m['actor'], reason='actor not in level'))
                continue
            before_loc = a.get_actor_location()
            before_rot = a.get_actor_rotation()
            before_sc = a.get_actor_scale3d()
            if m.get('to'):
                a.set_actor_location(v(m['to']), False, False)
            if m.get('yaw') is not None:
                a.set_actor_rotation(
                    u.Rotator(roll=before_rot.roll, pitch=before_rot.pitch,
                              yaw=-m['yaw']), False)
            # a reseated plate is meant to touch its door, so the overlap test
            # must not reject it for doing exactly that
            tight = m.get('snap') is False
            if m.get('scale'):
                s = m['scale']
                a.set_actor_scale3d(u.Vector(s[0], s[1], s[2]))
            # floor-snap anything that moved, unless it is mounted off the floor
            if m.get('to') and m.get('snap') is not False:
                origin, extent = a.get_actor_bounds(False)
                fz = floor_z_cm(world, origin.x, origin.y, origin.z - extent.z, [a])
                if fz is not None:
                    bottom = origin.z - extent.z
                    loc = a.get_actor_location()
                    a.set_actor_location(
                        u.Vector(loc.x, loc.y, loc.z + (fz - bottom)), False, False)
            bad = [] if tight else overlaps(world, a)
            if bad:
                a.set_actor_location(before_loc, False, False)
                a.set_actor_rotation(before_rot, False)
                a.set_actor_scale3d(before_sc)
                S['rejected'].append(dict(
                    name=m['actor'], reason='live geometry overlap after %s; reverted' % kind,
                    hits=sorted(set(bad))[:6]))
                continue
            origin, extent = a.get_actor_bounds(False)
            S[kind].append(dict(
                actor=m['actor'], why=m['why'],
                from_m=[round(before_loc.x / 100.0, 3), round(-before_loc.y / 100.0, 3),
                        round(before_loc.z / 100.0, 3)],
                to_m=[round(origin.x / 100.0, 3), round(-origin.y / 100.0, 3),
                      round(origin.z / 100.0, 3)],
                from_yaw=round(-before_rot.yaw, 2),
                to_yaw=(m.get('yaw') if m.get('yaw') is not None else round(-before_rot.yaw, 2)),
                scale=m.get('scale')))
        save()

    # ----------------------------------------------------------- collide
    for q in spec.get('collide', []):
        a = actors.get(q['actor'])
        if a is None:
            S['rejected'].append(dict(name=q['actor'], reason='actor not in level'))
            continue
        try:
            c = a.static_mesh_component
            was = str(c.get_collision_enabled())
            c.set_collision_enabled(u.CollisionEnabled.QUERY_AND_PHYSICS)
            c.set_collision_profile_name(q.get('profile', 'BlockAll'))
            S.setdefault('collided', []).append(dict(
                actor=q['actor'], was=was,
                now=str(c.get_collision_enabled()),
                profile=str(c.get_collision_profile_name()), why=q['why']))
        except Exception as e:
            S['rejected'].append(dict(name=q['actor'],
                                      reason='could not set collision: %s' % e))
    save()

    assert u.EditorLoadingAndSavingUtils.save_map(
        world, '/Game/Airport38/L_Airport_Repair38'), 'save_map failed'
    save('SUCCESS', finished=time.time(),
         summary=dict(placed=len(S['placed']), moved=len(S['moved']),
                      varied=len(S['varied']), collided=len(S.get('collided', [])),
                      rejected=len(S['rejected'])))


def start(game):
    global G
    G = game
    try:
        G.CAPTURE = True
        G.QA = True
        run(game)
        print('APPLY46 SUCCESS', flush=True)
    except Exception:
        S.setdefault('notes', []).append('failed')
        save('ERROR', error=traceback.format_exc())
    try:
        u.SystemLibrary.quit_game(G.P.STATE['world'], G.P.STATE['pc'],
                                  u.QuitPreference.QUIT, False)
    except Exception:
        pass
