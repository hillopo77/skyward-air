# Pass 46 — the whole-map improvement pass, measured

Written 2026-10-30, continuing from Pass45. This pass answers "how could the
rooms be better" with numbers instead of impressions, and it corrects three
claims I made in Pass45 from screenshots that the data does not support.

Everything here is derived from the authored layout
(`Airport38/Exports/airport_layout.json`, revision 38) and from real asset
bounds read out of the exported FBX with the project's own binary FBX reader
(`Exterior39/read_fbx39.py`) — 413 assets measured, no guessed footprints. All
of it ran while the game was open, because none of it touches the engine.

---

## 0. Three corrections to Pass45

I reported these to the user from captures. Two were wrong and one was
overstated. Recording them because the handoff asks that agent judgment be
distinguished from established fact, and because a wrong improvement brief
leads to building the wrong thing.

### Correction 1 — "the walls are blank" is wrong. The walls are finished.

My first pass measured bare wall by looking for authored objects near each wall
face, and found 50 of 94 interior faces with a bare run of 3 m or more, 1432 m²
in longest runs alone. That measurement ignored
`repair38.terminal_finish43_v1.wall_panels`: **298 cassette panels across 131
surfaces, 1423 m² of wall**, 26.5 mm thick with 18 mm shadow joints and a
2.45 m maximum panel width.

Folding those in, 31 faces still looked unpanelled. But `finish43._cladding`
excludes two categories deliberately:

- `_exterior_glazed()` skips curtain-wall faces, because they are glass with a
  view out. That accounts for the eight largest "bare" runs I found, including
  the two biggest: `gate08 y=-24` (20 m) and `cafe y=-49` (18 m at 6.8 m tall).
- its `public` set excludes `operations` and `baggageservice` as staff rooms.

After both exclusions, 10 faces remained. **Every one of those 10 is a door
opening or the baggage service wall**, which `_baggage()` handles separately:

| face | gap | what it actually is |
|---|---|---|
| `concourse y=-26` 2.1 .. 5.9 | 3.8 m | A07 portal, c=4.0 w=3.8 |
| `concourse y=-32` 4.9 .. 8.1 | 3.2 m | Recovery portal, c=6.5 w=3.2 |
| `concourse/cafefoyer y=-32` 10 .. 14 | 4.0 m | Cafe portal, c=12.0 w=3.6 |
| `checkin y=-26` -18 .. -8 | 10 m | baggage service wall, `_baggage()` owns it |

**There is no genuinely bare public wall in this building.** The wall finish is
complete. I came close to building ~1000 m² of redundant cladding over work
that was already done, and over glazing that is meant to be glass.

### Correction 2 — "the exterior roof is a flat slab" is wrong.

`repair38.whole_shell_union` records an exact union of **774 input solids
leaving 1734 exposed faces with buried faces removed**, and an explicit
`roof_steps` list stepping the roof per room: 3.76 m over publicreturn /
entrancefoyer, 3.96 m over publicreturn / checkin, 4.16 m and up. `SM_AP_Roofs38`
measures 35 × 56 m spanning z 3.16 .. 7.34 — 4.18 m of height variation.

The roof is a stepped union, not a slab. What it genuinely lacks is rooftop
equipment: 268 vertices over 1960 m² means prismatic steps with no plant, no
parapet detail and no rooftop units. That only matters because this game has a
flight mode and the player does see the roof from above on departure. Logged as
an opportunity, not a defect, and not fixed in this pass.

### Correction 3 — "uniform green ground" is half right.

`SM_AP_Ground12` is 550 × 1600 m carried by **130 vertices** — a flat plane over
880,000 m². But `SM_AP_Grounds34` is 516 × 1500 m with 2832 vertices spanning
z −3.77 .. 6.16, so there is ~10 m of real relief in the landscape. The ground
is not uniform; the base plane under it is.

---

## 1. What is actually wrong: the rooms are empty

The defect is not surface treatment. It is that whole rooms carry no content.
Bucketing all 315 authored instances into the 19 zones by smallest containing
rect:

| zone | area m² | props | per 100 m² | floor >2.2 m from anything |
|---|---:|---:|---:|---:|
| `publicreturneast` | 4 | 0 | 0.0 | 93% |
| `arrivalsreturn` | 10 | 0 | 0.0 | 81% |
| `cafefoyer` | 36 | 0 | 0.0 | 80% |
| `amenitylobby` | 33 | 0 | 0.0 | 70% |
| `baggageservice` | 26 | 0 | 0.0 | 37% |
| **`concourse`** | **108** | **2** | **1.9** | **75%** |
| `gate07entry` | 33 | 1 | 3.0 | 53% |
| `landsidecorridor` | 92 | 4 | 4.3 | 68% |
| `arrivals` | 80 | 4 | 5.0 | 45% |
| `publicreturn` | 92 | 6 | 6.5 | 31% |
| `operations` | 66 | 5 | 7.6 | 36% |
| `gate08` | 160 | 14 | 8.8 | 24% |
| `gate07` | 117 | 15 | 12.8 | 34% |
| `amenities` | 81 | 11 | 13.6 | — |
| `cafe` | 306 | 42 | 13.7 | 36% |
| `recovery` | 40 | 6 | 15.0 | 28% |
| `checkin` | 170 | 27 | 15.9 | 27% |
| `entrancefoyer` | 60 | 11 | 18.3 | 25% |
| `security` | 182 | 36 | 19.8 | 21% |

The rooms the game was built around run 13–20 props per 100 m². **The airside
concourse runs 1.9** — a 108 m² room on the player's main route holding one
plant and one security camera, with three quarters of its floor more than a
stride from anything. That is the measurement behind "the concourse floor is
40% of frame and featureless". Five more rooms hold nothing at all.

Two caveats on the table. `baggageservice` reads as 0 because its two
`Bag receiving bed38` units are centred at x=−26.11, 11 cm outside the zone
rect; it has content. And the large union actors (walls, ceilings, wayfinding,
retained craft, fixtures) sit at the origin, so their content is not bucketed
anywhere — 18 authored wall markers were counted separately.

## 2. Verbatim repetition

| asset | count | finding |
|---|---:|---|
| `SM_AP_Curb` | 23 | a curb line; repetition is correct here |
| `SM_AP_CafeChair34_Hardware40` | 12 | one asset, one scale, yaw only 0/90/180 |
| `SM_AP_GateDoor` | 9 | doors; correct |
| `SM_AP_Bench34_Hardware40` | 8 | acceptable, they are spread across four rooms |
| `SM_AP_Tree` | 4 | see below |
| `SM_AP_GardenBench` | 4 | see below |
| `SM_AP_Streetlight` | 4 | see below |

The forecourt is the clear one, and it is worse than "four identical trees":
**the whole group repeats verbatim four times.**

```
tree  x=-58.8  yaw 0   scale 1.25     y = -18, -8, 2, 12
bench x=-55.7  yaw 90  scale 1        y = -18, -8, 2, 12
light x=-61.0  yaw 0   scale 1        y = -18, -8, 2, 12
```

Identical x, identical yaw, identical scale, on an exact 10 m pitch. This is the
first thing the player sees on leaving the forecourt.

## 3. A new defect in the upstairs gallery

The gallery deck is `x -49..-41, y 25..34` at z 3.15, 72 m², holding eight
items. Two measured faults, both confirmed from authored coordinates and real
asset bounds rather than from a capture:

1. **A counter jammed against a shelf face.** `ChargingTable24_1797`
   (2.80 × 0.65) at (−47.5, 33.0) yaw 0 spans y 32.68 .. 33.33.
   `RetailShelf24_1832` (1.50 × 0.54) at (−47.0, 33.6) spans y 33.33 .. 33.87.
   They meet exactly at y = 33.33, and their x ranges overlap. A 2.46 m tall
   shelf unit has a 1.10 m counter flush against its front face, so neither is
   usable.
2. **Three identical shelves with their backs to the only view.** All three sit
   at y = 33.6, 0.40 m from the y = 34 glazing, all at yaw 0, all unscaled.

And the gallery has **no table at all** — two benches 4.5 m apart, one of them
isolated, a charging bar serving neither, three shelves and a bin.

Both benches carry a seated NPC anchor (`Gallery passenger 0` at (−46.8, 31.2),
`Gallery passenger 1` at (−42.3, 28.8)), so neither bench can be moved without
moving its character placement. The repair therefore moves the counter and the
shelves, and leaves the benches where they are.

## 4. The repair

`Spec46.json`, authored by `author_spec46.py`, three kinds of change kept
separate so each can be judged and reverted alone:

- **66 placements** — new instances of assets the project already owns, in the
  empty rooms. No new art, so no new art risk, and the style matches by
  construction. This is how the project's own layout passes work.
- **4 moves** — the gallery counter to a window bar at the stair head, and the
  three shelves into a back-to-back gondola island with an end cap, so the backs
  face each other and 2.1 m of walkway opens behind.
- **24 variations** — yaw, scale and cross-pitch offset on the forecourt group,
  and a few degrees of yaw jitter on the twelve cafe chairs. Chair positions are
  left exactly as authored, because the seated anchors are at table centres.

| room | added |
|---|---:|
| concourse | 9 |
| arrivals | 9 |
| operations | 8 |
| landsidecorridor | 7 |
| publicreturn | 7 |
| cafe (gallery) | 7 |
| baggageservice | 5 |
| gate07entry | 5 |
| cafefoyer | 4 |
| amenitylobby | 4 |
| arrivalsreturn | 1 |

The concourse's dead-end south bay — nothing pierces y=−4 — becomes a waiting
alcove with a departures board on the end wall, two benches facing each other,
a charging bar and planting, rather than more empty corridor.

### What the validator caught

`validate_spec46.py` checks every placement offline against real footprints:
inside its room, under its ceiling, clear of every authored instance, clear of
the other placements, outside the 1.9 m `route_clear_width_m` corridor on all
three authored routes, clear of all 18 portal mouths, and not standing on a
seated NPC anchor.

The first run of the spec I had written by hand produced **35 failures**,
including one real conceptual error: I had the wall axis convention backwards
and put the arrivals reclaim board at x=−12, outside an 8 m room, when
`arrivals x=-12` denotes a wall at **y**=−12. Others were ordinary collisions
with props I had not noticed — `Plant1224_1772`, `Safety station 1`,
`RetailShelf24_1814`, `OperatorChair24_1813`, the existing trolley rank along
y=−21.2 — and two rooms where the portal mouths leave genuinely no room, so
placements were dropped rather than forced.

The spec now passes with 66 placements, 4 moves, 24 variations and no failures.
`Run-Apply46.ps1` refuses to launch unless the validator exits clean, and
`apply46_probe.py` re-checks every change against live geometry in-engine,
destroying and reporting anything that overlaps — because an authored rectangle
clearing every authored prop can still hit a wall cassette, a soffit or a
fixture living inside a union actor.

## 5. Not established

- Everything above is authored-data analysis. It says nothing about how any of
  it looks; the apply pass and captures are what settle that.
- The empty-floor percentages use authored instance positions only. Union-actor
  content (wall finishes, wayfinding, fixtures) is not included, so a room with
  mounted content it does not measure will read emptier than it plays.
- The repetition judgment is mine. Four identical streetlights on a road are
  normal; four identical tree-plus-bench-plus-light groups at identical yaw are
  the thing I am calling a defect, and that is a judgment, not a measurement.
- Rooftop equipment is not addressed.

---

# RESULT — 2026-10-30

## What landed

| | |
|---|---:|
| New actors placed | **96** of 98 (2 kerbs rejected for clipping `Slab12_1`) |
| Existing actors moved | 6 |
| Variations applied | 12 |
| Collision enabled on walk-through planting | 10 |
| Ceiling mounts built and imported | 2 |

### Room density, live level before and after

| zone | area m² | before | after | per 100 m² before | after |
|---|---:|---:|---:|---:|---:|
| `cafefoyer` | 36 | 0 | 4 | 0.0 | 11.1 |
| `amenitylobby` | 33 | 0 | 4 | 0.0 | 12.1 |
| `arrivalsreturn` | 10 | 0 | 1 | 0.0 | 10.0 |
| `publicreturneast` | 4 | 0 | 0 | 0.0 | 0.0 |
| **`concourse`** | 108 | 3 | **12** | 2.8 | **11.1** |
| `gate07entry` | 33 | 1 | 6 | 3.0 | 18.2 |
| `landsidecorridor` | 92 | 4 | 11 | 4.3 | 12.0 |
| `operations` | 66 | 4 | 12 | 6.1 | 18.2 |
| `publicreturn` | 92 | 6 | 13 | 6.5 | 14.1 |
| `arrivals` | 80 | 6 | 15 | 7.5 | 18.8 |
| `cafe` (incl. gallery) | 306 | 46 | 53 | 15.0 | 17.3 |
| **forecourt** | open | **4** | **39** | — | — |

`publicreturneast` is a 1 m wide, 4 m² connector. Nothing fits in it without
blocking the only route through, so it was left alone deliberately.
`baggageservice`, `amenities`, `gate08` and `recovery` were not touched: the
live level shows them adequately furnished, whatever the authored census said.

## The forecourt was the real find

The improvement brief started from the authored layout and said the forecourt
repeated one landscape group four times. The live inventory says otherwise:
**zero** `SM_AP_Tree`, `GardenBench`, `Streetlight`, `Curb`, `TaxiCar` and
`ShuttleBus` actors exist in the built level. The forecourt the player spawns
into held four actors in total — a character collision proxy, `Slab12_1`, the
canopy and one asphalt slab.

All eight meshes still exist under `/Game/Airport10/Meshes`, none is on
`repair38.forbidden_architecture_assets`, and none is in
`architecture_removed_asset_ids` — they were dropped as instances by the pass
that removed 1504 of them, not banned. So the repair places them, with
variation built in from the start rather than restoring a 4× repeat: three
trees at differing yaw, scale and offset, four lamp standards with alternating
arm direction interleaved between them, three planter-benches under the
shelter, a kerb run, three taxis at slightly differing angles and a shuttle bus.

Nothing tall stands under the canopy: it occupies x −61..−52.95, y −21..−3.5 up
to z 3.85, and an 8.5 m tree or a 5.8 m lamp there would pierce the shelter
roof. `A2_forecourt_north.png` is the result.

## Check-in header mounts

`Check-in service header29 0` and `1` are 3.34 m boards hanging at 2.85 m with
nothing holding them. Two mounts were built in Blender following
`secondary_patch38`'s part language exactly — ceiling shoe, threaded hanger,
captured saddle — and imported. `H1_checkin_headers.png` shows four hangers
bearing the two boards.

Measured in-engine: mount spans z 3.155 → 3.800, board top is z 3.180, so the
saddle straddles the board's top edge by 24 mm; the mount's top, 3.800, is the
same height as the top of `Airport38 verified architectural attachments`, the
existing tested actor whose own test asserts ceiling contact at the zone
ceiling height in a 3.8 m room.

**Not verified by trace.** Line traces and box overlaps above roughly 2.5 m
returned nothing in the `-run=pythonscript -NullRHI` context — including at the
A07 and A08 displays, which are mounted and have a passing contact test in
`test_secondary38.py`. The physics query, not the geometry, is what failed
there, so the mounting rests on the two in-engine bound measurements above and
on the capture, not on a contact trace.

## Regression

| run | score | failing check |
|---|---:|---|
| before Pass46 | 166/167 | Scanned airport bag physically carried aboard in flight |
| after, run 1 | 161/162 | Departure interlock: path blocked by Physical luggage 01 |
| after, run 2 | **166/167** | Scanned airport bag physically carried aboard in flight |

Run 2 reproduces the pre-Pass46 result exactly, so **Pass46 did not regress the
journey**. Run 1's interlock was run-to-run variance in the bag system, which
is now evidenced across four runs with three distinct outcomes — the strongest
support yet for P45-008. The checked bag ends at (−23.40, −13.02) in the
receiving bed, state `safely_received`, in both runs; it is the carry-on whose
fate varies.

## Mistakes this pass made, and what caught them

- The spec was first validated against the **authored layout**, which still
  lists 1504 instances the built level does not have. That invented collisions
  with every `Curb12_*` and `Tree12_*`, and missed real ones — it is why five
  placements went into `baggageservice`, a room that is actually full. The
  validator now reads `Inventory46.json`, the live level.
- The wall axis convention was backwards: `arrivals x=-12` denotes a wall at
  **y** = −12, so the reclaim board was first placed outside an 8 m room.
- Placements ran before moves, so the gallery planter was rejected for
  overlapping a counter the same run was about to move away.
- Gallery items were floor-snapped, and the deck has no collision, so the snap
  traced through it and dropped a 2.46 m shelf 2.15 m into the café below.
- The gondola yaws were inverted, pointing both shelf fronts at each other and
  both backs at the room — worse than the defect being repaired. Caught in
  `G2_gallery_retail.png` and fixed; `G1_gallery.png` shows the corrected run.
- Three new flight boards rendered blank, because `equipment_displays38` routes
  screen content by actor name from `repair38.equipment.screen_roles38` and the
  new names were not in it. Registered in the export, in
  `equipment_scrutiny38.py` and in the count assertion in `test_secondary38.py`.

## Still open

- `P46-015` — two X-ray scanners, six queue posts and four stanchions are
  visible, solid-looking and walk-through. They sit in the security and
  check-in lanes the 166/167 journey walks, so making them solid needs its own
  run per change. Not attempted here.
- The gallery deck (`Crafted GalleryStair35`) is registered with collision
  `none`, so physics objects fall through it. The player stands on it via the
  authored floor zone, so this only shows up for dropped items.
- Rooftop equipment; `SM_AP_Ground12`'s 130-vertex base plane.
- P45-008, the bag carry non-determinism, is unfixed and now better evidenced.
