# Pass49: softer ceilings, real ground

Follow-on to `Pass48/MAKEOVER48.md`, from the player's feedback on it: the
straight oak baffles were "jarring" and "too longitudinal" in places, though
they "really work in some places", and changes should blend, not switch.

## Wave ceilings (`Pass48/survey48_probe.py`, `ceilings48_blender.py`, `Ceilings48.json`)
- The big rooms now have wave baffles. Every baffle's underside follows a
  long, soft swell (6-10 m), and the crests curve gently from line to line,
  so the ceiling reads as one rolling timber surface rather than hard
  parallel stripes: entrance foyer, check-in, security, repack, concourse,
  gate A07, gate A08, cafe approach, arrivals and both cafe ceilings
  (323 wave baffles; deepest 0.24-0.47 m, 0.55 m and 0.85 m in the cafe).
- The straight baffles stay where they lead you along a route: both long
  corridors, the A07 approach, the washroom passage, the arrivals exit and
  the forecourt canopy.
- Blends, not switches: every wave fades to the flat 150 mm baffle over
  the last 1.8-2.2 m before a room edge, so wave rooms and straight
  corridors meet at the same depth. Waves also flatten 0.25-1.2 m beside
  every light channel (the lights are not shadowed), and before every sign,
  rod or wall.
- Clearance is measured, not assumed: the survey now also traces every
  baffle line at the mid and full depth of its wave, and a wave only
  deepens where both traces were clear.

## Outside surfaces (`textures49_blender.py`, `surfaces49_editor.py`, `Surfaces49.json`)
New master `M_AP_Ground49`: a world-projected (tri-planar) finish, so it
needs no UVs, with a very soft 45-70 m variation on top so no map reads as
a repeat. The existing instances were re-parented in place and tinted from
their old colours, so the palette stays and each surface gains material:
- Lawns, airfield and field extension: mown turf with soft 4 m mowing
  stripes, clover and dry patches, a deeper natural green.
- Apron, forecourt slab, kerbs and runway shoulders: 5 m concrete bays with
  sealed joints, per-bay tone, aggregate and faint tyre staining.
- Runway, taxiway, access roads: dense asphalt with aggregate and patching.
- Roofs: light grey-green single-ply membrane with welded laps.

## Inside surfaces
- Plaster walls (both tones): soft limewash mottle on the same colours, so
  the large white walls are no longer flat.
- Cafe gallery deck, its stair and the check-in queue mat: the teal cloth
  is replaced with the Skyward gate carpet, matching the gates.

## Safety
All asset changes were backed up first (`Pass49/Backup/assets`), the level
before the ceiling import (`Pass48/Backup/L_Airport_Repair38.20261031-214410.umap.bak`).
Nothing added has collision.
