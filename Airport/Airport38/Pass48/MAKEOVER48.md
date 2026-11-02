# Pass48: the makeover

Pass47 fixed defects. This pass changes what the airport looks like, inside
and out. Every piece below was measured before it was built (survey probes in
the running game), built headless in Blender from those measurements, placed
by an editor script that backs the level up first (`Backup/`), and checked in
the running game. Before/after sheets: `BeforeAfter/BA1..BA3`. Full set of 51
after-views: `Sweep3/` (contact sheets `sheet_0..2.png`).

## Sound
- The parked aircraft's APU drone is gone from the ambience mixer
  (`Pass47/ambience47.py`, installed). Room tone, crowd, outdoor and PA stay.

## Surfaces, whole terminal (`textures48_blender.py`, `surfaces48_editor.py`)
The existing finish instances were re-parented onto one new master
(`M_AP_Finish48`: texture, tint, roughness scale, emissive lift), so every
mesh already using them changed at once:
- Floors: polished terrazzo, ivory with five chip colours, brass divider
  strips on a 3 m grid.
- Gate lounges: Skyward carpet, deep navy with teal flight-path lines and
  gold waypoints.
- Washrooms: 50 mm sage/ivory mosaic.
- Lower walls (the old slate dado): light-oak board wainscot all round.
- Ceilings: bright smooth plaster with a slight lift.
- Oak trims: richer grain.

## Ceilings and lighting (`survey48_probe.py`, `ceilings48_blender.py`)
- Oak baffle ceilings in 16 spaces (foyer, check-in, both corridors,
  security, repack, concourse, both gates and the A07 approach, cafe approach,
  WC passage, arrivals, arrivals exit, the cafe's 4.4 m and 6.8 m ceilings)
  and under the forecourt canopy: 393 baffle runs, each cut to the free span
  the survey traced along its own line, so none touches a wall, sign or rod.
- The old dark box fittings are hidden; the rows the lights stand in are now
  continuous linear light channels in the baffles. Cafe: three large navy and
  gold drum pendants over the tables. Service rooms: flush linear lights.
- Bottom of every baffle sits above the light actors, so nothing shadows them.

## Feature pieces (`Walls48.json`, `features48_blender.py`, `mural48_blender.py`)
- Check-in: oak slat feature wall on navy, 'WHERE WILL YOU GO TODAY?' in gold.
- Concourse: 7 m living green wall, 4,200 leaves, oak frame.
- Entrance foyer: 'Flock', 28 hanging gold and ivory paper planes.
- Public return: 11.9 m 'WELCOME TO AZURE BAY' mural for arriving passengers.

## Outside (`exterior48_probe.py`, `exterior48_blender.py`)
- 75 vertical oak fins on every solid run of the landside, south and airside
  facades (glazing, doors and signs left clear by measurement).
- Oak slat soffit under the forecourt canopy with light channels.
- Car park opposite the forecourt: 52 bays, 38 parked cars, lamp posts,
  islands with trees, hedge, driveway, footpath and zebra crossing to the
  forecourt.
- Raised planting beds and a tree row along the south facade; navy totem
  sign at the car-park entrance; three flagpoles.
- Apron: baggage tug with three loaded carts, belt loader at the aft hold,
  fuel truck, two floodlight masts, all aft and east of the wing, clear of
  the taxi route and the tailplane sweep.

## Atmosphere (`grade48_editor.py`)
- Screen-space ambient occlusion raised (0.55, 110 cm) in the daylight grade
  and in all 22 room grades that overrode it with weaker values; soft bloom
  and light vignette. The renderer has no global illumination, so this is what
  gives corners and furniture their depth. Renderer settings untouched.

## Gameplay safety
Everything added has no collision; the old fittings had none either. Journey
regression results are recorded below.

Journey regression after the whole makeover: three runs, 174/174 each, all
five journey flags true (`Pass46/Backup/FlightJourney39_pass48m1..m3_*.json`).
