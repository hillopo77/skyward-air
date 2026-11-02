"""Pass46 / P46-017 acceptance: does a real physics body now rest on the deck?

deck46_probe could not spawn a test cube - this engine build exposes no
deferred spawn to Python - so this uses a physics body the level already has:
`Physical luggage 06`, an 8 kg simulated bag parked on the ground floor near
the gallery and used by no journey step (the journey uses 01 and 02).

The bag is lifted to 0.65 m above three deck points in turn and released, plus
a control drop onto the cafe floor under the deck. After each settle its height
and what is under it are recorded. Its original transform is restored at the
end. Nothing is saved; the bag's displacement exists only in this session.
"""
import unreal as u, json, time, traceback

G = None
S = {}
BAG = 'Physical luggage 06'
DROPS = [('deck west', -46.0, 30.5, 3.80), ('deck east', -42.2, 32.6, 3.80),
         ('deck stair head', -46.4, 26.2, 3.80),
         ('control: cafe floor under the deck', -45.0, 29.5, 0.80)]
SETTLE_S = 3.0


def save(status='RUNNING', **extra):
    out = dict(status=status, results=S.get('results', []),
               control=S.get('control'), deck_traces=S.get('deck_traces'))
    out.update(extra)
    (G.R / 'Pass46' / 'Drop46.json').write_text(json.dumps(out, indent=1),
                                                 encoding='utf-8')


def down(x, y, z, ignore):
    hit = u.SystemLibrary.line_trace_single(
        G.P.STATE['world'], G.v([x, y, z]), G.v([x, y, -1.0]),
        u.TraceTypeQuery.TRACE_TYPE_QUERY1, False,
        [G.P.STATE['pawn']] + ignore, u.DrawDebugTrace.NONE, True)
    t = hit.to_tuple() if hit else None
    if not t or not t[0]:
        return None, None
    lbl = None
    for i in (9, 10):
        try:
            lbl = t[i].get_actor_label()
            break
        except Exception:
            try:
                lbl = t[i].get_owner().get_actor_label()
                break
            except Exception:
                continue
    return lbl, round(G.source(t[5])[2], 3)


def release(bag, x, y, z):
    c = bag.static_mesh_component
    c.set_simulate_physics(False)
    bag.set_actor_location_and_rotation(G.v([x, y, z]), u.Rotator(0, 0, 0),
                                        False, True)
    c.set_simulate_physics(True)
    c.wake_all_rigid_bodies()


def tick(dt):
    try:
        now = time.monotonic()
        if now - S['start'] < 3.0 or now < S.get('next', 0):
            return
        if 'bag' not in S:
            bag = next((a for a in u.GameplayStatics.get_all_actors_of_class(
                G.P.STATE['world'], u.StaticMeshActor)
                if a.get_actor_label() == BAG), None)
            if bag is None:
                save('ABORTED', error=BAG + ' not in the level')
                u.unregister_slate_post_tick_callback(S['handle'])
                return
            S['bag'] = bag
            S['home'] = (bag.get_actor_location(), bag.get_actor_rotation(),
                         bag.static_mesh_component.is_simulating_physics())
            lbl, z = down(-42.0, -13.0, 1.4, [])
            S['control'] = dict(floor=lbl, z=z, passed=lbl is not None)
            S['deck_traces'] = [dict(at=[x, y], hit=down(x, y, 5.0, [bag]))
                                for _, x, y, _ in DROPS[:3]]
            S['results'] = []
            S['i'] = 0
            name, x, y, z = DROPS[0]
            release(bag, x, y, z)
            S['next'] = now + SETTLE_S
            save()
            return
        bag = S['bag']
        name, x, y, z = DROPS[S['i']]
        p = G.source(bag.static_mesh_component.get_center_of_mass())
        on, support = down(p[0], p[1], p[2] + 0.4, [bag])
        S['results'].append(dict(
            drop=name, released=[x, y, z], rest_com=[round(v, 3) for v in p],
            fell_m=round(z - p[2], 3), resting_on=on, support_z=support,
            speed_cm_s=round(bag.static_mesh_component
                             .get_physics_linear_velocity().length(), 1)))
        S['i'] += 1
        if S['i'] < len(DROPS):
            name, x, y, z = DROPS[S['i']]
            release(bag, x, y, z)
            S['next'] = now + SETTLE_S
            save()
            return
        loc, rot, sim = S['home']
        bag.static_mesh_component.set_simulate_physics(False)
        bag.set_actor_location_and_rotation(loc, rot, False, True)
        bag.static_mesh_component.set_simulate_physics(sim)
        save('SUCCESS')
        print('DROP46 SUCCESS', flush=True)
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
