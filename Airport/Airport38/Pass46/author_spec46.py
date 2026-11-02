"""Pass46: author the improvement spec, offline, from measured evidence.

Three kinds of change, kept separate so each can be judged and reverted alone:

  place  - a new instance of an asset the project already owns, in a room the
           census found empty. No new art, so no new art risk, and it matches
           the established style by construction.
  move   - an existing actor relocated because its current position is a defect
           (a counter jammed against a shelf face, shelves backing onto glazing).
  vary   - yaw/scale variation on verbatim-repeated groups.

Every footprint below is checked against real asset bounds read from the FBX
exports, against the 1.9 m route_clear_width_m, against authored portals, and
against seated NPC anchors - a bench with a passenger sitting on it is never
moved, because the character placement would be left behind.

Writes Spec46.json. The engine script that consumes it re-checks every
placement against live geometry and refuses anything that overlaps.
"""
import json, math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
D = json.loads((ROOT / 'Airport/Airport38/Exports/airport_layout.json').read_text(encoding='utf-8'))
BOUNDS = json.loads((HERE / 'asset_bounds46.json').read_text(encoding='utf-8'))

ROUTE_CLEAR = D['prototype27']['route_clear_width_m']      # 1.9

place, move, vary = [], [], []


def P(room, asset, name, x, y, yaw=0.0, z=0.0, scale=None, why='', path=None):
    """One placement. `path` names the content folder for an asset that no
    actor in the level uses yet, so the engine script can load it directly
    instead of copying a mesh off an existing actor."""
    q = dict(room=room, asset=asset, name=name,
             location=[round(x, 3), round(y, 3), round(z, 3)],
             rotation_degrees=yaw, scale=scale or [1, 1, 1], why=why)
    if path:
        q['package'] = path + asset
    place.append(q)


# ---------------------------------------------------------------- concourse
# 108 m2 carrying two props: a camera and one plant. 75% of its floor is more
# than a stride from anything. Its south end (y -4..2) is a dead end - no
# portal pierces y=-4 - so it becomes a waiting alcove rather than more
# corridor, and the main route along y=6.5 is left clear.
R = 'concourse'
P(R, 'SM_AP_ScreenBoard', 'Concourse departures board46', -29.0, -3.88, 0, 2.15,
  why='dead-end south wall, faces north up the concourse at arriving passengers')
P(R, 'SM_AP_Bench34_Hardware40', 'Concourse alcove bench46 0', -30.55, -0.9, 90,
  why='alcove seating, facing its pair across 3.1 m')
P(R, 'SM_AP_Bench34_Hardware40', 'Concourse alcove bench46 1', -27.45, -0.9, -90,
  why='alcove seating, facing its pair')
P(R, 'SM_AP_Charging34', 'Concourse charging bar46', -31.62, 1.5, 90,
  why='west wall between the facade corner and the recovery portal at y 4.9')
P(R, 'SM_AP_Bins36', 'Concourse waste sorting46', -31.5, -3.4, 90,
  why='alcove corner; y=3.6 is taken by Plant1224_1772 at (-30.9, 4.0)')
P(R, 'SM_AP_Planter27', 'Concourse planter46 0', -26.5, 1.2, 90,
  why='east wall, marks the alcove mouth')
P(R, 'SM_AP_Information27', 'Concourse information totem46', -26.55, 11.9, 90,
  why='north decision node: cafe west, A08 north')
P(R, 'SM_AP_Plant12', 'Concourse plant46 0', -29.0, 1.2, 0,
  why='closes the north edge of the alcove; the west wall at y=11 falls inside the cafe portal mouth')
P(R, 'SM_AP_Recycling38', 'Concourse recycling46', -26.55, 9.0, 90,
  why='east wall below the existing A07 sign')

# ------------------------------------------------------------- cafe approach
# 36 m2, zero props, a pure threshold. Cafe_welcome already signs the west wall
# at y 11.6..14.6, so planting stays south of it rather than standing in it.
R = 'cafefoyer'
P(R, 'SM_AP_Planter27', 'Cafe approach planter46 0', -37.3, 15.4, 0,
  why='west of the cafe threshold mouth, which spans x -36.3..-32.7')
P(R, 'SM_AP_Bench27_Hardware40', 'Cafe approach bench46', -35.4, 10.45, 0,
  why='south wall, a pause before the cafe')
P(R, 'SM_AP_Bins36', 'Cafe approach waste sorting46', -37.4, 10.5, 0,
  why='south-west corner, clear of the welcome sign above y 11.6')
P(R, 'SM_AP_Plant12', 'Cafe approach plant46', -33.6, 10.7, 0,
  why='south-east corner; against the west wall it would stand in the welcome sign')

# --------------------------------------------------------------- WC passage
# 33 m2, zero props. 3 m wide, so only 1.1 m of slack outside the 1.9 m route;
# everything here hugs a wall.
R = 'amenitylobby'
P(R, 'SM_AP_Bench27_Hardware40', 'WC passage bench46', -25.62, -6.2, 90,
  why='west wall waiting bench, 2.28 m left clear')
P(R, 'SM_AP_Plant12', 'WC passage plant46', -23.48, -4.6, 0,
  why='east wall, opposite the bench')
P(R, 'SM_AP_Recycling38', 'WC passage recycling46', -23.3, -10.8, 90,
  why='south end of the passage')
P(R, 'SM_AP_Planter27', 'WC passage planter46', -25.5, -11.4, 0,
  why='closes the dead south corner')

# ---------------------------------------------------------- landside corridor
# 92 m2 with four props. The blue route runs along y=-6, so the two 1 m strips
# against y=-8 and y=-4 are free.
R = 'landsidecorridor'
P(R, 'SM_AP_ScreenBoard', 'Landside departures board46', -39.0, -7.9, 0, 2.15,
  why='south wall facing the corridor, between check-in and security')
P(R, 'SM_AP_Bench29_Hardware40', 'Landside corridor bench46 0', -34.8, -7.6, 0,
  why='south wall, clear of the board')
P(R, 'SM_AP_Bench29_Hardware40', 'Landside corridor bench46 1', -46.0, -7.6, 0,
  why='south wall, west end')
P(R, 'SM_AP_Charging34', 'Landside charging bar46', -37.0, -4.38, 0,
  why='north wall, clear of the security portal at x -43.2..-40.8')
P(R, 'SM_AP_Planter27', 'Landside planter46 1', -44.0, -4.5, 0, why='north wall')
P(R, 'SM_AP_Planter27', 'Landside planter46 2', -28.6, -4.5, 0,
  why='north wall, east end, clear of Safety station 1 at (-26.7, -5.0)')
P(R, 'SM_AP_Bins36', 'Landside waste sorting46', -27.6, -7.5, 0,
  why='east end, clear of the check-in threshold mouth x -31.5..-28.5')

# ----------------------------------------------------------------- arrivals
# 80 m2 with four props, and a 9.7 m carousel dominating it.
R = 'arrivals'
P(R, 'SM_AP_ScreenBoard', 'Arrivals reclaim board46', -18.0, -12.12, 0, 2.15,
  why='north wall at y=-12, facing the carousel; x=-14 is glazed')
P(R, 'SM_AP_Trolley', 'Arrivals trolley rank46 0', -20.8, -20.2, 0, why='trolley rank by the exit')
P(R, 'SM_AP_Trolley', 'Arrivals trolley rank46 1', -20.0, -20.2, 0, why='trolley rank by the exit')
P(R, 'SM_AP_Trolley', 'Arrivals trolley rank46 2', -19.2, -20.2, 0, why='trolley rank by the exit')
P(R, 'SM_AP_Bench34_Hardware40', 'Arrivals bench46', -21.0, -13.2, 90, why='west wall, meeting seat')
P(R, 'SM_AP_Planter27', 'Arrivals planter46 0', -20.6, -21.3, 0,
  why='south-west, clear of the arrivals-exit portal mouth')
P(R, 'SM_AP_Planter27', 'Arrivals planter46 1', -14.6, -21.3, 0, why='south-east corner')
P(R, 'SM_AP_Bins36', 'Arrivals waste sorting46', -14.7, -13.0, 90, why='north-east corner')
P(R, 'SM_AP_Recycling38', 'Arrivals recycling46', -16.5, -12.5, 0, why='north wall, under the board')

# ------------------------------------------------------------ arrivals exit
# 10 m2 vestibule, zero props, with a portal on each side at y=-20, so the
# 1.9 m route band y -20.95..-19.05 must stay clear.
R = 'arrivalsreturn'
P(R, 'SM_AP_Bins36', 'Arrivals exit waste sorting46', -23.5, -21.5, 0,
  why='the one spot clear of both portal mouths; two planters were dropped because '
      'a 3x3.5 m vestibule with an opening on each side has no room for them')

# --------------------------------------------------------- baggage handling
# NOT furnished. The authored census read 0 props because this room's
# contents are centred just outside its rect or are union actors; the live
# inventory shows Bag receiving bed38 01/02, a 2.09 x 3.08 x 1.37 m
# Baggage handling fitted details38, a service door and a 5 m backdrop in a
# 4 x 6.5 m room. It is full. The first apply run rejected all five
# placements here for exactly that, which is the live re-check doing its job.

# ---------------------------------------------------------------- operations
R = 'operations'
P(R, 'SM_AP_StaffStorage38', 'Operations storage46 0', -48.2, 15.6, 0,
  why='north wall racking; RetailShelf24_1814 already holds the west wall')
P(R, 'SM_AP_StaffStorage38', 'Operations storage46 1', -43.0, 15.6, 0,
  why='north wall racking')
P(R, 'SM_AP_CafeTable34', 'Operations break table46', -40.5, 14.5, 0, why='staff break table')
P(R, 'SM_AP_CafeChair34_Hardware40', 'Operations break chair46 0', -40.5, 13.65, 180, why='break seat')
P(R, 'SM_AP_CafeChair34_Hardware40', 'Operations break chair46 1', -40.5, 15.35, 0, why='break seat')
P(R, 'SM_AP_Plant12', 'Operations plant46', -39.0, 10.8, 0, why='south-east corner')
P(R, 'SM_AP_Recycling38', 'Operations recycling46', -47.0, 10.6, 0, why='south wall')
P(R, 'SM_AP_Bins36', 'Operations waste sorting46', -48.4, 11.0, 90, why='west wall, south of RetailShelf24_1814')

# -------------------------------------------------------------- gate07 entry
R = 'gate07entry'
P(R, 'SM_AP_Bench34_Hardware40', 'A07 entry bench46 0', -25.5, 8.8, 90,
  why='west wall, north of the main route along y=6.5')
P(R, 'SM_AP_Bench34_Hardware40', 'A07 entry bench46 1', -23.5, 8.8, -90,
  why='east wall, north of the main route along y=6.5')
P(R, 'SM_AP_Planter27', 'A07 entry planter46 0', -25.5, 0.2, 0, why='flanks the south threshold')
P(R, 'SM_AP_Planter27', 'A07 entry planter46 1', -23.5, 0.2, 0, why='flanks the south threshold')
P(R, 'SM_AP_Recycling38', 'A07 entry recycling46', -24.5, 9.6, 0, why='north wall, between the benches')

# ------------------------------------------------------- public arrivals return
R = 'publicreturn'
P(R, 'SM_AP_Bench27_Hardware40', 'Public return bench46 0', -44.0, -21.4, 0,
  why='south wall, between the existing trolleys at x=-46 and x=-42')
P(R, 'SM_AP_Bench27_Hardware40', 'Public return bench46 1', -31.5, -21.4, 0,
  why='south wall, east of the trolley at x=-34')
P(R, 'SM_AP_Planter27', 'Public return planter46 0', -40.0, -18.6, 0, why='north wall rhythm')
P(R, 'SM_AP_Planter27', 'Public return planter46 1', -29.0, -18.6, 0, why='north wall rhythm')
P(R, 'SM_AP_Trolley', 'Public return trolley46 0', -47.5, -19.0, 0, why='trolley return by the exit')
P(R, 'SM_AP_Trolley', 'Public return trolley46 1', -46.7, -19.0, 0, why='trolley return by the exit')
P(R, 'SM_AP_Bins36', 'Public return waste sorting46', -36.0, -18.6, 0, why='north wall')

# -------------------------------------------------------------- gallery remake
# The upstairs gallery deck is x -49..-41, y 25..34 at z 3.15, 72 m2, holding
# eight items. Two measured defects:
#   1. ChargingTable24_1797 spans y 32.68..33.33 and RetailShelf24_1832 starts
#      at y 33.33 - the counter is flush against the face of a 2.46 m shelf,
#      so neither can be used.
#   2. All three shelves sit at y=33.6, 0.4 m from the y=34 glazing, showing
#      their backs to the only view in the room.
# Both benches carry a seated NPC anchor, so neither bench moves.
R = 'cafe'
move.append(dict(actor='ChargingTable24_1797', to=[-48.4, 27.2, 3.15], yaw=90,
                 why='becomes a window counter facing the west glazing at the stair '
                     'head, instead of blocking the retail shelf face'))
for i, (name, x, y, yaw) in enumerate([
        # yaw 0 puts a unit's FRONT at -y: that is how the originals stood,
        # fronts to the room at y=33.6 with the glazing behind them. Back to
        # back therefore needs the NORTH unit at 180 and the SOUTH unit at 0.
        # The first run had these swapped, which pointed both fronts inward at
        # each other and both backs out at the room - worse than the defect.
        ('RetailShelf24_1832', -43.4, 31.6, 180),
        ('RetailShelf24_1833', -43.4, 31.06, 0),
        ('RetailShelf24_1834', -44.7, 31.2, 90)]):
    move.append(dict(actor=name, to=[x, y, 3.15], yaw=yaw,
                     why='back-to-back gondola island with an end cap, so the backs '
                         'face each other instead of the glazing, and 2.1 m of '
                         'walkway opens behind it'))
P(R, 'SM_AP_OvalTable36', 'Gallery table46 0', -46.5, 28.6, 0, 3.15,
  why='the gallery had no table at all; seats face each other across it')
# every gallery item is marked no-snap below
P(R, 'SM_AP_CafeChair34_Hardware40', 'Gallery chair46 0', -46.5, 27.75, 180, 3.15, why='serves table46 0')
P(R, 'SM_AP_CafeChair34_Hardware40', 'Gallery chair46 1', -46.5, 29.45, 0, 3.15, why='serves table46 0')
P(R, 'SM_AP_OvalTable36', 'Gallery table46 1', -43.5, 26.6, 0, 3.15, why='second gallery table')
P(R, 'SM_AP_CafeChair34_Hardware40', 'Gallery chair46 2', -43.5, 25.75, 180, 3.15, why='serves table46 1')
P(R, 'SM_AP_CafeChair34_Hardware40', 'Gallery chair46 3', -43.5, 27.45, 0, 3.15, why='serves table46 1')
P(R, 'SM_AP_Planter27', 'Gallery planter46', -48.3, 33.2, 0, 3.15,
  why='softens the glazed north-west corner the charging bar vacated')

# ---------------------------------------------------------------- forecourt
# The player starts at (-50.9, -12.5) and walks east to the entrance. The live
# inventory finds FOUR actors in the whole forecourt: a character collision
# proxy, Slab12_1, the Canopy38 shelter and one asphalt slab. The authored
# layout asks for 23 curbs, 4 trees, 4 garden benches, 4 streetlights, 3 taxis
# and a shuttle bus; none of them is in the level. They are not on
# repair38.forbidden_architecture_assets and not in
# architecture_removed_asset_ids, so they were dropped as instances rather than
# banned, and all eight meshes still exist under /Game/Airport10/Meshes.
#
# This places them with variation built in, rather than restoring the verbatim
# 4x repeat the layout describes. The canopy occupies x -61..-52.95,
# y -21..-3.5, up to z 3.85, so nothing tall goes under it: an 8.5 m tree or a
# 5.8 m streetlight there would pierce the shelter roof.
R = 'forecourt'
CANOPY_Y = (-21.0, -3.5)
AP10 = '/Game/Airport10/Meshes/'

# Kerb line between the road and the walkway. A kerb repeats by nature.
for i in range(23):
    y = -24.0 + i * 2.0
    P(R, 'SM_AP_Curb', 'Forecourt kerb46 %02d' % i, -61.8, y, 90,
      why='kerb run between the asphalt at x<-62 and the walkway', path=AP10)

# Streetlights, 5.8 m, so clear of the 3.85 m canopy. Alternating arm direction.
for i, (y, yaw) in enumerate([(-23.0, 0.0), (4.8, 180.0), (14.0, 0.0),
                              (22.0, 180.0)]):
    P(R, 'SM_AP_Streetlight', 'Forecourt streetlight46 %d' % i, -60.4, y, yaw,
      why='outside the canopy footprint; arm direction alternates along the row',
      path=AP10)

# Trees, 6.8 m before scale, so north of the canopy only. Varied yaw and scale.
for i, (x, y, yaw, sc) in enumerate([(-55.0, 1.0, 14.0, 1.25),
                                     (-54.4, 9.5, -37.0, 1.12),
                                     (-54.8, 18.0, 61.0, 1.19)]):
    P(R, 'SM_AP_Tree', 'Forecourt tree46 %d' % i, x, y, yaw,
      scale=[sc, sc, sc], path=AP10,
      why='north of the canopy; yaw, scale and offset differ per tree so the '
          'row is not a stamped array')

# Garden benches, sheltered under the canopy, alternating facing.
for i, (y, yaw) in enumerate([(-18.0, 90.0), (-12.25, -90.0), (-6.5, 90.0)]):
    P(R, 'SM_AP_GardenBench', 'Forecourt garden bench46 %d' % i, -55.7, y, yaw,
      why='sheltered seating under the canopy, facing alternately', path=AP10)

# Taxis on the asphalt, slight yaw differences so they are not a rigid rank.
for i, (y, yaw) in enumerate([(-19.0, 0.0), (-6.0, 2.5), (8.0, -3.0)]):
    P(R, 'SM_AP_TaxiCar', 'Forecourt taxi46 %d' % i, -64.5, y, yaw,
      why='drop-off rank on the asphalt road', path=AP10)

P(R, 'SM_AP_ShuttleBus', 'Forecourt shuttle bus46', -66.0, 23.0, 0,
  why='the layout asks for a shuttle bus; it is absent from the level', path=AP10)

# The twelve cafe chairs are one asset at one scale. A small yaw jitter reads as
# chairs that people have actually moved. Seated NPC anchors sit at the TABLE
# centres, not the chair centres, so a few degrees of chair yaw is safe;
# positions are left exactly as authored.
CHAIR_JITTER = {
    'CafeChair24_1783': -7.0, 'CafeChair24_1784': 5.0, 'CafeChair24_1786': 11.0,
    'CafeChair24_1787': -4.0, 'CafeChair24_1789': 6.0, 'CafeChair24_1790': -9.0,
    'CafeChair24_1792': -6.0, 'CafeChair24_1793': 8.0,
    'Cafe extra chair36 0': 4.0, 'Cafe extra chair36 1': -5.0,
    'Cafe extra chair36 2': 9.0, 'Cafe extra chair36 3': -7.0}
BASE_YAW = {
    'CafeChair24_1783': 180.0, 'CafeChair24_1784': 0.0, 'CafeChair24_1786': 180.0,
    'CafeChair24_1787': 0.0, 'CafeChair24_1789': 180.0, 'CafeChair24_1790': 0.0,
    'CafeChair24_1792': 180.0, 'CafeChair24_1793': 0.0,
    'Cafe extra chair36 0': 90.0, 'Cafe extra chair36 1': -90.0,
    'Cafe extra chair36 2': 180.0, 'Cafe extra chair36 3': 0.0}
for actor, dj in CHAIR_JITTER.items():
    vary.append(dict(actor=actor, to=None, yaw=BASE_YAW[actor] + dj,
                     scale=[1, 1, 1], skip_overlap=True,
                     why='twelve identical chairs at identical yaw; jitter only, '
                         'position unchanged so seated anchors still line up'))

# ------------------------------------------------- lavatory release plates
# Measured from the live inventory, not from a capture:
#   Terminal WC 0 (SM_AP_CubicleDoor) centre (-21.019, -7.204), extent
#   [55.9, 9.2, 105.0] cm, so its faces are at y = -7.296 and y = -7.112.
#   WC release 0 outside at y=-7.325 spans y -7.355..-7.295 and meets the south
#   face within 1 mm. Correct.
#   WC release 0 inside at y=-6.775 spans y -6.805..-6.745, which leaves it
#   30.7 cm clear of the door's inner face, hanging in the cubicle.
# Reseat each inside plate flush to the inner face, penetrating 1 mm, which is
# the mount_penetration_m the project already uses for fitted relief.
INNER_FACE_Y = -7.112
PLATE_HALF_DEPTH = 0.030
PENETRATION = 0.001
for actor, x in (('WC release 0 inside', -20.55), ('WC release 1 inside', -16.65)):
    move.append(dict(
        actor=actor, to=[x, INNER_FACE_Y + PLATE_HALF_DEPTH - PENETRATION, 1.13],
        yaw=None, snap=False,
        why='hung 30.7 cm clear of the cubicle door inner face; the matching '
            'outside plate meets its face within 1 mm. Reseated flush, 1 mm in.'))

# ------------------------------------------------------- walk-through solids
# The inventory found 95 visible, prop-sized actors with collision disabled.
# Most are correct: floor decals, fabric curtains, thin queue tape, aircraft
# control surfaces inside the wing envelope, and the union actors that
# flow39.py:552 registers as 'none' on purpose.
#
# Decorative planting is not. Ten plant and planter actors, up to 1.19 m tall,
# stand in rooms the player walks through and can be walked straight through.
#
# Deliberately NOT changed here: the two X-ray scanners, six queue posts and
# four stanchions. They are also walk-through and also wrong, but they sit in
# the security and check-in lanes that the 166/167 journey test walks, and
# making them solid could block that route. They are logged as P46-015 for a
# pass that can re-run the journey against each change on its own.
collide = []
for i, actor in enumerate([
        'Plant1224_1761', 'Plant1224_1771', 'Plant1224_1772', 'Plant1224_1773',
        'Plant1224_1827', 'Plant1224_1828', 'Plant1224_1829',
        'Plant1224_1824', 'Plant1224_1825', 'Plant1224_1826']):
    collide.append(dict(actor=actor, profile='BlockAll',
                        why='visible 1.1-1.2 m planting with collision disabled; '
                            'the player walks through it'))

def spec_place_gallery_guard(rows):
    return [q for q in rows if q['location'][2] > 1.0]


spec = dict(
    revision=46,
    route_clear_width_m=ROUTE_CLEAR,
    rules=['place = new instance of an asset the project already owns',
           'move = existing actor relocated because its position is a measured defect',
           'vary = yaw/scale variation on verbatim-repeated groups',
           'no bench carrying a seated NPC anchor is moved',
           'collide = collision enabled on a visible solid that had none',
           'the engine script re-checks every placement against live geometry'],
    place=place, move=move, vary=vary, collide=collide)
# The gallery deck has no collision, so a floor snap would drop these into the
# cafe. Mark every item standing on it, placed or moved, as no-snap.
for q in spec_place_gallery_guard(place):
    q['snap'] = False
for m in move:
    if m.get('actor', '').startswith(('RetailShelf24_', 'ChargingTable24_1797')):
        m['snap'] = False
        m['to'][2] = 3.15
(HERE / 'Spec46.json').write_text(json.dumps(spec, indent=1), encoding='utf-8')

print('place %d, move %d, vary %d, collide %d'
      % (len(place), len(move), len(vary), len(collide)))
rooms = {}
for q in place:
    rooms[q['room']] = rooms.get(q['room'], 0) + 1
for r, n in sorted(rooms.items(), key=lambda kv: -kv[1]):
    print('  %-20s +%d' % (r, n))
missing = sorted({q['asset'] for q in place} - set(BOUNDS))
print('assets with no measured bounds: %s' % (missing or 'none'))
