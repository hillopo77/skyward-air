# Pass50: tall halls, landscape, landmarks and a style pass

Approved by the player: Lumen, opening up the layout from a copy of the
shell, unifying the style, faster checks, and a restore point for the
Pass49 look.

## Restore point
- `SkywardAir/Snapshots/Save-Look.ps1 -Name <name>` mirrors the project's
  Content and Config; `Restore-Look.ps1 -Name <name>` puts one back (it saves
  the current state as `BeforeRestore-<time>` first, so a restore can be
  undone). Both refuse to run while Unreal is open.
- `Look49` is the Pass49 look (wave ceilings, textured ground, before the
  hall and Lumen): `Restore-Look.ps1 -Name Look49`.

## Faster checks
Measured: an editor change takes ~20 s and a photo run ~45 s; the slow parts
were the 8-minute journey test (run three times) and separate round trips.
- `Pass50/Check50.ps1` does change → photograph → contact sheet in one call
  (`-Editor <scripts> -Mutates -Views <names|all> -Out <dir>`); views come
  from `Pass48/AllViews51.json` and `Pass50/Views50.json`.
- The journey runs once per change; three times only at the end.

## The landside hall (`export50_editor.py`, `hall50_blender.py`, `reimport50_editor.py`, `Hall50.json`)
- The foyer, check-in and landside corridor were three low rooms (3.4-3.8 m)
  behind two partitions. They are now one 23 x 14 m hall, 6.6 m high.
- Built from the live meshes (exported from the project, since some FBX in
  `Exports/FBX` are not what the level uses), edited headless, re-imported
  into the same assets with their slots and collision restored; your open
  Blender master was not touched.
- Removed: both partitions and everything mounted on them (signs and
  lettering, arch and door trims, fixings, an oak slat panel, wall finish
  panels), the low ceilings and roofs over the hall.
- New (`SM_AP_P50Hall`): upper walls to a 7.25 m parapet with a band of
  clerestory windows (4.4-6.2 m, 1.6 m bays) on all four sides, an oak datum
  band where old wall meets new, the 6.6 m ceiling and roof, oak pilasters
  where the partitions met the outer walls, terrazzo infill where they stood,
  steel rods carrying the check-in headers up to the new ceiling, oak fins
  outside on every window pier.
- The 12 hall lights moved up to the new ceiling with 2.2x output; the five
  room grades in the hall blend over 4 m instead of switching at old walls.
- The rooftop plant units over the hall were lifted onto the new roof.
- One wave-baffle field over the whole hall (45 baffles, up to 0.75 m deep)
  with three light channels; the paper-plane Flock now hangs 3.6-4.7 m from
  the hall ceiling.

## Lighting: Lumen tried, not possible on this machine yet
- Lumen needs DirectX 12 in this engine. With DirectX 11 the setting is
  accepted but does nothing (a same-frame on/off test changed no pixels).
- DirectX 12 hangs this GPU: the NVIDIA driver (522.06) is on Unreal's deny
  list, and with the warning suppressed the game crashed with
  DXGI_ERROR_DEVICE_HUNG during start-up.
- So the renderer is exactly as it was (`Config/DefaultEngine.ini` restored
  from `Pass50/Backup/DefaultEngine.ini.pre50`) and every post-process volume
  has its Pass49 GI, reflection and AO settings back (`restoregi50_editor.py`,
  read from the level saved just before the Lumen step).
- To get Lumen: update the NVIDIA driver (Unreal suggests 591.86 or newer),
  then set `r.DynamicGlobalIlluminationMethod=1`, `r.ReflectionMethod=1` and
  `DefaultGraphicsRHI_DX12`; `lumen50_editor.py` clears the volume overrides.

## Style
- New tree (`SM_AP_P50Tree`, `style50_blender.py`): forked trunk, eleven soft
  lumpy foliage masses in two greens, replacing the lollipop trees.
- New car (`SM_AP_P50Car_<paint>`): one rounded bevelled body, tinted glass,
  painted roof, bumpers, lamps, wheels with hubs, in the seven car-park
  paints; the 38 box cars are now placed models at the same spots.

## More tall rooms (same pipeline, `Hall50.json` 'halls')
- Gate A08 (8 x 20 m) and gate A07 (9 x 13 m): 6.4 m, clerestory all round
  (A08's west band sits above the cafe roof), their gate screens' rods
  stretched to the new ceiling, wave ceilings with their light channels.
- Arrivals (8 x 10 m): 6.4 m with clerestory; ceilings and roofs are now cut
  exactly at each hall's edges, so the arrivals exit kept its ceiling.
- Concourse and corridors stay low on purpose: low corridor, tall room.
- Rooftop plant over all four halls lifted onto the new roofs (139 units).

## Landscape and landmarks (`ground50_probe.py`, `landmark50_blender.py`)
- 110 new trees: an avenue on both sides of the access road north and south
  of the terminal, and clusters on the south and north lawns, each planted at
  the ground height measured in the game (the north lawn falls 1.8 m).
- 'SKYWARD AIR' in gold capitals on the landside hall roof, facing the road,
  on a steel frame sized to the lettering.
- 'Departure': a 10 x 4 m reflecting pool on the south lawn with a 3.6 m gold
  paper plane climbing out of it, the Flock at landscape scale.

## Journey regression
- First run after the halls: 170/174, every journey flag true. The four
  failures were acceptance probes that the old architecture exists, all
  non-blocking: the arch between foyer and check-in, and three roof steps
  between foyer, check-in and the landside corridor. Those three rooms are
  now one hall, so the probes were retired from `Exports/airport_layout.json`
  (`repair38.retired50` records why; the old file is
  `Pass50/Backup/airport_layout.before50.json`). The roof-step probes at every
  other room boundary, the gates' included, still pass.
- After retiring them: three runs, 170/170 each, all five journey flags true
  (`Pass46/Backup/FlightJourney39_pass50m1..m3_*.json`).
- Restore points: `Look49` (before this pass) and `Look50` (this pass).
- The 'START HERE / CHECK-IN' sign that hung on the removed foyer wall now stands on two steel posts with a navy board (Hall50.json 'extras').

