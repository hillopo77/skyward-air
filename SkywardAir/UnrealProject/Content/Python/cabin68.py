"""Cabin68: inside the aircraft, the light comes from the cabin's fittings, not the sky (Airport38 Pass68).

The terminal's sky light is stationary: its shadowing is baked, so it only
reaches indoors through windows. The aircraft flies, so it is movable and was
never part of that bake: to the sky light the whole cabin interior is open
air, and every surface got the same flat glow from no visible source. A
show-flag test (Pass51/Look/LX68) confirmed it: with the sky light off the
cabin is lit from its fittings; turning off baked bounce changes nothing.

While the camera is inside the cabin, the sky light fades to SKY_INSIDE of its
level (about 0.4 s, so walking through the door is not a switch), and back
outside, and the 'P69 cabin grade' post-process volume (bloom, soft ambient
occlusion) fades in with it. The cabin box is found from the 'Cabin broad practical' lights, which
fly with the aircraft, so this holds at the gate and in flight. Runs in every
-AirportRepair38 session, including captures, so photos show what the player sees.
"""
import unreal as u, time, math

SKY_INSIDE = .1
S = dict(sky=None, base=None, level=1.0, box=None, next_box=0.0, failed=False, grade=None)


def cabin_box(world):
    """UE-space box (min, max) around the cabin, from its ceiling practicals."""
    ps = [a.get_actor_location() for a in u.GameplayStatics.get_all_actors_of_class(world, u.RectLight)
          if a.get_actor_label().startswith('Cabin broad practical')]
    if len(ps) < 4:
        return None
    lo = u.Vector(min(p.x for p in ps) - 150, min(p.y for p in ps) - 450, min(p.z for p in ps) - 290)
    hi = u.Vector(max(p.x for p in ps) + 150, max(p.y for p in ps) + 820, max(p.z for p in ps) + 80)   # Pass70: + the flight deck
    return lo, hi


PANEL_PREFIX = 'PSU '                                               # Pass70: the economy passenger service units


def lived_in(airport):
    """Pass70: the player wanted the controls above the economy seats gone. cabin70_editor.py hides the
    panels in the level; here, once the plane's controls exist, their interactions (reading light, air
    vent, crew call) leave the plane's item list, so no prompt floats where a panel used to be."""
    P = airport.P
    if S.get('lived') or not P.STATE.get('configured') or not P.STATE.get('items'):
        return
    S['lived'] = True
    P.STATE['items'] = [q for q in P.STATE['items'] if not str(q.get('actor', '')).startswith(PANEL_PREFIX)]
    for name in [n for n in P.STATE.get('controls', {}) if n.startswith(PANEL_PREFIX)]:
        P.STATE['controls'].pop(name, None)


# ---------------------------------------------------------------- Pass72: panic
# Panic in the plane = a rejected takeoff (the cockpit's 'Reject takeoff / brake' emergency button: airport_flight39
# sets S['abort'] until the aircraft has stopped), or S['force_panic'] (photos: `py import cabin68;cabin68.S['force_panic']=True`).
# Then the red panic line at the ceiling pulses on and floods the cabin red, the floor path lights drop to a lower,
# cooler white, and the under-bin lights dim. It fades in fast and out slowly.
P72 = dict(ready=False, level=0.0, t=0.0)
PANIC_HZ = 1.6


def panic_wanted():
    import sys
    flight = sys.modules.get('airport_flight39')
    return bool(S.get('force_panic')) or bool(flight and getattr(flight, 'S', {}).get('abort'))


def panic_setup(world):
    P72.update(ready=True, strips=[], lights=[], floor=[], halos=[], bins=[], under=[])
    for a in u.GameplayStatics.get_all_actors_of_class(world, u.Actor):
        lab = a.get_actor_label()
        if lab.startswith('P72 cabin panic strip'):
            P72['strips'].append(a.static_mesh_component.create_dynamic_material_instance(0))
        elif lab.startswith('P72 cabin panic light'):
            c = a.get_component_by_class(u.RectLightComponent)              # same brightness per metre on every aisle
            P72['lights'].append((c, max(1.0, c.get_editor_property('source_width') / 580.0)))
        elif lab.startswith('P66 cabin floor diffuser'):
            P72['floor'].append(a.static_mesh_component.create_dynamic_material_instance(0))
        elif lab.startswith('P72 cabin floor glow'):
            c = a.get_component_by_class(u.RectLightComponent); P72['halos'].append((c, c.intensity))
        elif lab.startswith('P70 cabin bin glow'):
            P72['bins'].append(a.static_mesh_component.create_dynamic_material_instance(0))
        elif lab.startswith('Cabin broad practical'):
            c = a.get_component_by_class(u.RectLightComponent); P72['under'].append((c, c.intensity))


def panic_tick(world, dt):
    if not P72['ready']:
        panic_setup(world)
    want = 1.0 if panic_wanted() else 0.0
    if want == 0.0 and P72['level'] == 0.0:
        return
    P72['level'] += (want - P72['level']) * min(1.0, dt * (5.0 if want > P72['level'] else 1.2))
    if want == 0.0 and P72['level'] < .01:
        P72['level'] = 0.0                                                    # one last pass below sets everything back
    if S.get('force_panic') == 'photo':                                        # captures: full panic at a fixed phase
        P72['level'] = 1.0; P72['t'] = .25 / PANIC_HZ
    k = P72['level']; P72['t'] += dt if S.get('force_panic') != 'photo' else 0.0
    pulse = .35 + .65 * math.sin(math.pi * PANIC_HZ * P72['t']) ** 2            # panicky
    red = min(1.0, k * 3.0)                                                   # dormant grey glass until it lights
    for m in P72['strips']:
        m.set_vector_parameter_value('BaseColor', u.LinearColor(.12 + .88 * red, .12 - .06 * red, .13 - .09 * red, 1))
        m.set_scalar_parameter_value('Emission', 320.0 * k * pulse)
    for c, length in P72['lights']:
        c.set_intensity(9000.0 * length * k * pulse)
    for m in P72['floor']:                                                    # warm 260 -> a lower, cooler white 110
        m.set_vector_parameter_value('BaseColor', u.LinearColor(1.0, .86 + .1 * k, .64 + .3 * k, 1))
        m.set_scalar_parameter_value('Emission', 260.0 - 150.0 * k)
    for c, base in P72['halos']:
        c.set_intensity(base * (1 - .5 * k))
    for c, base in P72['under']:
        c.set_intensity(base * (1 - .7 * k))
    for m in P72['bins']:
        m.set_scalar_parameter_value('Emission', 150.0 * (1 - .7 * k))


def tick(airport, dt):
    if S['failed']:
        return
    try:
        lived_in(airport)
    except Exception:                                               # never let the details take the cabin light down
        S['lived'] = True
        import traceback
        u.log_error('Cabin68 lived_in: ' + traceback.format_exc())
    try:
        if not P72.get('broken'):
            panic_tick(airport.P.STATE['world'], dt)
    except Exception:
        P72['broken'] = True
        import traceback
        u.log_error('Cabin68 panic: ' + traceback.format_exc())
    try:
        world, pc = airport.P.STATE['world'], airport.P.STATE['pc']
        if S['sky'] is None:
            skies = u.GameplayStatics.get_all_actors_of_class(world, u.SkyLight)
            if not skies:
                S['failed'] = True; return
            S['sky'] = skies[0].light_component
            S['base'] = S['sky'].get_editor_property('intensity')
            S['grade'] = next((v for v in u.GameplayStatics.get_all_actors_of_class(world, u.PostProcessVolume)
                               if v.get_actor_label() == 'P69 cabin grade'), False)      # Pass69: bloom + soft AO aboard
        now = time.monotonic()
        if now >= S['next_box']:                                    # the aircraft moves: refresh twice a second
            S['box'] = cabin_box(world); S['next_box'] = now + .5
        box = S['box']
        c = pc.player_camera_manager.get_camera_location()
        inside = bool(box) and box[0].x <= c.x <= box[1].x and box[0].y <= c.y <= box[1].y and box[0].z <= c.z <= box[1].z
        goal = SKY_INSIDE * (1.0 - .8 * P72['level']) if inside else 1.0     # Pass72: a panic darkens the cabin too
        level = S['level'] + (goal - S['level']) * min(1.0, dt * 8)
        if abs(level - goal) < .002:
            level = goal
        if level != S['level']:
            S['level'] = level
            S['sky'].set_intensity(S['base'] * level)
            if S['grade']:
                S['grade'].set_editor_property('blend_weight', (1.0 - level) / (1.0 - SKY_INSIDE))
    except Exception:
        S['failed'] = True
        import traceback
        u.log_error('Cabin68: ' + traceback.format_exc())
