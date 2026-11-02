"""Gameplay66: playful first-person feel for the airport (Airport38 Pass66).

Agreed direction (player interview 2026-11-02): first person, snappy and
bouncy movement, R.E.P.O.-style floaty tether physics on almost everything,
equippable hand items, comedy reactions, a journey with no timer.

  move     snappy acceleration and braking; walk 4.0 m/s, sprint 6.0 m/s (Shift); a hop
           takes off at walking pace at most (Pass70)
  camera   wider FOV (88) that kicks out to 100 with real speed; after the
           Crossing engine's feel.js: a footfall gait, a head that rocks with
           each step, leans into sidesteps and corners, lags starts, nods on
           stops and landings and breathes hard after a sprint; hands that lag
           fast looks; landing squash; a crosshair that reacts to grabbables
  jump     Space: a springy hop; you land on whatever you hop onto (benches,
           terrace tiers, tables, suitcases) and drop off its edge
  slide    Ctrl while sprinting: a low, fast cartoon slide
  sit      E on any seat-height surface when nothing else is aimed at
  grab     hold Left Mouse on a loose object: it floats on a spring in front
           of you, swings and lags; mouse wheel = nearer/further; hold Right
           Mouse to wind up (it draws back over your shoulder), release to
           throw - harder the longer you held; let go = drop. Heavy things
           drag and sag.
  hands    F while holding something small: equip it (right hand, then left);
           F with nothing held: take the right-hand item back on the tether;
           Q: toss the right-hand item; Right Mouse with no tether: use it
           (a hammer swings and knocks things over, cups are sipped, anything
           else is turned over and admired); G aimed at someone: give it to them
  react    passengers and staff flinch and shout when things fly past them,
           thank you for gifts, complain when bonked; nothing is ever punished

Never active in automated runs (journey QA, captures, probes, performance,
another tool's demos): it then passes straight through, so those runs see the
old behaviour. '-Gameplay66Probe' turns it on inside an automated run so a
probe can drive it through VIRTUAL key presses.
"""
import unreal as u, math, random, time, traceback

A = None            # airport_runtime module
P = None            # skyward_runtime module
GS = dict(errors=0, held=None, dist=1.6, hands={'R': None, 'L': None}, vz=0.0, air=False, surface=None, base=None,
          bob=0.0, phase=0.0, squash=0.0, squash_v=0.0, fov=88.0, fov_sent=0.0, slide=0.0, use=None, thrown={}, react={},
          was_seated=False, last_e=0.0, converted=[], events=[], aim=None, jumps=0, landings=0, grabs=0, throws=0,
          dot_v=0.0, dot_s=.0026, used=set(), homes={}, touched=set(), falls={}, charge=None)
VIRTUAL = dict(down=set(), pressed=set())       # probe input
GRAVITY, JUMP_V = 14.0, 4.4                     # m/s^2, m/s (a 0.69 m hop, 0.63 s in the air)
WALK, SPRINT, SLIDE = 400, 600, 1000            # cm/s (Pass70: sprint 720 -> 600, the player found it far too fast)
CABIN_WALK, CABIN_SPRINT = 250, 340             # aboard the aircraft
PLAYER_EYE = 1.5                                # Pass70: a little shorter than the NPCs' 1.62 eye (gameplay only)
ACC, DEC = 5200, 9000
AUTOMATED = ('-AirportQA', '-AirportCapture', '-RenderOffscreen', '-Repair39', '-Validate', '-FriendAction03Demo', '-Gameplay66Off')
PROTECTED = ('COL_', 'CH12', 'AP COLL', 'MOTION_PROXY', 'P51 ', 'P54 ', 'P55 ', 'P58 ', 'P66 ', 'SM_Plane_', 'Slab', 'Floor',
             'Wall', 'Ceiling', 'Roof', 'Glazing', 'Bridge', 'Finished Grounds', 'SkyCloud', 'Entrance sliding', 'Screening',
             'A07 boarding', 'Arrivals public', 'Staff service', 'Aircraft door', 'Flightdeck', 'Lavatory', 'Terminal WC',
             'Check-in desk', 'Bag drop belt', 'Gate A0', 'Usable extinguisher', 'Extinguisher',
             'Cloud Nine serving', 'Jetbridge', 'Tow', 'Baggage tug', 'Aircraft', 'Door', 'Stair', 'Escalator', 'Lift')
LINES = {'flinch': ['Hey! Watch it!', 'Whoa!', 'Careful!', 'Oi! That nearly hit me!', 'Was that... a chair?!', 'Not again...',
                    'Somebody call security. Or don\'t. Whatever.', 'My coffee!'],
         'hit': ['Ow!', 'Excuse me?!', 'Really?', 'I felt that!', 'Is this part of the in-flight service?'],
         'give': ['Oh! Thank you!', 'For me? How kind.', 'Er... thanks?', 'I will treasure this.', 'Just what I always wanted.'],
         'sip': ['Mmm, Cloud Nine coffee.', 'Still hot.', 'That hits the spot.', 'Slurp.'],
         'look': ['You turn it over in your hands.', 'Nice. Very airport.', 'Looks well made.', 'Hm. Interesting.']}


def K(n):
    k = u.Key(); k.import_text(n); return k


KEYS = {n: K(n) for n in ('SpaceBar', 'LeftShift', 'LeftControl', 'LeftMouseButton', 'RightMouseButton', 'MouseScrollUp',
                          'MouseScrollDown', 'F', 'Q', 'G', 'E', 'W')}


def active():
    if A is None or P is None or not P.STATE.get('pawn') or not P.STATE.get('pc'):
        return False
    cmd = A.CMD
    if '-Gameplay66Probe' not in cmd and '-P48_game66' not in cmd:
        if A.QA or A.CAPTURE or any(f in cmd for f in AUTOMATED):
            return False
    if A.S.get('spectator') or A.S.get('driving') or P.STATE.get('review_index', -1) >= 0 or P.STATE.get('inspecting'):
        return False
    return True


def say(s, seconds=2.2):
    A.S['message'] = s; A.S['message_until'] = time.monotonic() + seconds
    GS['events'].append([round(time.monotonic(), 2), s])
    del GS['events'][:-40]


SFX_DIR = '/Game/Airport38/Gameplay66/Audio/SFX66_'


def sfx(name, at=None, volume=1.0, pitch=1.0):
    """Play a Gameplay66 effect: in the head (2D) or at a world point."""
    try:
        cache = GS.setdefault('sfx', {})
        if name not in cache:
            cache[name] = u.load_asset(SFX_DIR + name)
        s = cache[name]
        if not s:
            return
        pitch *= random.uniform(.94, 1.06)                             # never quite the same twice
        if at is None:
            fn = next(getattr(u.GameplayStatics, n) for n in ('play_sound2d', 'play_sound_2d') if hasattr(u.GameplayStatics, n))
            fn(P.STATE['world'], s, volume, pitch)
        else:
            u.GameplayStatics.play_sound_at_location(P.STATE['world'], s, at, u.Rotator(), volume, pitch)
    except Exception:
        pass


def down(n):
    return n in VIRTUAL['down'] or P.STATE['pc'].is_input_key_down(KEYS[n])


def pressed(n):
    return n not in GS['used'] and (n in VIRTUAL['pressed'] or P.STATE['pc'].was_input_key_just_pressed(KEYS[n]))


def take(n):
    """A press acts once: equipping with F must not also un-equip in the same frame."""
    if pressed(n):
        GS['used'].add(n); return True
    return False


def cam():
    m = P.STATE['pc'].player_camera_manager
    return m.get_camera_location(), m.get_camera_rotation()


def aim():
    """Where the player is really pointing: the camera's place, but the aim without the head's sway
    (breath, step nod, lean), so a thin handle stays under the crosshair while you breathe."""
    loc, rot = cam()
    cr = P.STATE['pc'].get_control_rotation()
    return loc, u.Rotator(roll=0.0, pitch=cr.pitch - HEAD['pitch_sent'], yaw=cr.yaw)


def trace(a, b, ignore=()):
    h = u.SystemLibrary.line_trace_single(P.STATE['world'], a, b, u.TraceTypeQuery.TRACE_TYPE_QUERY1, True,
                                          [P.STATE['pawn']] + [x for x in ignore if x], u.DrawDebugTrace.NONE, True)
    t = h.to_tuple() if h else None
    return t if t and t[0] else None


def carried():
    return [GS['held'], GS.get('dot') or None] + list(GS['hands'].values())


def aboard():
    return P.STATE['pawn'].get_actor_location().x > 1200


def interactive_nearby():
    return A.nearest() is not None or P.nearest() is not None


# ---------------------------------------------------------------- vertical: jump, surfaces, bob

STEP = .3                                       # walk-up height; anything taller needs a hop


def slope_zone(name):
    return any(z.get('slope') and z['name'] == name for z in P.DATA.get('layout', {}).get('navigation_floors', []))


def ground_below(pos, feet, depth=60.0):
    """The highest real surface under the player within 'depth' m (spectator exits, gaps in the authored floors)."""
    t = trace(u.Vector(pos.x, pos.y, (feet + .25) * 100), u.Vector(pos.x, pos.y, (feet - depth) * 100), carried())
    return t[5].z / 100 if t and t[7].z > .5 else None


# The aircraft's own decks at the gate (source metres): the steep lower-hold stair (2.05 m down over 2.3 m), the
# hold floor, and the cabin and flight deck. Pass70: the plane's floor picker only accepts a surface within 0.28 m
# of the feet, so one long frame on the stair stranded the player in mid-air, and coming back up could leave them
# at the last stair sample instead of the deck. After it runs, the height is re-read from the real geometry.
STAIR = dict(x0=13.9, x1=15.35, y0=1.2, y1=3.5, top=0.0, bottom=-2.05, hatch='Lower cargo stair hatch')
HOLD = dict(x0=14.6, x1=17.4, y0=1.3, y1=34.65, z=-2.05)
DECK = dict(x0=13.6, x1=18.4, y0=-5.4, y1=35.1, z=0.0)


def plane_floor_fix(pawn, dt):
    if GS.get('hop', 0.0) > 0:
        return
    p = pawn.get_actor_location(); x, y = p.x / 100, -p.y / 100
    eye = P.EYE_HEIGHT; feet = p.z / 100 - eye
    hatch = P.STATE.get('movables', {}).get(STAIR['hatch'], {}).get('progress', 0) >= .9
    want = None
    if hatch and STAIR['x0'] <= x <= STAIR['x1'] and STAIR['y0'] <= y <= STAIR['y1'] and -2.4 < feet < .45:
        t = (y - STAIR['y0']) / (STAIR['y1'] - STAIR['y0'])
        want = STAIR['top'] + (STAIR['bottom'] - STAIR['top']) * t
    elif HOLD['x0'] <= x <= HOLD['x1'] and HOLD['y0'] <= y <= HOLD['y1'] and feet < -1.0:
        want = HOLD['z']
    elif DECK['x0'] <= x <= DECK['x1'] and DECK['y0'] <= y <= DECK['y1'] and -1.0 < feet < .5:
        want = DECK['z']
    if want is None or abs(want - feet) < .01:
        return
    z = feet + (want - feet) * min(1.0, dt * 18) if abs(want - feet) < .3 else want   # glide on the stair, snap if stranded
    pawn.set_actor_location(u.Vector(p.x, p.y, (z + eye) * 100), True, False)
    a = pawn.get_actor_location()
    mv = pawn.get_component_by_class(u.FloatingPawnMovement)
    mv.set_plane_constraint_origin(u.Vector(0, 0, a.z)); mv.set_plane_constraint_enabled(True)
    P.STATE['floor_z'] = a.z / 100 - eye


def cabin_floor(original, dt):
    """Aboard, the flight code snaps the player to its decks every frame; a hop rides on top of that snap.
    The hop is taken off before the flight code looks, or it would read the hop as a new deck and stack it."""
    pawn = P.STATE['pawn']
    if GS.get('hop', 0.0) > 0:
        p = pawn.get_actor_location()
        pawn.set_actor_location(u.Vector(p.x, p.y, p.z - GS['hop'] * 100), False, True)
    r = original(dt)
    plane_floor_fix(pawn, dt)
    if GS['air']:
        GS['vz'] -= GRAVITY * dt
        GS['hop'] = GS.get('hop', 0.0) + GS['vz'] * dt
        if GS['hop'] <= 0:
            impact = -GS['vz']
            GS.update(hop=0.0, air=False, vz=0.0); GS['landings'] += 1
            GS['squash_v'] -= min(1.0, impact * .25); HEAD['land'][1] -= min(.6, impact * .12) * FEEL['landing']
            sfx('Land', volume=min(.8, .3 + impact * .1))
    if GS.get('hop', 0.0) > 0:
        p = pawn.get_actor_location()
        pawn.set_actor_location(u.Vector(p.x, p.y, (P.STATE.get('floor_z', p.z / 100 - P.EYE_HEIGHT) + P.EYE_HEIGHT + GS['hop']) * 100), True, False)
        if pawn.get_actor_location().z < p.z + GS['hop'] * 100 - 3 and GS['vz'] > 0:
            GS['vz'] = 0.0                                              # head on a bin
    return r


def floor_wrap(original):
    def update_floor(dt):
        if active() and not P.STATE.get('seated') and (A.S.get('aboard') or aboard()):
            GS['surface'] = None; GS['base'] = None; GS['bob'] = 0.0; GS['prev'] = None
            return cabin_floor(original, min(dt, .05))
        if not active() or P.STATE.get('seated'):
            GS['air'] = False; GS['surface'] = None; GS['base'] = None; GS['bob'] = 0.0; GS['prev'] = None; GS['hop'] = 0.0
            return original(dt)
        dt = min(dt, .05)
        pawn = P.STATE['pawn']; pos = pawn.get_actor_location(); eye = P.EYE_HEIGHT
        feet = pos.z / 100 - eye - GS['bob']
        if not slope_zone(P.STATE.get('floor_name', '')):                  # stairs keep their smooth nav slope
            pos = knee_block(pawn, pos, feet)
        elevated = GS['air'] or GS['surface'] is not None
        if GS['base'] is None:
            GS['base'] = feet
        nav, name = P.floor_at_source(pos.x / 100, -pos.y / 100, GS['base'] if elevated else feet)
        if nav is None or name == 'Current deck':                       # no authored floor here: stand on what is really there
            g = ground_below(pos, feet, 60.0 if GS['air'] else .42)    # (in the air, never on 'wherever you are now')
            nav, name = (g, 'Physical supporting surface66') if g is not None else (feet - 3.0 if GS['air'] else feet, name)
        if not elevated or abs(nav - GS['base']) < .3:
            GS['base'] = nav
        stairs = slope_zone(name)
        if GS['air']:
            GS['vz'] -= GRAVITY * dt
            z = feet + GS['vz'] * dt
            ground = max(nav, top_below(pos, nav, feet + .02)) if GS['vz'] <= 0 else nav
            if z <= ground:
                impact = -GS['vz']
                z = ground; GS['air'] = False; GS['vz'] = 0.0; GS['landings'] += 1
                GS['surface'] = ground if ground > nav + .12 else None
                GS['squash_v'] -= min(1.4, impact * .3)                     # landing squash
                HEAD['land'][1] -= min(.9, impact * .16) * FEEL['landing']      # and the head nods into it
                sfx('Land', volume=min(1.0, .35 + impact * .12))
        elif GS['surface'] is not None:
            top = top_below(pos, nav, feet + STEP)
            if top < feet - .06:                                            # walked off the edge
                GS['air'] = True; GS['vz'] = 0.0; z = feet; GS['surface'] = None
            else:
                z = top; GS['surface'] = top if top > nav + .12 else None
        else:
            top = -99.0 if stairs else top_below(pos, nav, feet + STEP)   # walk up onto low things
            if top > nav + .12:
                z = top; GS['surface'] = top; GS['squash_v'] -= .2
            elif stairs and abs(nav - feet) < .4:                       # stairs glide instead of stepping
                z = feet + (nav - feet) * min(1.0, dt * 16)
            else:
                z = nav
        GS['stairs'] = stairs
        GS['bob'] = camera_bob(dt)
        target = (z + eye + GS['bob']) * 100
        if abs(target - pos.z) > .05:
            pawn.set_actor_location(u.Vector(pos.x, pos.y, target), True, False)
        actual = pawn.get_actor_location()
        if GS['air'] and GS['vz'] > 0 and actual.z < target - 2:            # bumped a ceiling
            GS['vz'] = 0.0
        GS['prev'] = actual
        mv = pawn.get_component_by_class(u.FloatingPawnMovement)
        mv.set_plane_constraint_origin(u.Vector(0, 0, actual.z)); mv.set_plane_constraint_enabled(True)
        P.STATE['floor_z'] = actual.z / 100 - eye - GS['bob']; P.STATE['floor_name'] = name
    update_floor._g66 = True
    return update_floor


def ensure_floor_wrap():
    """The journey and flight modules install their own update_floor during initialise; wrap whichever is current."""
    if not getattr(P.update_floor, '_g66', False):
        P.update_floor = floor_wrap(P.update_floor)


def knee_block(pawn, pos, feet):
    """The pawn's own collision rides at eye height; this stops the legs walking through anything a step can't climb."""
    prev = GS.get('prev')
    if prev is None:
        return pos
    d = u.Vector(pos.x - prev.x, pos.y - prev.y, 0)
    n = d.length()
    if n < .5 or n > 120:
        return pos
    f = d * (1.0 / n)
    knee = (feet + STEP + .04) * 100
    for lift in (0, 38, 72):                                            # Pass70: shin, stool seat, desk top - a thin line
        a = u.Vector(prev.x, prev.y, knee + lift)                       # slipped between stool legs and under desk tops
        h = u.SystemLibrary.sphere_trace_single(P.STATE['world'], a, u.Vector(pos.x + f.x * 22, pos.y + f.y * 22, knee + lift), 14.0,
                                                u.TraceTypeQuery.TRACE_TYPE_QUERY1, True,
                                                [P.STATE['pawn']] + [x for x in carried() if x], u.DrawDebugTrace.NONE, True)
        t = h.to_tuple() if h else None
        if not t or not t[0] or abs(t[7].z) > .5 or (t[9] and (npc_of(t[9]) or grabbable(t[9]))):
            continue
        hn = u.Vector(t[7].x, t[7].y, 0); hn = hn * (1.0 / max(hn.length(), 1e-4))
        inside = t[5] - hn * 3
        top = trace(u.Vector(inside.x, inside.y, (feet + 1.35) * 100), u.Vector(inside.x, inside.y, feet * 100), carried())
        if top and top[7].z > .7 and top[5].z / 100 <= feet + STEP:
            continue
        stop = u.Vector(t[5].x - f.x * 22, t[5].y - f.y * 22, 0)        # back off to the contact, then slide along it
        rest = u.Vector(pos.x - stop.x, pos.y - stop.y, 0)
        along = rest - hn * rest.dot(hn)
        new = u.Vector(stop.x + along.x, stop.y + along.y, pos.z)
        if (new - u.Vector(prev.x, prev.y, pos.z)).dot(hn) < 0:
            new = u.Vector(prev.x + along.x, prev.y + along.y, pos.z)
        pawn.set_actor_location(new, False, False)
        return new
    return pos


def top_below(pos, nav, limit):
    """Highest walkable top (normal up) under the player's footprint, above the nav floor and at or below 'limit'."""
    best = -99.0
    for dx, dy in ((0, 0), (16, 0), (-16, 0), (0, 16), (0, -16)):
        a = u.Vector(pos.x + dx, pos.y + dy, (limit + .3) * 100)
        t = trace(a, u.Vector(a.x, a.y, (nav - .05) * 100), carried())
        if t and t[7].z > .7:
            h = t[5].z / 100
            if nav + .12 < h <= limit:
                best = max(best, h)
    return best


# ---------------------------------------------------------------- camera life
# After feel.js in the Crossing engine ("the grail"): a walking rhythm whose stride grows with speed, and
# a head that rocks with each step, leans into sidesteps and corners, lags a start and nods on a hard
# stop or a landing, and breathes (hard after a sprint). Every FEEL scale is 1 = as designed, 0 = off.
FEEL = dict(bob=1.0, sway=1.0, strafe=1.0, turn=1.0, nod=1.0, landing=1.0, breath=1.0, hand_lag=1.0, fov_kick=12.0)
HEAD = dict(tilt=[0.0, 0.0], nod=[0.0, 0.0], land=[0.0, 0.0], lag_r=[0.0, 0.0], lag_u=[0.0, 0.0], vf=0.0, af=0.0,
            yaw=None, yaw_rate=0.0, breath=random.uniform(0, 10), t=random.uniform(0, 10), effort=0.0, w=0.0,
            stride=0.0, step_dist=0.0, steps=0, gait_on=False, sprint=0.0, pitch_sent=0.0, rolled=False)


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def smoothstep(a, b, x):
    t = clamp((x - a) / (b - a)) if b > a else float(x >= b)
    return t * t * (3 - 2 * t)


def spring(s, target, k, d, dt):
    """A damped spring s = [value, velocity]."""
    s[1] += (k * (target - s[0]) - d * s[1]) * dt
    s[0] += s[1] * dt
    return s[0]


def speeds():
    return (CABIN_WALK, CABIN_SPRINT) if aboard() else (WALK, SPRINT)


def gait(dt, speed):
    """Footfalls: GS['phase'] advances pi per step; the stride grows with speed (m/s), so the cadence stays
    human (about 2 steps/s walking, 3 flat out) and the first step from standing comes early."""
    moving = speed > .4 and not GS['air'] and GS['slide'] <= 0
    HEAD['w'] += ((1.0 if moving else 0.0) - HEAD['w']) * min(1.0, dt * 6)
    stride = clamp(.38 + .24 * speed, .42, 1.75)
    prev = HEAD['stride'] or stride
    s = prev + (stride - prev) * min(1.0, dt * 6)
    HEAD['step_dist'] *= s / prev
    HEAD['stride'] = s
    if moving and not HEAD['gait_on'] and HEAD['w'] < .3:
        HEAD['step_dist'] = max(HEAD['step_dist'], s * .6)
    HEAD['gait_on'] = moving
    if moving:
        HEAD['step_dist'] += speed * dt
        if HEAD['step_dist'] > s:
            HEAD['step_dist'] = HEAD['step_dist'] - s if HEAD['step_dist'] < 2 * s else 0.0
            HEAD['steps'] += 1
    GS['phase'] = (HEAD['steps'] + HEAD['step_dist'] / s) * math.pi
    HEAD['gaited'] = True


def step_shape():
    """0..1, highest just as a foot lands: walking it rolls smoothly through the bottom, running the
    bottom turns into an impact and the top floats."""
    sin_p = math.sin(GS['phase'])
    sharp = .2 + .55 * HEAD['sprint']
    return (1 - sin_p * sin_p) * (1 - sharp) + (1 - abs(sin_p)) * sharp


def camera_bob(dt):
    pawn = P.STATE['pawn']; vel = pawn.get_velocity(); speed = math.hypot(vel.x, vel.y) / 100
    walk, sprint = speeds()
    HEAD['sprint'] = smoothstep(walk / 100 * 1.05, sprint / 100 * .95, speed)
    gait(dt, speed)
    amp = (.03 + .035 * HEAD['sprint']) * HEAD['w'] * FEEL['bob']        # a touch bouncier than the Crossing's
    k, c = 95.0, 10.0                                                       # under-damped: bouncy
    GS['squash_v'] += (-k * GS['squash'] - c * GS['squash_v']) * dt
    GS['squash'] += GS['squash_v'] * dt
    crouch = -.5 * min(1.0, GS['slide'] * 3)
    breath = math.sin(HEAD['breath']) * .007 * (.15 + .85 * HEAD['effort']) * FEEL['breath']
    return -amp * step_shape() + breath + GS['squash'] + crouch


def head(dt):
    """Roll and pitch the view on top of the player's aim. Pitch goes on as a change since last frame, so
    the mouse is never fought; roll is set outright (nothing else in the game rolls the view)."""
    if dt <= 1e-4:
        return
    pc, pawn = P.STATE['pc'], P.STATE['pawn']
    cr = pc.get_control_rotation()
    if HEAD['yaw'] is not None:
        rate = math.radians(((cr.yaw - HEAD['yaw'] + 180) % 360) - 180) / dt
        HEAD['yaw_rate'] += (rate - HEAD['yaw_rate']) * min(1.0, dt * 10)
    HEAD['yaw'] = cr.yaw
    HEAD['t'] += dt
    if not HEAD.pop('gaited', False):                                      # the floor code passed through (the cabin): walk here
        v = pawn.get_velocity(); walk, sprint = speeds()
        HEAD['sprint'] = smoothstep(walk / 100 * 1.05, sprint / 100 * .95, math.hypot(v.x, v.y) / 100)
        gait(dt, math.hypot(v.x, v.y) / 100); HEAD.pop('gaited', None)
    y = math.radians(cr.yaw)
    v = pawn.get_velocity()
    vf = (v.x * math.cos(y) + v.y * math.sin(y)) / 100                     # m/s forward
    vr = (-v.x * math.sin(y) + v.y * math.cos(y)) / 100                    # m/s to the right
    a = clamp((vf - HEAD['vf']) / dt, -25, 25)
    HEAD['vf'] = vf
    HEAD['af'] += (a - HEAD['af']) * min(1.0, dt * 14)
    grounded = not GS['air']
    w, sp = HEAD['w'], HEAD['sprint']
    sin_p = math.sin(GS['phase'])
    roll = sin_p * .0045 * (1 + 1.2 * sp) * w * FEEL['sway']               # the view rocks with each step
    pitch = -(step_shape() - .5) * .007 * sp * w * FEEL['bob']             # and nods with each running stride
    strafe = clamp(vr * .012, -.04, .04) * FEEL['strafe']                 # into a sidestep (UE: + roll tilts right)
    turn = clamp(HEAD['yaw_rate'] * max(0.0, vf) * .0045, -.03, .03) * FEEL['turn'] * (1 if grounded else .3)
    roll += spring(HEAD['tilt'], strafe + turn, 70, 15, dt)
    pitch += spring(HEAD['nod'], clamp(HEAD['af'] * .0032, -.05, .05) * FEEL['nod'] * (1 if grounded else .2), 85, 12, dt)
    pitch += spring(HEAD['land'], 0.0, 130, 15, dt)
    charge = GS.get('charge') or 0.0
    pitch += .02 * charge * charge * (3 - 2 * charge)                      # leaning back into a wind-up
    target = 1.0 if (down('LeftShift') and HEAD['sprint'] > .5) or GS['slide'] > 0 else 0.0
    HEAD['effort'] += (target - HEAD['effort']) * min(1.0, dt * (.9 if target > HEAD['effort'] else .16))
    HEAD['breath'] += dt * math.pi * 2 * (.24 + .62 * HEAD['effort'])
    br = math.sin(HEAD['breath']); bk = (.15 + .85 * HEAD['effort']) * FEEL['breath']
    pitch += br * .009 * bk
    still = 1 - w; t = HEAD['t']                                            # nobody holds a camera that steady
    pitch += (math.sin(t * .53) * .0016 + math.sin(t * 1.31 + 1) * .0007) * still * FEEL['breath']
    roll += math.sin(t * .41 + 2) * .0013 * still * FEEL['breath']
    pd, rd = math.degrees(pitch), math.degrees(roll)
    pc.set_control_rotation(u.Rotator(roll=rd, pitch=cr.pitch + pd - HEAD['pitch_sent'], yaw=cr.yaw))
    HEAD['pitch_sent'] = pd; HEAD['rolled'] = True
    # the hands lag a fast look and a start or stop (cm, springs that settle in about 0.2 s)
    spring(HEAD['lag_r'], clamp(-math.degrees(HEAD['yaw_rate']) * .025, -7, 7) * FEEL['hand_lag'], 160, 20, dt)
    spring(HEAD['lag_u'], clamp(-HEAD['af'] * .5 - math.degrees(HEAD['nod'][1]) * .02, -5, 5) * FEEL['hand_lag'], 160, 20, dt)


def head_reset():
    """Take the head's roll and pitch back off (sitting, or gameplay switched off)."""
    if not HEAD['rolled'] or P is None or not P.STATE.get('pc'):
        return
    pc = P.STATE['pc']; cr = pc.get_control_rotation()
    pc.set_control_rotation(u.Rotator(roll=0.0, pitch=cr.pitch - HEAD['pitch_sent'], yaw=cr.yaw))
    HEAD.update(pitch_sent=0.0, rolled=False, yaw=None, yaw_rate=0.0, vf=0.0, af=0.0)
    for k in ('tilt', 'nod', 'land', 'lag_r', 'lag_u'):
        HEAD[k][0] = HEAD[k][1] = 0.0


# ---------------------------------------------------------------- movement feel

def movement(dt):
    pc, pawn = P.STATE['pc'], P.STATE['pawn']
    mv = pawn.get_component_by_class(u.FloatingPawnMovement)
    cabin = aboard()
    sprint = down('LeftShift') and down('W')
    if pressed('LeftControl') and sprint and not GS['air'] and GS['slide'] <= 0 and not cabin:
        GS['slide'] = .75; say('Wheee!', .9); sfx('Slide', volume=.6)
    speed = CABIN_WALK if cabin else WALK
    if GS['slide'] > 0:
        GS['slide'] = max(0.0, GS['slide'] - dt)
        f = u.MathLibrary.get_forward_vector(u.Rotator(yaw=pc.get_control_rotation().yaw))
        pawn.add_movement_input(f, 1.0)
        speed = WALK + (SLIDE - WALK) * (GS['slide'] / .75) ** .5
        if GS['slide'] == 0:
            GS['squash_v'] += .5                                            # pop back up
    elif sprint:
        speed = CABIN_SPRINT if cabin else SPRINT
    if GS['held'] is not None:
        speed *= .85
    acc, dec = ACC, DEC
    if GS['air']:                                                       # Pass70: a hop does not carry a sprint along
        walk = CABIN_WALK if cabin else WALK
        speed = min(speed, walk * .9); acc, dec = ACC * .4, DEC * .35
    mv.set_editor_property('max_speed', float(speed))
    mv.set_editor_property('acceleration', float(acc))
    mv.set_editor_property('deceleration', float(dec))
    mv.set_editor_property('turning_boost', 12.0)
    if pressed('SpaceBar') and not GS['air'] and not GS['was_seated'] and GS['slide'] <= 0:
        GS['air'] = True; GS['vz'] = JUMP_V; GS['squash_v'] -= .35; GS['jumps'] += 1
        sfx('Hop', volume=.5)
        v = mv.get_editor_property('velocity'); h = math.hypot(v.x, v.y); cap = (CABIN_WALK if cabin else WALK) * 1.05
        if h > cap:                                                     # take off at walking pace at most
            mv.set_editor_property('velocity', u.Vector(v.x * cap / h, v.y * cap / h, v.z))
    v = pawn.get_velocity(); walk, fast = speeds()                      # the kick follows real speed: blocked by a wall or a
    kick = smoothstep(walk * 1.05, max(walk * 1.1, fast * .92), math.hypot(v.x, v.y))   # crowd, Shift alone does not widen it
    target = 88.0 + FEEL['fov_kick'] * (kick if not cabin else .4 * kick)
    GS['fov'] += (target - GS['fov']) * min(1.0, dt * 7)
    if abs(GS['fov'] - GS['fov_sent']) > .3:
        u.SystemLibrary.execute_console_command(P.STATE['world'], 'fov %.1f' % GS['fov'], pc)
        GS['fov_sent'] = GS['fov']


# ---------------------------------------------------------------- tether grab and throw

def grabbable(actor):
    if not isinstance(actor, u.StaticMeshActor):
        return None
    lab = actor.get_actor_label()
    if lab.startswith(PROTECTED) or ' COLL ' in lab or lab.endswith(' collision'):
        return None
    c = actor.static_mesh_component
    if not c or not c.static_mesh or c.get_editor_property('hidden_in_game'):
        return None
    o, e = actor.get_actor_bounds(False)
    if max(e.x, e.y, e.z) * 2 > 240 or e.x * e.y * e.z * 8 > 2.2e6:      # bigger than ~2.4 m or 2.2 m^3
        return None
    return c


def remember(actor):
    lab = actor.get_actor_label()
    if lab not in GS['homes']:
        GS['homes'][lab] = (actor, actor.get_actor_location(), actor.get_actor_rotation())


def safety_net():
    """Mess stays where it lands, but nothing is lost through a gap: anything that falls well below where it
    started (out through glazing, under a floor) pops back to its original spot."""
    now = time.monotonic()
    if now < GS.get('net_next', 0):
        return
    GS['net_next'] = now + .5
    for lab, (a, home, rot) in list(GS['homes'].items()):
        if not u.SystemLibrary.is_valid(a):
            GS['homes'].pop(lab); continue
        if a is GS['held'] or a in GS['hands'].values():
            continue
        if a.get_actor_location().z < home.z - 250:
            c = a.static_mesh_component
            falls = GS.setdefault('falls', {}); falls[lab] = falls.get(lab, 0) + 1
            c.set_physics_linear_velocity(u.Vector(0, 0, 0), False)
            if falls[lab] >= 2 and lab not in GS.setdefault('touched', set()):
                c.set_simulate_physics(False)                           # it rests here until someone picks it up
            a.set_actor_location_and_rotation(home + u.Vector(0, 0, 2), rot, False, True)
            if lab in GS['touched']:
                say(nice(a)[4:].capitalize() + ' found its way back.', 1.4)


def make_physical(c):
    remember(c.get_owner())
    if c.is_simulating_physics():
        return True
    c.set_mobility(u.ComponentMobility.MOVABLE)
    c.set_collision_enabled(u.CollisionEnabled.QUERY_AND_PHYSICS)
    o, e = c.get_owner().get_actor_bounds(False)
    kg = max(.3, min(60.0, e.x * e.y * e.z * 8 / 1e6 * 90))           # airport-prop light: a cup 0.3 kg, a chair ~20 kg
    try:
        c.set_mass_override_in_kg(u.Name('None'), kg, True)
    except Exception:
        pass
    c.set_simulate_physics(True)
    c.wake_all_rigid_bodies()
    lab = c.get_owner().get_actor_label()
    if lab not in GS['converted']:
        GS['converted'].append(lab)
    return c.is_simulating_physics()


def aimed(reach=3.2):
    loc, rot = aim()
    return trace(loc, loc + u.MathLibrary.get_forward_vector(rot) * reach * 100, carried())


def grab_aim(reach=3.2):
    """What a grab would take: the exact aim, or, when that finds nothing loose, anything grabbable within
    9 cm of the aim line up to what the line hit, so a hammer lying flat or a magazine needs no pixel hunt."""
    t = aimed(reach)
    if t and t[9] and grabbable(t[9]):
        return t
    loc, rot = aim()
    f = u.MathLibrary.get_forward_vector(rot)
    end = loc + f * ((t[3] + 10) if t else reach * 100)
    h = u.SystemLibrary.sphere_trace_single(P.STATE['world'], loc + f * 20, end, 9.0, u.TraceTypeQuery.TRACE_TYPE_QUERY1, True,
                                            [P.STATE['pawn']] + [x for x in carried() if x], u.DrawDebugTrace.NONE, True)
    s = h.to_tuple() if h else None
    return s if s and s[0] and s[9] and grabbable(s[9]) else t


def grab(actor, c, distance):
    GS.setdefault('touched', set()).add(actor.get_actor_label())
    if not c.is_simulating_physics():
        c.set_simulate_physics(True); c.wake_all_rigid_bodies()
    GS['held'] = actor; GS['dist'] = max(1.1, min(2.8, distance / 100 + .15)); GS['grabs'] += 1
    c.set_collision_response_to_channel(u.CollisionChannel.ECC_PAWN, A.IGNORE)
    c.set_angular_damping(2.5); c.set_linear_damping(.8)
    GS['squash_v'] -= .15
    sfx('Grab', actor.get_actor_location(), .5, 1.25 - min(.4, c.get_mass() / 40))


def tether(dt):
    held = GS['held']
    if held is None:
        if pressed('LeftMouseButton') and not A.S.get('held') and not P.STATE.get('seated') and not interactive_nearby():
            t = grab_aim()
            if t and t[9]:
                c = grabbable(t[9])
                if c and make_physical(c):
                    grab(t[9], c, t[3])
                elif c:
                    say('It will not budge.', 1.0)
                elif c is None and npc_of(t[9]):
                    react(npc_of(t[9]), 'hit')                         # poking people is allowed, and noted
        return
    if not u.SystemLibrary.is_valid(held):
        GS['held'] = None; return
    c = held.static_mesh_component
    if not down('LeftMouseButton'):
        drop(); return
    if pressed('MouseScrollUp'):
        GS['dist'] = min(3.4, GS['dist'] + .25)
    if pressed('MouseScrollDown'):
        GS['dist'] = max(.9, GS['dist'] - .25)
    loc, rot = cam()
    ch = GS.get('charge') or 0.0; ease = ch * ch * (3 - 2 * ch)                # winding up pulls it back over your shoulder
    goal = (loc + u.MathLibrary.get_forward_vector(rot) * max(.7, GS['dist'] - .45 * ease) * 100 + u.Vector(0, 0, -12 + 22 * ease)
            + u.MathLibrary.get_right_vector(rot) * (24 * ease))
    m = max(c.get_mass(), 1.0)
    light = min(1.0, 15.0 / m)                                         # heavy things drag, lag and sag
    com = c.get_center_of_mass(); vel = c.get_physics_linear_velocity()
    off = goal - com
    if off.length() > 260:                                             # snagged far behind something: let go
        drop(); say('It slipped away.', 1.0); return
    acc = off * (60 * light + 12) - vel * (4.2 * light + 2) + u.Vector(0, 0, 980 * (.4 + .6 * light))   # Pass70: springy (zeta ~0.35)
    n = acc.length()
    if n > 6000:
        acc = acc * (6000 / n)
    c.add_force(acc, A.NONE, True)
    w = c.get_physics_angular_velocity_in_radians()
    c.add_torque_in_radians(w * -4.0, A.NONE, True)
    if GS.get('charge') is None and take('RightMouseButton'):          # hold Right Mouse to wind up, release to throw
        GS['charge'] = 0.0
    if GS.get('charge') is not None:
        if down('RightMouseButton'):
            GS['charge'] = min(1.0, GS['charge'] + dt / .85)
        else:
            throw(clamp(GS['charge'], .12, 1.0)); return
    elif take('F'):
        equip(held)


def drop():
    h = GS['held']; GS['held'] = None; GS['charge'] = None
    if h and u.SystemLibrary.is_valid(h):
        c = h.static_mesh_component
        c.set_collision_response_to_channel(u.CollisionChannel.ECC_PAWN, A.BLOCK)
        c.set_angular_damping(.2); c.set_linear_damping(.05)


def throw(charge=.6):
    """Release at 'charge' (0.12 a flick .. 1 a full wind-up): a light thing flies up to 14 m/s, a heavy one
    lobs; you add your own running speed; it tumbles end over end about its middle, faster the harder
    it went and the smaller it is (after the Crossing engine's throwHeld)."""
    h = GS['held']; c = h.static_mesh_component
    loc, rot = aim()
    f = u.MathLibrary.get_forward_vector(rot); r = u.MathLibrary.get_right_vector(rot)
    m = max(c.get_mass(), 1.0)
    speed = 1400 * min(1.0, (15.0 / m) ** .5) * (.2 + .8 * charge)
    run = P.STATE['pawn'].get_velocity() * .8
    c.set_physics_linear_velocity(f * speed + u.Vector(run.x, run.y, 0) + u.Vector(0, 0, 90 + 90 * charge), False)
    o, e = h.get_actor_bounds(False)
    spin = math.degrees((2 + 6 * charge) / (1 + max(e.x, e.y, e.z) / 100 * 4))
    c.set_physics_angular_velocity_in_degrees(r * spin + u.Vector(random.uniform(-40, 40), random.uniform(-40, 40),
                                                                  random.uniform(-40, 40)), False)
    GS['thrown'][h.get_actor_label()] = (h, time.monotonic() + 3.0); GS['throws'] += 1
    GS['last_throw'] = dict(charge=round(charge, 2), speed=round(speed))
    sfx('Throw', loc + f * 80, .3 + .6 * charge, .9 + .25 * charge)
    GS['squash_v'] += .1 + .25 * charge
    HEAD['nod'][1] -= .35 * charge                                          # the follow-through
    drop()


# ---------------------------------------------------------------- hands

HAND = {'R': (48, 28, -31), 'L': (48, -28, -31)}                 # where characters12 draws the view hands


def legacy():
    try:
        import characters12_runtime as C
        return C if C.S.get('hands') else None
    except Exception:
        return None


def hidden(actor):
    for get in (lambda: actor.is_hidden(), lambda: actor.get_editor_property('hidden'),
                lambda: actor.root_component.get_editor_property('hidden_in_game')):
        try:
            return bool(get())
        except Exception:
            continue
    return False


def set_hand_mesh(C, side, grip):
    """Compare with the mesh really on the hand; characters12's own cache is left alone so the two never fight."""
    name = 'SM_CH12_ViewHand_' + side + ('Grip' if grip and side == 'R' else '')
    hand = C.S['hands'].get(side)
    mesh = C.S.get('hand_meshes', {}).get(name)
    if hand and mesh and hand.static_mesh_component.static_mesh != mesh:
        hand.static_mesh_component.set_static_mesh(mesh)
        try:
            C.update_hand_colour()
        except Exception:
            pass


def equip(actor):
    o, e = actor.get_actor_bounds(False)
    if max(e.x, e.y, e.z) * 2 > 80:
        say('Too big to hold in one hand.', 1.2); return
    slot = 'R' if GS['hands']['R'] is None else 'L' if GS['hands']['L'] is None else None
    if slot is None:
        say('Both hands are full.', 1.2); return
    GS['held'] = None
    c = actor.static_mesh_component
    c.set_simulate_physics(False); c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
    GS['hands'][slot] = actor
    sfx('Equip', volume=.6)
    say('Equipped ' + nice(actor) + (' (right hand)' if slot == 'R' else ' (left hand)'), 1.6)


def nice(actor):
    s = (actor.get_actor_label() + ' ' + actor.static_mesh_component.static_mesh.get_name()).lower()
    for w in ('hammer', 'mallet', 'cup', 'mug', 'coffee', 'magazine', 'book', 'bag', 'bottle', 'phone', 'plant', 'chair',
              'tray', 'bin', 'cushion', 'lamp', 'cone', 'suitcase', 'case', 'sign', 'stool', 'pot', 'vase'):
        if w in s:
            return 'the ' + w
    return 'the ' + actor.get_actor_label().split(' ')[0].lower()


def kind(actor):
    s = (actor.get_actor_label() + ' ' + actor.static_mesh_component.static_mesh.get_name()).lower()
    if any(w in s for w in ('hammer', 'mallet', 'wrench', 'bat', 'umbrella')):
        return 'hammer'
    if any(w in s for w in ('cup', 'mug', 'coffee', 'saucer', 'glass', 'bottle')):
        return 'cup'
    return 'thing'


def hands(dt):
    owner = legacy()
    if owner and owner.S.get('paired_hand_owner'):
        return
    loc, rot = cam()
    f = u.MathLibrary.get_forward_vector(rot); r = u.MathLibrary.get_right_vector(rot); up = u.MathLibrary.get_up_vector(rot)
    C = legacy()
    hand_actor = {side: (C.S['hands'].get(side) if C else None) for side in ('R', 'L')}
    shown = bool(C) and not C.S.get('third') and not A.S.get('spectator')    # characters12's own rule for the view hands
    visible = {side: bool(h) and shown for side, h in hand_actor.items()}
    for slot, a in GS['hands'].items():
        if a is None or not u.SystemLibrary.is_valid(a):
            GS['hands'][slot] = None; continue
        fo, ri, dn = HAND[slot]
        bob = abs(math.sin(GS['phase'])) * 1.2 - GS['squash'] * 40
        hp = loc + f * fo + r * (ri + HEAD['lag_r'][0]) + up * (dn + bob + HEAD['lag_u'][0])   # the hand, lagging fast looks
        tool = kind(a) == 'hammer'
        rr = u.Rotator(roll=rot.roll, pitch=rot.pitch + (65 if tool else 0), yaw=rot.yaw)   # a hammer is held head-up
        if slot == 'R' and GS['use']:
            k, t0 = GS['use']; t = (time.monotonic() - t0) / .45; s = math.sin(math.pi * min(t, 1.0))
            if t >= 1:
                GS['use'] = None
            elif k == 'hammer':
                rr = u.Rotator(roll=rot.roll, pitch=rot.pitch + 65 - 85 * s, yaw=rot.yaw - 10 * s)   # chop forward
                hp = hp + f * (28 * s) - r * (10 * s) + up * (14 * s)
            elif k == 'cup':
                rr = u.Rotator(roll=rot.roll + 35 * s, pitch=rot.pitch + 25 * s, yaw=rot.yaw)
                hp = hp + up * (22 * s) - r * (22 * s) - f * (22 * s)
            else:
                rr = u.Rotator(roll=rot.roll, pitch=rot.pitch + 20 * s, yaw=rot.yaw + 360 * t)
                hp = hp + up * (12 * s) - r * (14 * s)
        # the item's centre sits in the grip (right) or rests on the open palm (left)
        centre = hp + up * (20 if tool else 9) + f * 4 + r * (-2 if slot == 'R' else 2)   # resting in the open palm
        a.set_actor_location_and_rotation(centre, rr, False, True)
        o, e = a.get_actor_bounds(False)
        a.set_actor_location(a.get_actor_location() + (centre - o), False, True)
        if visible[slot]:
            set_hand_mesh(C, slot, False)                               # the open cartoon hand reads best
            hand_actor[slot].set_actor_location(hp, False, True)
            hand_actor[slot].set_actor_rotation(u.Rotator(pitch=rot.pitch, yaw=rot.yaw - 90, roll=rot.roll), False)
    if C and visible['R'] and GS['hands']['R'] is None:
        held = GS['held']
        if held is not None and u.SystemLibrary.is_valid(held):         # the hand reaches out, gripping the tether
            set_hand_mesh(C, 'R', False)
            fo, ri, dn = HAND['R']
            ch = GS.get('charge') or 0.0                                # the hand reaches toward the item, at arm's length
            shoulder = loc + r * 20 + up * -24
            to = held.static_mesh_component.get_center_of_mass() - shoulder
            n = max(to.length(), 1.0)
            reach = shoulder + to * (min(n, 58.0) / n)
            hand_actor['R'].set_actor_location(reach - f * (22 * ch) + up * (10 * ch + HEAD['lag_u'][0]) + r * (8 * ch + HEAD['lag_r'][0]),
                                               False, True)
        elif not A.S.get('held'):
            set_hand_mesh(C, 'R', False)
    if C and visible['L'] and GS['hands']['L'] is None:
        set_hand_mesh(C, 'L', False)
    busy = GS['held'] is not None or bool(A.S.get('held')) or GS['aim'] is not None
    want = 1.0 if busy else 0.0                                         # Pass70: idle hands rest out of view
    spring(GS.setdefault('raise', [0.0, 0.0]), want, 150, 22, dt)
    lift = GS['raise'][0]
    for side in ('R', 'L'):
        if not (C and visible[side]) or GS['hands'][side] is not None or (side == 'R' and GS['held'] is not None):
            continue
        fo, ri, dn = HAND[side]
        bob = abs(math.sin(GS['phase'])) * 1.2 - GS['squash'] * 40
        hand_actor[side].set_actor_location(loc + f * (fo - 10 * (1 - lift)) + r * (ri + HEAD['lag_r'][0])
                                            + up * (dn + bob + HEAD['lag_u'][0] - 55 * (1 - lift)), False, True)
        hand_actor[side].set_actor_rotation(u.Rotator(pitch=rot.pitch, yaw=rot.yaw - 90, roll=rot.roll), False)
    if GS['held'] is not None:
        return
    n = A.S.get('held')                                                # the airport's own E pickups (cups, bags) equip too
    if n and 'extinguisher' not in n.lower() and A.S['actors'].get(n) and take('F'):
        a = A.S['actors'][n]
        c = a.static_mesh_component
        c.set_collision_response_to_channel(u.CollisionChannel.ECC_PAWN, A.BLOCK)
        A.S['held'] = None
        equip(a)
        if a not in GS['hands'].values():                              # too big: back to the airport's hold
            c.set_collision_response_to_channel(u.CollisionChannel.ECC_PAWN, A.IGNORE); A.S['held'] = n
        return
    full = GS['hands']['R'] or GS['hands']['L']
    if GS['hands']['R'] and take('RightMouseButton'):
        use_item(GS['hands']['R'])
    elif full and take('F'):
        slot = 'R' if GS['hands']['R'] else 'L'
        a = release_hand(slot); grab(a, a.static_mesh_component, 120)
    elif full and take('Q'):
        slot = 'R' if GS['hands']['R'] else 'L'
        a = release_hand(slot); grab(a, a.static_mesh_component, 120); throw(.5)
    elif GS['hands']['R'] and take('G'):
        give(GS['hands']['R'])


def release_hand(slot):
    a = GS['hands'][slot]; GS['hands'][slot] = None
    c = a.static_mesh_component
    c.set_collision_enabled(u.CollisionEnabled.QUERY_AND_PHYSICS); c.set_simulate_physics(True); c.wake_all_rigid_bodies()
    return a


def use_item(a):
    k = kind(a); GS['use'] = (k, time.monotonic())
    if k == 'hammer':
        loc, rot = aim(); f = u.MathLibrary.get_forward_vector(rot)
        hit = trace(loc, loc + f * 200, [a])
        if hit and hit[9]:
            target = hit[9]
            c = grabbable(target)
            if c and make_physical(c):
                GS.setdefault('touched', set()).add(target.get_actor_label())
                if not c.is_simulating_physics():
                    c.set_simulate_physics(True)
                c.add_impulse(f * 700 + u.Vector(0, 0, 260), A.NONE, True)
                GS['thrown'][target.get_actor_label()] = (target, time.monotonic() + 2.5)
                say('BONK!', .9); sfx('Bonk', hit[5], .9)
            elif npc_of(target):
                react(npc_of(target), 'hit'); sfx('Bonk', hit[5], .8, .8)
            else:
                say('Clang!', .7); sfx('Clang', hit[5], .55)
        else:
            say('Whoosh.', .6); sfx('Throw', volume=.4, pitch=1.3)
    elif k == 'cup':
        say(random.choice(LINES['sip']), 1.6); sfx('Sip', volume=.6)
    else:
        say(random.choice(LINES['look']), 1.6)


def npc_of(actor):
    lab = actor.get_actor_label()
    who = 'CH12 ' + lab[len('CH12COLL '):] if lab.startswith('CH12COLL ') else lab if lab.startswith('CH12 ') else None
    return None if who is None or 'avatar' in who.lower() else who


def npc_actors():
    try:
        import characters12_runtime as C
        return {k: v for k, v in C.ACTORS.items() if u.SystemLibrary.is_valid(v) and 'avatar' not in k.lower()}
    except Exception:
        return {}


def give(a):
    loc, rot = aim(); f = u.MathLibrary.get_forward_vector(rot)
    hit = trace(loc, loc + f * 280, [a])
    who = npc_of(hit[9]) if hit and hit[9] else None
    npc = npc_actors().get(who) if who else None
    if not npc:
        say('Aim at someone to give it to them.', 1.2); return
    GS['hands']['R'] = None
    c = a.static_mesh_component
    c.set_collision_enabled(u.CollisionEnabled.QUERY_AND_PHYSICS)
    p = npc.get_actor_location() + u.Vector(0, 0, 105) + u.MathLibrary.get_forward_vector(npc.get_actor_rotation()) * 28
    a.set_actor_location(p, False, True)
    c.set_simulate_physics(True); c.wake_all_rigid_bodies()                # it settles into their lap
    react(who, 'give', force=True)


def react(who, what, force=False):
    now = time.monotonic()
    if not force and now < GS['react'].get(who, 0):
        return
    GS['react'][who] = now + 4.0
    name = who.replace('CH12 ', '').replace('Additional ', '').split(' ')[0]
    say(name + ': "' + random.choice(LINES[what]) + '"', 2.4)
    try:
        npc = npc_actors().get(who)
        if npc and what in ('flinch', 'hit') and who not in GS.setdefault('flinch', {}):
            GS['flinch'][who] = (npc, npc.get_actor_location(), now)
    except Exception:
        pass


def reactions():
    now = time.monotonic()
    for who, (npc, home, t0) in list(GS.get('flinch', {}).items()):     # a quick cartoon duck and pop
        t = (now - t0) / .5
        if t >= 1 or not u.SystemLibrary.is_valid(npc):
            if u.SystemLibrary.is_valid(npc):
                npc.set_actor_location(home, False, True)
            GS['flinch'].pop(who); continue
        npc.set_actor_location(home + u.Vector(0, 0, -14 * math.sin(math.pi * t)), False, True)
    if not GS['thrown']:
        return
    npcs = npc_actors()
    for lab, (a, until) in list(GS['thrown'].items()):
        if now > until or not u.SystemLibrary.is_valid(a):
            GS['thrown'].pop(lab, None); continue
        c = a.static_mesh_component
        speed = c.get_physics_linear_velocity().length() if c.is_simulating_physics() else 0.0
        last = GS.setdefault('speeds', {}).get(lab, 0.0); GS['speeds'][lab] = speed
        if last > 280 and speed < last * .45 and a is not GS['held']:          # it hit something: thunk
            sfx('Land', a.get_actor_location(), min(1.0, last / 1200), 1.5 - min(.6, c.get_mass() / 20))
        if speed < 250:
            continue
        p = a.get_actor_location()
        for who, npc in npcs.items():
            if (npc.get_actor_location() + u.Vector(0, 0, 100) - p).length() < 160:
                react(who, 'flinch')


# ---------------------------------------------------------------- sit anywhere

def sit_anywhere():
    if not pressed('E') or P.STATE.get('seated') or GS['was_seated'] or GS['held'] or A.S.get('held') or GS['air']:
        return
    if time.monotonic() - GS['last_e'] < .4 or interactive_nearby():
        return
    GS['last_e'] = time.monotonic()
    t = aimed(2.4)
    if t and t[7].z < .7:                                               # aimed at the front of a seat: find its top
        loc, rot = cam(); f = u.MathLibrary.get_forward_vector(u.Rotator(yaw=rot.yaw))
        p = t[5] + f * 22
        t = trace(u.Vector(p.x, p.y, p.z + 70), u.Vector(p.x, p.y, p.z - 40), carried())
    if not t or t[7].z < .7:
        return
    floor = P.STATE.get('floor_z', 0.0)
    h = t[5].z / 100
    if not (floor + .3 <= h <= floor + 1.3):
        return
    loc, rot = cam(); f = u.MathLibrary.get_forward_vector(u.Rotator(yaw=rot.yaw))
    x, y = t[5].x / 100, -t[5].y / 100
    # you sit down the way people do: turned round, back to where you were looking
    P.sit(dict(kind='seat', title='Seat', location=[x, y, h + .72], facing=[-f.x, f.y], view_pitch=-4))
    say('Ahh.', .8)


# ---------------------------------------------------------------- crosshair and hints

HIGHLIGHT = '/Game/Airport38/Pass48/Materials/M_AP_P66Highlight'


def set_highlight(actor, on):
    try:
        if actor is not None and u.SystemLibrary.is_valid(actor):
            actor.static_mesh_component.set_overlay_material(GS['hl_mat'] if on else None)
    except Exception:
        pass


def crosshair(dt):
    held = GS['held'] is not None
    t = None if held else grab_aim()
    target = t[9] if t and t[9] and grabbable(t[9]) and not interactive_nearby() and not P.STATE.get('seated') else None
    lit = GS['held'] if held else target
    if lit is not GS['aim']:
        set_highlight(GS['aim'], False); set_highlight(lit, True)
        if lit is not None and not held:
            GS['dot_v'] += .05                                              # the dot pops as it finds something
            GS['squash_v'] -= .03
        GS['aim'] = lit
    dot = GS.get('dot')
    if dot is None:
        dot = next((a for a in u.GameplayStatics.get_all_actors_of_class(P.STATE['world'], u.StaticMeshActor)
                    if a.get_actor_label() == 'P66 crosshair dot'), False)
        GS['dot'] = dot
        if dot:
            dot.set_actor_enable_collision(False)                           # the profile can restore collision on load
            dot.static_mesh_component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
            GS['dot_mid'] = dot.static_mesh_component.create_dynamic_material_instance(0)
            GS['dot_mid'].set_scalar_parameter_value('Strength', 9.0)       # reads bright and warm through exposure
            GS['dot_s'] = .0012
    if dot:
        goal = (.0055 + .005 * (GS.get('charge') or 0.0)) if lit is not None else .0012   # springy; swells as you wind up
        GS['dot_v'] += ((goal - GS['dot_s']) * 260 - GS['dot_v'] * 16) * dt
        GS['dot_s'] = max(.0012, GS['dot_s'] + GS['dot_v'] * dt)
        eye = P.STATE['pawn'].get_actor_location(); rot = aim()[1]                                # the true aim, no camera lag
        dot.set_actor_location(eye + u.MathLibrary.get_forward_vector(rot) * 25, False, True)
        dot.set_actor_scale3d(u.Vector(GS['dot_s'], GS['dot_s'], GS['dot_s']))
        dot.static_mesh_component.set_hidden_in_game(GS['dot_s'] < .0016)
        warm = lit is not None
        if GS.get('dot_warm') != warm and GS.get('dot_mid'):
            GS['dot_warm'] = warm
            GS['dot_mid'].set_vector_parameter_value('Colour', u.LinearColor(1, .7, .3, 1) if warm else u.LinearColor(1, .97, .92, 1))
            GS['dot_mid'].set_scalar_parameter_value('Opacity', .95 if warm else .7)
    small = lambda a: max(a.get_actor_bounds(False)[1].to_tuple()) * 2 <= 80
    q = A.nearest() if not held and target is None else None
    if P.STATE.get('seated'):
        hint = 'Space  stand up'
    elif held:
        hint = ('Release  throw!' if GS.get('charge') is not None else
                ('F  equip    ' if small(GS['held']) else '') + 'Hold right click  throw    Let go  drop')
    elif target is not None:
        hint = 'Hold left click  pick up' + ('    then F  equip' if small(target) else '')
    elif A.S.get('held'):
        hint = 'Hold click  spray    E  put down'
    elif q:
        hint = 'E  ' + q.get('title', 'use')
    elif GS['hands']['R'] or GS['hands']['L']:
        hint = 'Right click  use    G  give    Q  toss    F  put away'
    else:
        hint = ''
    msg = A.S.get('message', '') if time.monotonic() < A.S.get('message_until', 0) else ''
    hud(hint, msg)


HUD_NAMES = ('P70 hud prompt', 'P70 hud prompt shadow', 'P70 hud message', 'P70 hud message shadow')
HUD = dict(actors=None, text={})


def hud_actors():
    if HUD['actors'] is None:
        found = {a.get_actor_label(): a for a in u.GameplayStatics.get_all_actors_of_class(P.STATE['world'], u.TextRenderActor)
                 if a.get_actor_label() in HUD_NAMES}
        HUD['actors'] = [found[n] for n in HUD_NAMES] if len(found) == len(HUD_NAMES) else False
        for a in HUD['actors'] or []:
            a.set_actor_enable_collision(False)
    return HUD['actors']


def hud(prompt, message):
    """Two short centred lines just under the crosshair: what you can do, then what just happened."""
    acts = hud_actors()
    if not acts:                                                        # no HUD actors in this level: the old print
        if prompt or message:
            u.SystemLibrary.print_string(P.STATE['world'], (message + '\n' if message else '') + prompt, True, False,
                                         u.LinearColor(1, .86, .55, 1), .05, u.Name('Gameplay66Hint'))
        return
    loc, rot = aim()
    f = u.MathLibrary.get_forward_vector(rot); r = u.MathLibrary.get_right_vector(rot); up = u.MathLibrary.get_up_vector(rot)
    face = u.MathLibrary.make_rot_from_xz(f * -1.0, up)
    base = loc + f * 30.0
    for i, (text, dy) in enumerate(((prompt, -2.25), (message, -3.45))):
        for j, a in enumerate(acts[2 * i:2 * i + 2]):
            if not text:
                a.set_actor_hidden_in_game(True); continue
            if HUD['text'].get(a.get_actor_label()) != text:
                a.text_render.set_text(text); HUD['text'][a.get_actor_label()] = text
            off = (r * .045 - up * .045 + f * .06) if j else u.Vector(0, 0, 0)          # j = 1: the drop shadow
            a.set_actor_location_and_rotation(base + up * dy + off, face, False, True)
            a.set_actor_hidden_in_game(False)


def hide_hud():
    for a in hud_actors() or []:
        a.set_actor_hidden_in_game(True)


def hide_dot():
    if GS.get('dot'):
        GS['dot'].static_mesh_component.set_hidden_in_game(True); GS['dot'] = None
    set_highlight(GS['aim'], False); GS['aim'] = None


# ---------------------------------------------------------------- tick

def tick(dt):
    if not active():
        if GS['held']:
            drop()
        head_reset()
        if GS.get('dot') or GS['aim'] is not None:
            hide_dot()
        if HUD['actors']:
            hide_hud()
        GS['was_off'] = True
        if GS['fov_sent'] and P is not None and P.STATE.get('pc'):
            u.SystemLibrary.execute_console_command(P.STATE['world'], 'fov 0', P.STATE['pc']); GS['fov_sent'] = 0.0
        return
    try:
        dt = min(dt, .05)
        GS['used'].clear()
        if not GS.get('props_known'):                                   # the Pass66 loose props, for the safety net
            GS['props_known'] = True
            for x in u.GameplayStatics.get_all_actors_of_class(P.STATE['world'], u.StaticMeshActor):
                if x.get_actor_label().startswith('Airport66 '):
                    remember(x)
        ensure_floor_wrap()
        if P.EYE_HEIGHT != PLAYER_EYE:
            P.EYE_HEIGHT = PLAYER_EYE
        if GS.pop('was_off', False) and not P.STATE.get('seated'):    # back from spectator / driving: no hovering
            GS.update(air=True, vz=0.0, surface=None, base=None, prev=None, hop=0.0)
        if not P.STATE.get('seated'):
            movement(dt)
            head(dt)
        else:
            head_reset()
        tether(dt)
        hands(dt)
        sit_anywhere()
        reactions()
        safety_net()
        crosshair(dt)
        GS['was_seated'] = bool(P.STATE.get('seated'))
    except Exception:
        GS['errors'] += 1
        err = traceback.format_exc()
        u.log_error('Gameplay66: ' + err)
        try:
            (A.R / 'ArtBible/Gameplay66Error.txt').write_text(err, encoding='utf-8')
        except Exception:
            pass
    finally:
        VIRTUAL['pressed'].clear()


def install(airport):
    global A, P
    A = airport; P = airport.P
    ensure_floor_wrap()
    if not getattr(A.nearest, '_g70', False):                          # Pass70: in play, pick-ups are held like
        original = A.nearest                                            # everything else (hold left click)

        def nearest():
            if not active():
                return original()
            keep = A.S['targets']
            A.S['targets'] = [q for q in keep if q.get('kind') != 'pickup']
            try:
                return original()
            finally:
                A.S['targets'] = keep
        nearest._g70 = True
        A.nearest = nearest
    GS['hl_mat'] = u.load_asset(HIGHLIGHT)
    u.log('GAMEPLAY66 INSTALLED')
