"""Pass47 terminal ambience: four looping 2D sounds mixed by where you stand.

Until Pass47 the game had interaction blips and flight sounds and nothing
else: the terminal was silent between beeps. These loops (made locally by
audio47_blender.py; the announcer is Windows' offline speech) fill it in:

  room     interior air-handling hush
  murmur   distant crowd, scaled by how busy each room is
  outdoor  breeze over distant road rumble
  pa       chime and announcement every 30 s, heard indoors

The parked aircraft's APU drone ('apron', Apron47) was dropped at the
player's request: it read as an unpleasant engine whine at the gates and
outside. The asset stays in the project, unused.

Each loop is spawned once as a 2D component and only its volume changes, so
it costs almost nothing per frame. Targets are set from the player's position
every 0.1 s and every volume glides toward its target, so moving between a
room, the forecourt and the apron crossfades instead of switching.

Returns at once under -NoSound (all QA runs use it). Never raises into the
game: any failure is logged and the game plays on silently as before.
"""
import time
import unreal as u

G = None
S = dict(status='not started', volumes={}, targets={}, context=None)
ASSETS = dict(room='RoomTone47', murmur='Murmur47', outdoor='Outdoor47', pa='PA47')
PATH = '/Game/Airport38/Pass47/Audio/'

# How busy each room sounds, 0..1.
CROWD = dict(checkin=1.0, cafe=1.0, concourse=0.9, security=0.8, gate07=0.8,
             gate08=0.8, entrancefoyer=0.7, cafefoyer=0.7, arrivals=0.6,
             gate07entry=0.6, landsidecorridor=0.5, recovery=0.5,
             publicreturn=0.4, arrivalsreturn=0.4, publicreturneast=0.3,
             amenitylobby=0.3, amenities=0.2, operations=0.15,
             baggageservice=0.1)
AIRCRAFT = (13.4, 18.6, -5.6, 35.4)          # cabin and flight deck, source metres
GLIDE = 1.4                                   # per second


def _zone(x, y):
    for z in G.D['zones']:
        x0, x1, y0, y1 = z['rect']
        if x0 <= x <= x1 and y0 <= y <= y1:
            return z['id']
    return None


def _targets(p):
    x, y, z = p
    if AIRCRAFT[0] <= x <= AIRCRAFT[1] and AIRCRAFT[2] <= y <= AIRCRAFT[3] and z < 4.5:
        return 'aircraft', dict(room=0.12, murmur=0.0, outdoor=0.0, pa=0.0)
    zone = _zone(x, y)
    if zone:
        return zone, dict(room=0.55, murmur=0.75 * CROWD.get(zone, 0.4), outdoor=0.05, pa=0.7)
    if x < -49.0:
        return 'landside', dict(room=0.0, murmur=0.06, outdoor=0.8, pa=0.12)
    return 'airside', dict(room=0.0, murmur=0.0, outdoor=0.7, pa=0.05)


def tick(dt):
    try:
        now = time.monotonic()
        if now - S.get('last', 0) < 0.1:
            return
        step = (now - S.get('last', now)) or 0.1
        S['last'] = now
        p = list(G.source(G.P.STATE['pawn'].get_actor_location()))
        ctx, tgt = _targets(p)
        S['context'], S['targets'] = ctx, tgt
        k = min(1.0, step * GLIDE)
        for name, comp in S['comps'].items():
            v = S['volumes'].get(name, 0.0)
            v += (tgt[name] - v) * k
            S['volumes'][name] = v
            comp.set_volume_multiplier(max(0.0001, v))
    except Exception as exc:
        S['status'] = 'stopped: ' + str(exc)[:160]
        try:
            u.unregister_slate_post_tick_callback(S['handle'])
        except Exception:
            pass


def start(game):
    global G
    G = game
    if '-nosound' in G.CMD.lower():
        S['status'] = 'disabled under -NoSound'
        return
    spawn = next((getattr(u.GameplayStatics, n) for n in ('spawn_sound2d', 'spawn_sound_2d')
                  if hasattr(u.GameplayStatics, n)), None)
    if spawn is None:
        S['status'] = 'no 2D sound API'
        return
    S['comps'] = {}
    for name, asset in ASSETS.items():
        wave = u.load_asset(PATH + asset)
        if wave is None:
            S['status'] = 'missing ' + asset
            return
        comp = spawn(G.P.STATE['world'], wave, 0.0001, 1.0, 0.0, None, False, False)
        if comp is None:
            S['status'] = 'no audio device'
            return
        S['comps'][name] = comp
        S['volumes'][name] = 0.0
    S['handle'] = u.register_slate_post_tick_callback(tick)
    S['status'] = 'playing'
