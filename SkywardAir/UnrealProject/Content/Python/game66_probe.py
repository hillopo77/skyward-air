"""Pass66: drive the Gameplay66 mechanics in -game and photograph them from the player's own eyes (read-only).

Run: Run-GameProbe48.ps1 -Flag P48_game66_probe -Probe game66_probe.py -Report Game66.json
The '-P48_game66' flag switches Gameplay66 on inside this automated run. Keys
are pressed through gameplay66.VIRTUAL; walking uses add_movement_input.
Scenes (Pass48/Game66Scenes.json overrides): A08 terrace hop, tier climb,
knee block, sprint slide, tether grab/swing/throw, equip and use, sit
anywhere. Each records numbers (feet height over time, speeds, what was
grabbed, where it went) and screenshots to Pass48/Look/G66. Nothing is saved.
"""
import unreal as u, json, math, time, traceback

G = None
M = None
S = dict(steps=[], i=0, t0=0.0, shots=[], log={}, wait=None)
OUT = 'Look/G66'


def pc():
    return G.P.STATE['pc']


def pawn():
    return G.P.STATE['pawn']


def feet():
    return round(pawn().get_actor_location().z / 100 - G.P.EYE_HEIGHT - M.GS['bob'], 3)


def place(x, y, yaw, pitch=-5.0):
    """Stand the player on the floor at source (x, y), facing yaw (UE degrees)."""
    if G.P.STATE.get('seated'):
        G.P.stand()
    nav, _ = G.P.floor_at_source(x, y, 0.0)
    nav = 0.0 if nav is None else nav
    pawn().set_actor_location(G.v([x, y, nav + G.P.EYE_HEIGHT]), False, True)
    pc().set_control_rotation(u.Rotator(pitch=pitch, yaw=yaw, roll=0))
    M.GS.update(air=False, surface=None, base=None, vz=0.0, prev=None, slide=0.0)
    M.VIRTUAL['down'].clear()


def look_at(target):
    loc = pawn().get_actor_location()
    r = u.MathLibrary.find_look_at_rotation(loc, target)
    pc().set_control_rotation(u.Rotator(pitch=r.pitch, yaw=r.yaw, roll=0))


def walk(yaw, amount=1.0):
    pawn().add_movement_input(u.MathLibrary.get_forward_vector(u.Rotator(yaw=yaw)), amount)


def press(*keys):
    M.VIRTUAL['pressed'].update(keys)


def shot(name):
    p = G.R / 'Pass48' / OUT / (name + '.png')
    S['shots'].append(name)
    u.SystemLibrary.execute_console_command(G.P.STATE['world'], 'Shot -nosuffix filename="' + p.as_posix() + '"', pc())


def rec(key, value):
    S['log'].setdefault(key, []).append(value)


# ---------------------------------------------------------------- scenes
# each step: (duration_s, fn(t, first)) ; fn runs every tick of the step

def hop_terrace():
    st = {}

    def setup(t, first):
        if first:
            place(-28.2, 26.75, 180.0, -12)
    def run_jump(t, first):
        walk(180.0)
        if first:
            press('SpaceBar')
        rec('hop_feet', [round(t, 3), feet(), M.GS['air'], M.GS['surface']])
        if 0.28 < t and not st.get('mid'):
            st['mid'] = 1; shot('G66_hop_mid')
    def settle(t, first):
        if first:
            rec('hop_landed', dict(feet=feet(), surface=M.GS['surface'], landings=M.GS['landings'],
                                   x=round(pawn().get_actor_location().x / 100, 2)))
        if t > .6 and not st.get('land'):
            st['land'] = 1; shot('G66_hop_landed')
    def climb(t, first):
        walk(180.0)
        if first or (not M.GS['air'] and t > .2 and int(t * 2) != st.get('k')):
            st['k'] = int(t * 2); press('SpaceBar')
        rec('climb_feet', [round(t, 3), feet(), M.GS['air'], M.GS['surface']])
    def top(t, first):
        if first:
            rec('climb_top', dict(feet=feet(), surface=M.GS['surface'], x=round(pawn().get_actor_location().x / 100, 2)))
            pc().set_control_rotation(u.Rotator(pitch=-14, yaw=20.0, roll=0))
        if t > .8 and not st.get('top'):
            st['top'] = 1; shot('G66_terrace_top')
    def walk_off(t, first):
        walk(0.0)
        rec('off_feet', [round(t, 3), feet(), M.GS['air'], M.GS['surface']])
    return [(1.0, setup), (1.1, run_jump), (1.2, settle), (2.6, climb), (1.2, top), (2.2, walk_off)]


def knee_block():
    def setup(t, first):
        if first:
            place(-28.2, 28.2, 180.0, -10)
    def push(t, first):
        walk(180.0)
        rec('knee', [round(t, 3), round(pawn().get_actor_location().x / 100, 3), feet()])
    def done(t, first):
        if first:
            rec('knee_end', dict(x=round(pawn().get_actor_location().x / 100, 3), feet=feet()))
            shot('G66_knee_block')
    return [(.8, setup), (1.8, push), (.6, done)]


def slide():
    st = {}

    def setup(t, first):
        if first:
            place(-28.5, -1.0, -90.0, -6)         # concourse, sliding toward gate A08
            M.VIRTUAL['down'].update({'LeftShift', 'W'})
    def run(t, first):
        walk(-90.0)
        if abs(t - 1.0) < .02 and not st.get('go'):
            st['go'] = 1; press('LeftControl')
        v = pawn().get_velocity()
        mv = pawn().get_component_by_class(u.FloatingPawnMovement); p = pawn().get_actor_location()
        cm = pc().player_camera_manager.get_camera_rotation()
        rec('slide', [round(t, 3), round(math.hypot(v.x, v.y)), round(M.GS['fov'], 1), round(M.GS['bob'], 3), round(M.GS['slide'], 2),
                      round(mv.get_editor_property('max_speed')), round(-p.y / 100, 3),
                      round(M.HEAD['pitch_sent'], 2), round(cm.roll, 2), round(M.HEAD['sprint'], 2), round(M.HEAD['effort'], 2)])
        if 1.15 < t and not st.get('s'):
            st['s'] = 1; shot('G66_slide')
    def stop(t, first):
        if first:
            M.VIRTUAL['down'].clear()
    return [(.6, setup), (2.2, run), (.8, stop)]


def sees(a, o):
    """Does a straight line from the (just placed) eye reach actor a first?"""
    eye = pawn().get_actor_location()
    h = M.trace(eye, eye + (o - eye) * 1.1, M.carried())
    return bool(h and h[9] == a)


def pick_target(cx, cy, r=6.0):
    """Nearest grabbable thing around (cx, cy) the player can stand 1.4 m from and see."""
    world = G.P.STATE['world']
    found = []
    for a in u.GameplayStatics.get_all_actors_of_class(world, u.StaticMeshActor):
        p = a.get_actor_location()
        if (p.x / 100 - cx) ** 2 + (-p.y / 100 - cy) ** 2 > r * r:
            continue
        if M.grabbable(a):
            o, e = a.get_actor_bounds(False)
            found.append((((p.x / 100 - cx) ** 2 + (-p.y / 100 - cy) ** 2), a, o, e))
    found.sort(key=lambda q: q[0])
    return found


def tether():
    st = {}

    def setup(t, first):
        if not first:
            return
        cands = [c for spot in S['spots'] for c in pick_target(*spot)]
        cands.sort(key=lambda q: (not q[1].get_actor_label().startswith('Airport66 '), 'hammer' in q[1].get_actor_label()))
        rec('grab_candidates', [[q[1].get_actor_label(), round(q[0] ** .5, 2), round(max(q[3].x, q[3].y, q[3].z) * 2)] for q in cands[:60]])
        for d2, a, o, e in cands:
            if max(e.x, e.y, e.z) * 2 > 120 or o.z > 160:
                continue
            for ang in range(0, 360, 45):
                x = o.x / 100 + 1.5 * math.cos(math.radians(ang)); y = -o.y / 100 - 1.5 * math.sin(math.radians(ang))
                place(x, y, 0.0)
                look_at(o)
                if sees(a, o):
                    st['a'] = a; st['o'] = o; S['grabbed'] = a
                    rec('grab_target', dict(label=a.get_actor_label(), mesh=a.static_mesh_component.static_mesh.get_name(),
                                            size=round(max(e.x, e.y, e.z) * 2), from_=[round(x, 2), round(y, 2)]))
                    return
        rec('grab_target', None)
    def grab(t, first):
        if 'a' not in st:
            return
        M.VIRTUAL['down'].add('LeftMouseButton')
        if first:
            press('LeftMouseButton')
            h = M.aimed()                                                  # why a grab would be refused
            an, pn = G.nearest(), G.P.nearest()
            rec('grab_why', dict(aimed=h[9].get_actor_label() if h and h[9] else None, dist=round(h[3]) if h else None,
                                 grabbable=bool(h and h[9] and M.grabbable(h[9])), airport_held=G.S.get('held'),
                                 near_airport=(an.get('title') if isinstance(an, dict) else str(an)) if an else None,
                                 near_skyward=(pn.get('title') if isinstance(pn, dict) else str(pn)) if pn else None,
                                 seated=bool(G.P.STATE.get('seated'))))
        if t > 1.0 and not st.get('s1'):
            st['s1'] = 1; shot('G66_grab_hold')
            rec('grab_hold', dict(held=bool(M.GS['held']), sim=st['a'].static_mesh_component.is_simulating_physics(),
                                  rise=round((st['a'].get_actor_location().z - st['o'].z) / 100, 2)))
    def swing(t, first):
        if 'a' not in st:
            return
        r = pc().get_control_rotation()
        pc().set_control_rotation(u.Rotator(pitch=r.pitch, yaw=r.yaw + 140 * (1 / 60.0) * 2, roll=0))
        if t > .35 and not st.get('s2'):
            st['s2'] = 1; shot('G66_grab_swing')
    def throw(t, first):
        if 'a' not in st:
            return
        if first:                                                      # hold Right Mouse 0.9 s to wind up, then let go
            p = st['a'].get_actor_location(); st['p0'] = p
            press('RightMouseButton'); M.VIRTUAL['down'].add('RightMouseButton')
        if .6 < t and not st.get('w'):
            st['w'] = 1; shot('G66_windup'); rec('windup', dict(charge=M.GS.get('charge'), pitch=round(M.HEAD['pitch_sent'], 2)))
        if t > .9:
            M.VIRTUAL['down'].discard('RightMouseButton')
        if t > 1.15 and not st.get('v'):
            st['v'] = 1; v = st['a'].static_mesh_component.get_physics_linear_velocity()
            rec('throw', dict(speed=round(v.length()), held=bool(M.GS['held']), last=M.GS.get('last_throw')))
            shot('G66_throw')
    def after(t, first):
        if 'a' not in st:
            return
        if first:
            M.VIRTUAL['down'].discard('LeftMouseButton')
            p = st['a'].get_actor_location()
            rec('thrown_to', dict(moved=round((p - st['p0']).length() / 100, 2), z=round(p.z / 100, 2)))
    return [(.5, setup), (1.4, grab), (.9, swing), (1.4, throw), (1.6, after)]


def equip():
    st = {}

    def setup(t, first):
        if not first:
            return
        pool = [c for spot in S['spots'] for c in pick_target(*spot)]
        pool.sort(key=lambda q: 'hammer' not in q[1].get_actor_label())        # equip the hammer if there is one
        for d2, a, o, e in pool:
            if st.get('skip') is None:
                st['skip'] = S.get('grabbed')
            if a == st['skip']:
                continue
            if max(e.x, e.y, e.z) * 2 > 75 or o.z > 160:
                continue
            for ang in range(0, 360, 45):
                x = o.x / 100 + 1.3 * math.cos(math.radians(ang)); y = -o.y / 100 - 1.3 * math.sin(math.radians(ang))
                place(x, y, 0.0); look_at(o)
                if sees(a, o):
                    st['a'] = a; rec('equip_target', a.get_actor_label()); return
        rec('equip_target', None)
    def grab(t, first):
        if 'a' not in st:
            return
        M.VIRTUAL['down'].add('LeftMouseButton')
        if first:
            press('LeftMouseButton')
        if t > .7 and not st.get('f'):
            st['f'] = 1; press('F')
        if t > 1.0 and not st.get('r'):
            st['r'] = 1; rec('equipped_now', dict(R=M.GS['hands']['R'].get_actor_label() if M.GS['hands']['R'] else None,
                                                   held=bool(M.GS['held'])))
    def hold(t, first):
        if 'a' not in st:
            return
        if first:
            M.VIRTUAL['down'].discard('LeftMouseButton')
            look_at(G.v([-29.6, 1.0, 1.45]))                              # down the open concourse
            rec('equipped', dict(R=M.GS['hands']['R'].get_actor_label() if M.GS['hands']['R'] else None, held=bool(M.GS['held'])))
        if t > .6 and not st.get('s'):
            st['s'] = 1; shot('G66_equipped')
    def use(t, first):
        if 'a' not in st:
            return
        if first:
            press('RightMouseButton')
        if .18 < t and not st.get('u'):
            st['u'] = 1; shot('G66_use'); rec('use', dict(kind=M.kind(st['a']), msg=G.S.get('message'),
                                                            events=M.GS['events'][-3:]))
    def toss(t, first):
        if 'a' not in st:
            return
        if first:
            press('Q')
        if t > .8 and not st.get('q'):
            st['q'] = 1; rec('tossed', dict(R=bool(M.GS['hands']['R']), sim=st['a'].static_mesh_component.is_simulating_physics()))
    return [(.5, setup), (1.2, grab), (1.0, hold), (.8, use), (1.2, toss)]


def sit():
    st = {}

    def setup(t, first):
        if first:
            place(-28.5, 28.2, 180.0, -32)            # in front of terrace tier 1, looking down at its top
    def go(t, first):
        if first:
            h = M.aimed(2.4)
            rec('sit_aim', dict(hit=h[9].get_actor_label() if h and h[9] else None, z=round(h[5].z / 100, 3) if h else None,
                                nz=round(h[7].z, 2) if h else None))
            press('E')
        if t > .9 and not st.get('s'):
            st['s'] = 1; rec('sat', dict(seated=bool(G.P.STATE.get('seated')))); shot('G66_sit')
    def up(t, first):
        if first and G.P.STATE.get('seated'):
            G.P.stand()
    return [(.6, setup), (1.4, go), (.5, up)]


def scenes():
    steps = []
    for f in (hop_terrace, knee_block, slide, tether, equip, sit):
        steps += [(f.__name__, d, fn) for d, fn in f()]
    return steps


# ---------------------------------------------------------------- driver

def save(status='RUNNING', **kw):
    d = dict(status=status, step=S['i'], shots=S['shots'], log=S['log'], gs=dict(
        errors=M.GS['errors'] if M else None, jumps=M.GS['jumps'] if M else None, grabs=M.GS['grabs'] if M else None,
        throws=M.GS['throws'] if M else None, converted=M.GS['converted'][:40] if M else None,
        events=M.GS['events'][-30:] if M else None, falls=M.GS.get('falls') if M else None), **kw)
    (G.R / 'Pass48' / 'Game66.json').write_text(json.dumps(d, indent=1, default=str), encoding='utf-8')


def tick(dt):
    try:
        now = time.monotonic()
        if now < S['next']:
            return
        if not S['steps']:
            import gameplay66
            global M
            M = gameplay66
            if not M.active():
                raise RuntimeError('gameplay66 not active in probe run')
            S['steps'] = scenes(); S['t0'] = now; S['first'] = True
        if S['i'] >= len(S['steps']):
            save('SUCCESS'); quit_(); return
        name, d, fn = S['steps'][S['i']]
        t = now - S['t0']
        fn(t, S['first']); S['first'] = False
        if t >= d:
            S['i'] += 1; S['t0'] = now; S['first'] = True
            save()
    except Exception:
        save('ERROR', error=traceback.format_exc()); quit_()


def quit_():
    u.unregister_slate_post_tick_callback(S['handle'])
    S['next'] = 1e18
    G.P.STATE['quit_at'] = time.monotonic() + 3
    u.register_slate_post_tick_callback(lambda dt: time.monotonic() > G.P.STATE['quit_at'] and
                                        u.SystemLibrary.quit_game(G.P.STATE['world'], pc(), u.QuitPreference.QUIT, False))


def start(game):
    global G
    G = game
    (G.R / 'Pass48' / OUT).mkdir(parents=True, exist_ok=True)
    spec = G.R / 'Pass48' / 'Game66Scenes.json'
    cfg = json.loads(spec.read_text(encoding='utf-8')) if spec.exists() else {}
    S['spots'] = [tuple(p) for p in cfg.get('spots', [[-26.9, 7.0], [-36.5, 33.0], [-44.0, 20.0], [-28.0, 18.0]])]   # renovation corner, cafe bar, cafe, gate A08
    S['next'] = time.monotonic() + 8.0
    (G.R / 'Pass48' / 'Game66.json').write_text(json.dumps(dict(status='RUNNING')), encoding='utf-8')
    S['handle'] = u.register_slate_post_tick_callback(tick)
