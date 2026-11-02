# Pass 46 defect and improvement ledger

Continues Pass45's ledger. Source-bound: every row cites the file or the
measurement it came from, and says whether it is a measured fact or my
judgment. `Run-*.ps1` in this folder reproduces each check.

## Status

| id | sev | status | title |
|---|---|---|---|
| P46-001 | P1 | **FIXED** | Five rooms carry no authored content; the airside concourse carries two props in 108 m² |
| P46-002 | — | **WITHDRAWN** | "The forecourt group repeats four times" - those actors are not in the built level at all |
| P46-002b | P1 | **FIXED** | The forecourt the player spawns into held four actors; all its authored landscape was missing |
| P46-003 | P1 | **FIXED** | Gallery charging counter is flush against a retail shelf face; neither is usable |
| P46-004 | P2 | **FIXED** | Three identical gallery shelves stand 0.4 m from the glazing, backs to the view |
| P46-005 | P2 | **FIXED** | The gallery has no table; two benches 4.5 m apart and a counter serving neither |
| P46-006 | P3 | **FIXED** | Empty roof: 17 units of rooftop plant, a railed hatch, paver walkway and cable tray, all on survey-measured flat roof |
| P46-007 | — | **WITHDRAWN** | "SM_AP_Ground12 is 130 vertices" - no actor uses it; the ground is Grounds34 plus the Flight39 airfield. Real ground defect is P46-020 |
| P46-008 | — | **WITHDRAWN** | "The walls are blank" — they are not. 298 cassette panels, 1423 m², cover them |
| P46-009 | — | **WITHDRAWN** | "The roof is a flat slab" — it is a 774-solid union with per-room steps |
| P46-010 | P2 | **RESOLVED** | Pass45's support probe fired one ray per face centre, so ceiling-hung and wall-hung items reported as floating |
| P46-011 | P1 | **FIXED** | Bag lost in security and in the cockpit. Two root causes fixed; journey now 174/174 three runs running, from 0 passes in 6 |
| P46-012 | P1 | **FIXED** | Lavatory inside release plates hung 30.7 cm clear of the cubicle door face |
| P46-013 | P1 | **FIXED, VERIFIED** | Check-in headers had no mount; hangers built. -game trace: ceiling at 3.800 over all four hangers, mount top 3.800, gap 0 |
| P46-014 | — | **WITHDRAWN** | "Ten plants were walk-through" - they were already QUERY_AND_PHYSICS; the change was a no-op. All ten now traced solid in -game |
| P46-015 | P2 | **FIXED** | Two X-ray scanners, six queue posts, four stanchions were walk-through; all twelve now traced solid in -game, journey unchanged |
| P46-016 | P2 | **FIXED** | Three new flight boards rendered blank: not registered in screen_roles38 |
| P46-017 | P3 | **FIXED** | Gallery deck had collision off; now solid. A real 8 kg bag dropped on it rests at the deck surface, speed 0 |
| P46-018 | P2 | **OPEN** | The player is a floating 0.70 m sphere at z 1.27..1.97, so nothing lower than 1.27 m can stop it |
| P46-019 | — | **CORRECTION** | No physics query answers under -run=pythonscript at any height; not "above 2.5 m" as first reported |
| P46-020 | P2 | **FIXED** | The world ended in a straight edge 150 m west of the terminal, sky dome visible below it; ground skirt to the horizon |

---

### P46-001 — rooms with no content

**Measured.** All 315 authored instances bucketed into the 19 zones by smallest
containing rect, from `Exports/airport_layout.json`.

Zero authored props: `publicreturneast` (4 m²), `arrivalsreturn` (10 m²),
`cafefoyer` (36 m²), `amenitylobby` (33 m²), `baggageservice` (26 m², though it
does hold two `Bag receiving bed38` units centred 11 cm outside the rect).
`concourse` holds 2 props in 108 m² — 1.9 per 100 m² where the rooms the game
was built around run 13–20 — with 75% of its floor more than 2.2 m from
anything.

**Repair:** 66 new instances of assets the project already owns, across 11
rooms. `Spec46.json`, validated offline by `validate_spec46.py` and re-checked
live by `apply46_probe.py`.

**Acceptance:** `Run-Apply46.ps1` reports 66 placed and 0 rejected; a re-run of
the census shows no public room below 8 props per 100 m².

### P46-002 — forecourt repetition

**Measured, with a judgment attached.** `SM_AP_Tree` at x=−58.8 yaw 0
scale 1.25, `SM_AP_GardenBench` at x=−55.7 yaw 90, `SM_AP_Streetlight` at
x=−61.0 yaw 0, each at y = −18, −8, 2, 12. Identical x, yaw and scale on an
exact 10 m pitch.

The measurement is that the group is identical. That this reads as a defect is
my judgment: four identical streetlights along a road are normal, four
identical tree-plus-bench-plus-light groups are not.

**Repair:** per-instance yaw (14°, −37°, 61°, −88°), scale (1.25, 1.12, 1.34,
1.19), cross-pitch offsets up to 0.9 m, and alternating bench facing and lamp
arm direction. Nothing leaves the forecourt slab.

### P46-003 / P46-004 / P46-005 — the gallery

**Measured.** From authored coordinates and FBX bounds:

- `ChargingTable24_1797` (2.80 × 0.65) at (−47.5, 33.0) spans y 32.68..33.33.
- `RetailShelf24_1832` (1.50 × 0.54) at (−47.0, 33.6) spans y 33.33..33.87.
- They meet exactly at y = 33.33 with overlapping x. A 2.46 m shelf has a
  1.10 m counter flush against its front face.
- All three shelves sit at y = 33.6, 0.40 m from the y = 34 glazing, yaw 0.
- No table exists anywhere on the 72 m² deck.

**Constraint honoured:** `Gallery passenger 0` sits at (−46.8, 31.2) and
`Gallery passenger 1` at (−42.3, 28.8), which are the two bench positions. The
repair moves the counter and the shelves and leaves both benches, because
moving a bench would leave its character placement behind.

**Repair:** counter becomes a window bar at the stair head facing the west
glazing; the three shelves become a back-to-back gondola island with an end
cap, backs facing each other, 2.1 m of walkway behind; two tables with four
chairs added; a planter closes the corner the counter vacated.

### P46-008 / P46-009 — withdrawn claims

Both were reported to the user from captures in Pass45 and are not supported.
`FINDINGS_ROOMS.md` §0 gives the full accounting. Short version: the wall
finish is complete (`terminal_finish43_v1`: 298 panels, 131 surfaces, 1423 m²),
`finish43._exterior_glazed` correctly skips curtain wall, and every remaining
"bare" run is a door opening. The roof is `whole_shell_union`: 774 input
solids, 1734 exposed faces, buried faces removed, with an explicit per-room
`roof_steps` list.

Acting on either claim would have meant building ~1000 m² of cladding over
finished wall and over glazing meant to be glass.

### P46-010 — the support probe's ray pattern

**Measured.** `Pass45/support45_probe.py` fires one ray per bounding face, from
the face centre. `secondary_patch38.py:47` builds ceiling shoes, threaded
hangers and captured saddles for both gate flight displays at `y ± 0.65` from
their centre — so a single centre ray up from the display top passes between
the two hangers and hits nothing.

That explains the Pass45 report of `Gate A07 flight display`,
`Gate A08 flight display`, `Check-in service header29 0/1` and the WC release
plates as unsupported. `inventory46_probe.py` fires a 3×3 fan from each face,
54 rays per actor, to settle which of the 30 are real.

**Not yet established:** which of the 30 survive the corrected probe. Until the
inventory run lands, I do not know, and I have built no mounting geometry.

### P46-015 — security and queue furniture (FIXED, 2026-10-31)

**Measured before changing anything.** `verify46_probe.py` under `-game`, with a
passing control (floor below check-in and the west wall both hit): all twelve
read `NO_COLLISION` and a trace passed straight through each.

**Why the scanners were off.** The layout declares both `collision: True`. The
component was fine to set; the *actor-level* switch was off, which masks the
component — the first attempt came back `NO_COLLISION -> NO_COLLISION`. No
runtime code touches it, so it was lost at build time. `collide46_probe.py` now
records and restores actor-level collision as well.

**Lane clearance, offline.** `clearance46.py` rebuilds all 61 terminal walk legs
of the flight journey from `qa_contract38` + `qa_scanner38` exactly as
`journey38_review.start(flight=True)` composes them. The pawn
(`BP_ArtTourPawn_C`, measured: z 1.62, z half-extent 35.0 cm) collides only in
z 1.27..1.97. Posts (top 1.028) and stanchions (top 1.073) cannot reach that
band; the scanners are at least 1.50 m from every leg. Note: the bag-pickup
diagonal `[-32.1,-13.65] -> [-35.7,-15.5]` passes *through* `Queue post31 4`'s
footprint. It only works because the pawn floats over it (see P46-018).

**Verified in -game.** 22 of 22 traced solid and conclusive: the twelve plus the
ten P46-014 plants. Rays now come from four sides with a 0.45 m standoff; the
first single-ray run left five plants inconclusive because a wall stopped the
ray first. The scanners block from the sides and not along y, which is the
tunnel axis; the bag path at z 1.375 traces open through both.

**Regression, one run per group.**

| run | checks | walk legs | scan waits | failing check |
|---|---|---|---|---|
| before Pass46 | 166/167 | 83/83 | pass | carried-bag proof (P46-011) |
| after group A (posts, stanchions) | 166/167 | 83/83 | pass | carried-bag proof (P46-011) |
| after group B (scanners) | 166/167 | 83/83 | pass | carried-bag proof (P46-011) |

### P46-014 — withdrawn

`Apply46.json` shows `was = QUERY_AND_PHYSICS` for all ten plants. The
"collision off" reading never came from a measurement: `dig46.py` filtered on
`visible` and `collision_enabled`, neither of which `Inventory46.json` records,
so that section printed nothing and the claim was inferred. They were solid all
along, and are now proven so.

### P46-018 — the player cannot hit anything low

**Measured.** The pawn is a DefaultPawn sphere, r 0.35 m, held at z 1.62 by
`FloatingPawnMovement` with no gravity; the walk operator zeroes `d.z`. Its
collision exists only between 1.27 and 1.97 m. Benches, tables, planters,
posts, counters and stanchions are all below that, so the player passes over
them whatever their collision says. It is an art-tour pawn, so this may be
intended. A real capsule would change the game's feel and would break at least
the `Queue post31 4` leg and the 0.40 m squeeze past the two queueing
passengers, so it is a design decision, not a fix to make quietly.

### P46-019 — correction to the header-mount limitation

Pass46 reported that physics queries "above ~2.5 m" return nothing under
`-run=pythonscript -NullRHI`. A control trace onto the check-in floor at 1.4 m
also returns nothing there, so **no** query answers in that mode at any height.
The same control passes under `-game`. The header-mount conclusion is
unchanged — still not verified by trace — but the reason is the mode, not the
height, and it can now be checked under `-game`.

### P46-017 — gallery deck (FIXED, 2026-10-31)

`Crafted GalleryStair35` is the whole gallery kit in one mesh. flow39 registers
it `none` by name and validate39 pins that as the "retained stair collision
contract"; Flow39's REPORT gives the reason, preserving the stair navigation
floors. The player's height comes from `floor_at_source`, not physics, so the
contract was protecting something physics never drove.

**Measured before changing it** (`deck46_probe.py`, -game, collision toggled
for the session only): as built, down-traces pass through the deck. Toggled
on, simple and complex collision both hit the deck at 3.165; horizontal traces
under the deck at 0.6/1.62/2.4 m hit nothing, so there is no auto-generated
hull filling the cafe; the pawn's sphere sweeps up both flights, across the
landing and onto the deck are clear either way.

**Applied** (`collide46_probe.py` group C) to the level, and the layout
instance set `collision: True` so a rebuild keeps it. The asset-level contract
in validate39 is untouched; it is about the mesh, not the placed actor.

**Accepted** (`drop46_probe.py`, -game): `Physical luggage 06`, a real 8 kg
simulated bag no journey step uses, released 0.65 m over three deck points
comes to rest on `Crafted GalleryStair35` at 3.165, speed 0, centre of mass
0.448 m above the surface — the same offset as the control drop onto the cafe
floor (0.449). The bag is put back afterwards.

### P46-013 — verified by trace

`deck46_probe.py` traced up from each hanger in -game, ignoring the mount:
`Airport38 coherent ceiling union` at 3.800 at all four; mount tops 3.800; gap
0.000. With the mount included the first hit is its shoe at 3.776. The mounts
bear on the real ceiling.

### P46-011 — the bag carry bug: two root causes, both fixed

**1. The security greeter stood in the walk lane.** Every lost-bag run stops
the held bag dead at (-47.31, -0.14, ~1.3), inside `CH12COLL Security
greeter` (0.7 x 0.7 x 1.8 m at (-47.0, -0.4)), placed in Pass39 on the y=-0.4
walk line that has existed since Pass38. The pawn slides round her; the lower
bag swings into her box and wedges, and the passenger walks on "holding" it.
Whether it wedges depends on the swing — hence the run-to-run variation.
Moved to (-43.6, -2.3), beside the controlled entry, >1 m from every walk leg,
facing the people coming in. Level (`npc46_probe.py`), layout,
`Characters/Revision39/ArtBible/NativeCharacters39.json` (the runtime builds
her talk target from it) and the Pass39 literal all agree.

**2. Seated at the flight controls the bag wedged at the side console.** With
the snag gone the bag reached the cockpit and exposed this: the core carry
goal is 1.25 m ahead of the camera, which seated at the controls is inside the
instrument panel. The bag pressed into it, lost to the capped spring under
taxi and takeoff acceleration and wedged at (14.68, -3.84, 0.65); on standing
it stayed, so the in-flight check found it 3 m away (run bagfix2), or the
departure sweep saw it poking out of the strict cockpit cell (run bagfix1:
"Departure path blocked: Physical luggage 01"). `airport_journey38._seated_hold_goal`
now holds a carried item, while seated in an aircraft seat, where the
passenger stood just before sitting — a spot they had just occupied with the
same bag, and where `stand()` returns them. Aircraft seats only.

The journey report now also carries a `departure_diagnosis` (blocking bounds,
and for a held bag which aboard test failed) whenever departure is refused, so
the next failure of this kind names its cause.

### P46-011 — result

| run | after | checks | outcome |
|---|---|---|---|
| before46, run1, groupA, groupB | (baseline) | 166/167, 161/162 | bag lost: wedged in the greeter, or at the cockpit console |
| bagfix1 | greeter moved | 161/162 | bag reached the cockpit; departure sweep saw it poking out of the cockpit cell |
| bagfix2 | + departure diagnosis | 166/167 | bag wedged at the side console while seated, left behind on standing |
| bagfix3 | + seated hold goal | **174/174** | first full pass ever recorded |
| bagfix4 | repeat | **174/174** | |
| final2 | + deck, rooftop plant, ground skirt | **174/174** | |

174 is more than 167 because the route now reaches the in-flight drop and the
checks after it. One further run ("final") was killed at 171/171 by my own
launcher, not by the game: the journey truncates and rewrites its report on
every check, `ConvertFrom-Json` of the empty read is `$null`, and
`$null -ne 'RUNNING'` is true. All three Pass46 launchers now require a real
end state.

### P46-006 — rooftop plant (FIXED)

`roof46_probe.py` (-game) surveyed the roof on a 1 m grid: one roof actor,
`Airport38 coherent roof union`, tops between 3.34 and 7.34 m.
`plan_roof46.py` places each unit only where every survey point under its
footprint plus a margin is one height within 3 cm, on the room it serves, 1.2 m
from every other unit; walkway and tray runs are checked flat at one level and
clear of every unit. `build_roof46.py` (headless Blender) builds the kit:
air-handling units on dunnage with louvres, battens and a supply duct through a
curb; condensers with guarded fans; mushroom extract fans on curbs; goosenecks;
a hatch on a curb with a three-sided rail standing on the roof; rubber pavers
with 50 mm joints; cable tray on pedestals. Rendered and corrected twice before
import (floating rail posts; overlapping, z-fighting pavers).

Placed: AHUs over check-in, gate 08 and security; condensers over the cafe,
concourse, gate 07 and arrivals; kitchen extract over the cafe, WC extract over
the amenities; four goosenecks; the hatch on the security roof with a paver
path round the AHU's end to its service doors; a tray between the concourse and
gate 07 condensers. 21 640 triangles, four project materials, no collision.
Before/after stills: `Captures/R1..R3_*_before.png` / `_after.png`.

### P46-020 — the edge of the world (FIXED)

Found while judging P46-007 from the flight vantage (`R4_ground_wide_before`):
the Flight39 airfield slab (x -200..500, y -2600..800) ends in a straight edge
and the 4 km `SkyCloudDome`'s lower half shows beyond it. There is no sea or
backdrop. `edge46_probe.py` measured the edge every 25 m in -game: -0.08 m
landside, -3.78 m airside, graded between. `build_skirt46.py` lays a skirt that
follows those heights: inner rim 3 m under the slab's lip 5 cm low, flat for
40 m, then out to a 3850 m circle inside the dome; rim order checked strictly
anticlockwise so it cannot fold. The airfield's own `MI_AP_F39Field`, no
collision.

### Still open, deliberately

- **P46-018**, the player's floating 0.70 m sphere. A real capsule changes how
  the game plays and would break route legs that only pass because the pawn
  floats (one runs through `Queue post31 4`). That is a design decision.

---

## Pass47 (2026-10-31)

Full critique of the game in `Pass47/CRITIQUE47.md`; this records what changed
in the level and how each change was proved. Every level edit was preceded by
a hashed backup in `Pass47/Backup/`.

| id | status | change | proof |
|---|---|---|---|
| P47-001 | FIXED | Ceilings mid-grey under white walls: ceiling emission 15 | `Look47.json`, luminance 0.42 -> 0.56 (check-in) |
| P47-002 | FIXED | 31 forecourt duplicates of instanced scenery removed; canopy trees/lights replanted across the road | `Fix47.json` |
| P47-003 | FIXED | Two flight boards hung backwards; arrivals board said DEPARTURES | `After/Z07b`, `Z13b`, `Z31b` |
| P47-004 | FIXED | Access road ended in the grass; extended y -600..800 | `Road47.json` |
| P47-005 | FIXED | Silent airport: five ambient loops mixed by position | `VerifyAudio47.json`, 10 stops |
| P47-006 | FIXED | Bag fell out of the cockpit in flight: `COL_CockpitFloor47` | `Floor47.json`, 1,430 cells at z 0.000 |
| P47-007 | MITIGATED | Carried bag snag in the cabin aisle: held 0.7 m ahead at hip height aboard | journey runs below |
| P47-008 | FIXED | Bare corridors and repack room: seven lit travel posters | `Posters47.json`, `After2/P*`, `After3/Z11*` |
| P47-009 | FIXED | Sign arrows over text (CHECK-IN, CLOUD NINE): corrected faces in game, builder fixed | `After2/S1`, `S2` |
| P47-010 | FIXED | Blank landside facade: roof lettering and arrivals fascia | `After2/F1..F3` |
| P47-011 | FIXED | Gate 08 clone row: one passenger re-seated, one standing at the glass | `Gate08_47.json`, `After3/G1`, `G2` |
| P47-012 | FIXED | Unmarked apron: airside service road, zebra carried across it | `AirsideRoad47Build.json`, `After3/T1`, `R1` |
| P47-013 | FIXED | Unmarked access road; taxis and shuttle parked broadside across it: road painted, vehicles turned to the kerb lane, taxi rank and bus bay | `Kerb47.json`, `After3/L1`, `L3`, `L4` |
| P47-014 | PROPOSAL | No segregated arrivals route; needs new openings in the union shell from the Blender master | `CRITIQUE47.md` L1 |

### Journey regression

Before round 2 (posters, signs, facade, Gate 08, roads, vehicles): three runs,
174/174 each (`Pass46/Backup/FlightJourney39_pass47c1..c3_*.json`).
After everything, on the final level: three runs, 174/174 each, all five
journey flags true (`Pass46/Backup/FlightJourney39_pass47f1..f3_*.json`,
551 s, 510 s, 436 s).
