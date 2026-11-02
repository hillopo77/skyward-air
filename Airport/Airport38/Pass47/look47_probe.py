"""Pass47 experiments in the running game. Nothing is saved.

  panel    The landside corridor shows a large flat black rectangle on its south
           wall that reads as a dead screen. Traces along that wall at eye and
           head height name what it is.

  ceiling  Every interior ceiling reads mid-grey (0.37-0.48 in the stills)
           because every fixture points down and this renderer has no bounce
           light. The ceiling material, MI_AP_P43TCeiling, already exposes an
           Emission scalar (0 today). Editing that asset in a running game
           trips an editor-only assertion (first attempt crashed), so this
           gives the ceiling union a dynamic instance of it, sets Emission on
           that per trial, and photographs the same three rooms.
"""
import unreal as u, json, time, hashlib, traceback

G = None
S = {}
MI = '/Game/Airport38/Materials/MI_AP_P43TCeiling'
TRIALS = [5.0, 15.0, 40.0]   # 0..0.7 moved the ceiling by under 0.01 (first trial)
VIEWS = [('checkin', [-42.3, -15, 1.62], [-27, -12, 1.7]),
         ('concourse', [-29, -3.3, 1.62], [-29, 13.5, 1.8]),
         ('corridor', [-27, -20, 1.62], [-48, -20, 1.7])]


def save(status='RUNNING', **kw):
    (G.R / 'Pass47' / 'Look47.json').write_text(json.dumps(dict(
        status=status, panel=S.get('panel'), shots=S.get('shots', []), **kw), indent=1),
        encoding='utf-8')


def finish(status, **kw):
    save(status, **kw)
    u.unregister_slate_post_tick_callback(S['handle'])
    u.SystemLibrary.quit_game(G.P.STATE['world'], G.P.STATE['pc'], u.QuitPreference.QUIT, False)


def ceiling_mids():
    """Dynamic instances on every ceiling-union slot that uses the ceiling MI."""
    mi = u.load_asset(MI)
    out = []
    for a in u.GameplayStatics.get_all_actors_of_class(G.P.STATE['world'], u.StaticMeshActor):
        if a.get_actor_label() != 'Airport38 coherent ceiling union':
            continue
        c = a.static_mesh_component
        for i in range(c.get_num_materials()):
            m = c.get_material(i)
            if m and m.get_name() == mi.get_name():
                out.append(c.create_dynamic_material_instance(i, mi))
    return out


def panel():
    rows = []
    for i in range(0, 41):
        x = -48.0 + i * 0.5
        for z in (1.4, 2.1):
            hit = u.SystemLibrary.line_trace_single(
                G.P.STATE['world'], G.v([x, -6.0, z]), G.v([x, -9.5, z]),
                u.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [G.P.STATE['pawn']],
                u.DrawDebugTrace.NONE, True)
            t = hit.to_tuple() if hit else None
            if t and t[0]:
                comp = t[10]
                mat = None
                try:
                    mat = comp.get_material(0).get_name()
                except Exception:
                    pass
                rows.append(dict(x=x, z=z, y_hit=round(G.source(t[5])[1], 3),
                                 actor=t[9].get_actor_label() if t[9] else None,
                                 component=comp.get_name() if comp else None,
                                 face_material=mat, element=t[14] if len(t) > 14 else None))
    # Summarise runs of the same actor along the wall.
    runs, prev = [], None
    for r in rows:
        if r['z'] != 1.4:
            continue
        key = (r['actor'], r['y_hit'])
        if key != prev:
            runs.append(dict(from_x=r['x'], actor=r['actor'], y_hit=r['y_hit'], material=r['face_material']))
            prev = key
        runs[-1]['to_x'] = r['x']
    return dict(rows=rows, runs=runs)


def tick(dt):
    try:
        now = time.monotonic()
        if now < S['next']:
            return
        if S.get('mids') is None:
            S['mids'] = ceiling_mids()
            S['panel'] = dict(note='measured in the first run; see Look47_first.json', mids=len(S['mids']))
            save()
        if S.get('wait'):
            p = S['wait']
            if p.exists() and p.stat().st_mtime >= S['requested']:
                S['shots'].append(dict(emission=S['e'], view=S['view'], file=str(p)))
                S.pop('wait')
                S['k'] += 1
                save()
            elif now - S['req_mono'] > 25:
                raise RuntimeError('frame timeout')
            return
        jobs = [(e, v) for e in TRIALS for v in VIEWS]
        if S['k'] >= len(jobs):
            finish('SUCCESS')
            return
        e, (name, eye, target) = jobs[S['k']]
        if S.get('posed') != S['k']:
            for mid in S['mids']:
                mid.set_scalar_parameter_value('Emission', e)
            cam = S['cam']
            cam.set_actor_location(G.v(eye), False, True)
            cam.set_actor_rotation(u.MathLibrary.find_look_at_rotation(G.v(eye), G.v(target)), False)
            S.update(posed=S['k'], e=e, view=name, next=now + 1.6)
            return
        p = G.R / 'Pass47' / 'Look' / ('ceiling_%s_e%03d.png' % (name, int(e * 10)))
        S.update(wait=p, requested=time.time(), req_mono=now, next=now + .4)
        u.SystemLibrary.execute_console_command(G.P.STATE['world'], 'Shot -nosuffix filename="' + p.as_posix() + '"', G.P.STATE['pc'])
    except Exception:
        finish('ERROR', error=traceback.format_exc())


def start(game):
    global G
    G = game
    S.update(shots=[], k=0, panel=None, mids=None)
    (G.R / 'Pass47' / 'Look').mkdir(parents=True, exist_ok=True)
    G.CAPTURE = True
    cam = next(iter(G.S['cameras'].values()))
    cam.camera_component.set_field_of_view(84)
    G.P.STATE['pc'].set_view_target_with_blend(cam, 0)
    S.update(cam=cam, next=time.monotonic() + 3.0)
    S['handle'] = u.register_slate_post_tick_callback(tick)
    save()
