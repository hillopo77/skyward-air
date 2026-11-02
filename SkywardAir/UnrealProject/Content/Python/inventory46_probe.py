"""Pass46: dump every actor in the level, with the facts needed to judge it.

The whole-game audit. Read-only. One engine pass writes everything, so the
analysis that follows is offline and can be repeated and corrected without
re-running the engine - which is what went wrong in Pass45, where each wrong
judgment cost a fresh session.

Per actor: label, class, folder, mesh, triangles, material slots and what is
actually bound to them, world bounds, scale, mobility, collision, attachment.

Per prop-sized actor it also fires a 3x3 ray fan from each of the six bounding
faces, instead of Pass45's single ray from each face centre. That single ray is
why two ceiling-hung gate displays, supported by hangers 65 cm either side of
their centre, were reported as floating.
"""
import unreal as u, json, time, traceback

G = None
S = {}

PER_TICK = 60
INSET_CM = 3.0
TOLERANCE_CM = 14.0
FAN = (-0.62, 0.0, 0.62)        # fraction of the half-extent, so 9 rays per face
DIRS = [('down', 0, 0, -1), ('up', 0, 0, 1), ('east', 1, 0, 0),
        ('west', -1, 0, 0), ('north', 0, 1, 0), ('south', 0, -1, 0)]
# Carried or simulated items move at runtime; their resting place proves nothing.
SKIP_CONTAINS = ('Physical luggage', 'Security tray', 'Cafe cup', 'Coffee cup',
                 'CH12COLL ', 'AP Tow joint ')
PROP_MIN_CM = 4.0
PROP_MAX_CM = 900.0


def save(status='RUNNING', **kw):
    out = G.R / 'Pass46'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'Inventory46.json').write_text(json.dumps(dict(
        status=status,
        method=dict(inset_cm=INSET_CM, tolerance_cm=TOLERANCE_CM,
                    rays_per_face=len(FAN) ** 2,
                    rule='unsupported = no geometry within tolerance on ANY of '
                         '54 rays (3x3 fan from each of six bounding faces)'),
        counted=S.get('i', 0), total=len(S.get('actors', [])),
        traced=S.get('traced', 0), skipped=S.get('skipped', 0),
        actors=S.get('rows', []), unsupported=S.get('bad', []), **kw),
        indent=1), encoding='utf-8')


def stop(status, **kw):
    save(status, **kw)
    try:
        u.unregister_slate_post_tick_callback(S['handle'])
    except Exception:
        pass
    u.SystemLibrary.quit_game(G.P.STATE['world'], G.P.STATE['pc'],
                              u.QuitPreference.QUIT, False)


def mesh_facts(a):
    """Mesh, triangles, LODs and what is really bound to each material slot."""
    out = dict(mesh=None, triangles=None, lods=None, slots=[], missing_slots=0)
    try:
        c = a.static_mesh_component
    except Exception:
        return out
    if c is None:
        return out
    m = c.get_editor_property('static_mesh')
    if m is None:
        return out
    out['mesh'] = m.get_name()
    out['path'] = m.get_path_name().split('.')[0]
    try:
        out['lods'] = m.get_num_lods()
        out['triangles'] = u.EditorStaticMeshLibrary.get_number_triangles(m, 0)
    except Exception:
        pass
    try:
        n = c.get_num_materials()
        for i in range(n):
            mat = c.get_material(i)
            name = mat.get_name() if mat else None
            # an unassigned slot, or the editor's grey default, is a defect
            if name is None or name in ('WorldGridMaterial', 'DefaultMaterial',
                                        'BasicShapeMaterial'):
                out['missing_slots'] += 1
            out['slots'].append(name)
    except Exception:
        pass
    return out


def support(a, origin, extent, world):
    """54 rays. Returns the nearest contact per direction, cm, or None."""
    dists = {}
    for name, dx, dy, dz in DIRS:
        e = extent.x if dx else (extent.y if dy else extent.z)
        best = None
        # the two axes that span the face
        span = [(extent.x, 1, 0, 0), (extent.y, 0, 1, 0), (extent.z, 0, 0, 1)]
        span = [q for q in span if not (q[1] * abs(dx) or q[2] * abs(dy) or q[3] * abs(dz))]
        for fa in FAN:
            for fb in FAN:
                ox = span[0][1] * fa * span[0][0] + span[1][1] * fb * span[1][0]
                oy = span[0][2] * fa * span[0][0] + span[1][2] * fb * span[1][0]
                oz = span[0][3] * fa * span[0][0] + span[1][3] * fb * span[1][0]
                sx = origin.x + dx * (e - INSET_CM) + ox
                sy = origin.y + dy * (e - INSET_CM) + oy
                sz = origin.z + dz * (e - INSET_CM) + oz
                tx = origin.x + dx * (e + TOLERANCE_CM) + ox
                ty = origin.y + dy * (e + TOLERANCE_CM) + oy
                tz = origin.z + dz * (e + TOLERANCE_CM) + oz
                hit = u.SystemLibrary.line_trace_single(
                    world, u.Vector(sx, sy, sz), u.Vector(tx, ty, tz),
                    u.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [a],
                    u.DrawDebugTrace.NONE, True)
                if hit:
                    t = hit.to_tuple()
                    if t[0]:
                        d = round(float(t[2]) - INSET_CM, 2)
                        if best is None or d < best:
                            best = d
        dists[name] = best
    return dists


def tick(dt):
    try:
        if time.monotonic() < S['next']:
            return
        world = G.P.STATE['world']
        n = 0
        while S['i'] < len(S['actors']) and n < PER_TICK:
            a = S['actors'][S['i']]
            S['i'] += 1
            n += 1
            if not u.SystemLibrary.is_valid(a):
                continue
            label = a.get_actor_label()
            try:
                origin, extent = a.get_actor_bounds(False)
                loc = a.get_actor_location()
                rot = a.get_actor_rotation()
                sc = a.get_actor_scale3d()
            except Exception:
                S['skipped'] += 1
                continue

            row = dict(
                actor=label, cls=a.get_class().get_name(),
                folder=str(a.get_folder_path()),
                loc_m=[round(loc.x / 100.0, 3), round(-loc.y / 100.0, 3),
                       round(loc.z / 100.0, 3)],
                yaw=round(rot.yaw, 2), pitch=round(rot.pitch, 2),
                roll=round(rot.roll, 2),
                scale=[round(sc.x, 4), round(sc.y, 4), round(sc.z, 4)],
                centre_m=[round(origin.x / 100.0, 3), round(-origin.y / 100.0, 3),
                          round(origin.z / 100.0, 3)],
                extent_cm=[round(extent.x, 1), round(extent.y, 1), round(extent.z, 1)])
            row.update(mesh_facts(a))
            try:
                c = a.static_mesh_component
                row['mobility'] = str(c.get_editor_property('mobility'))
                row['collision_enabled'] = str(c.get_collision_enabled())
                row['collision_profile'] = str(c.get_collision_profile_name())
                row['simulating'] = bool(c.is_simulating_physics())
                row['visible'] = bool(c.is_visible())
                row['casts_shadow'] = bool(c.get_editor_property('cast_shadow'))
            except Exception:
                pass
            p = a.get_attach_parent_actor()
            row['parent'] = p.get_actor_label() if p else None

            biggest = max(extent.x, extent.y, extent.z)
            if (biggest >= PROP_MIN_CM and biggest <= PROP_MAX_CM
                    and not any(k in label for k in SKIP_CONTAINS)
                    and not row.get('simulating')):
                d = support(a, origin, extent, world)
                row['support_cm'] = d
                S['traced'] += 1
                if not any(v is not None for v in d.values()):
                    S['bad'].append(dict(actor=label, mesh=row.get('mesh'),
                                         centre_m=row['centre_m'],
                                         extent_cm=row['extent_cm'],
                                         parent=row['parent']))
            S['rows'].append(row)

        if S['i'] % 600 < PER_TICK:
            save()
        if S['i'] >= len(S['actors']):
            stop('SUCCESS', finished=time.time())
    except Exception:
        stop('ERROR', error=traceback.format_exc())


def start(game):
    global G
    G = game
    try:
        G.CAPTURE = True
        G.QA = True
        actors = list(u.GameplayStatics.get_all_actors_of_class(
            G.P.STATE['world'], u.Actor))
        S.update(actors=actors, i=0, traced=0, skipped=0, rows=[], bad=[],
                 next=time.monotonic() + 2.0, started=time.time())
        S['handle'] = u.register_slate_post_tick_callback(tick)
        save()
    except Exception:
        S.setdefault('actors', [])
        stop('ERROR', error=traceback.format_exc())
