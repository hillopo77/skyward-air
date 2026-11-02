# Pass47 critique: the whole game, big picture to small

Everything below was looked at in the running game, not inferred from files:
40 player-eye stills of every space (`Captures/`), one still of each of the
**402 distinct models** (`ModelSheets/`, index in `ModelSheets/index.json`), a
reachability flood-fill with the player's real collision, light measurements
from every still (`Ambience47.json`), real-world size checks, and a sound
inventory. Each finding says whether it is fixed, and how that was proved.

## What the game does well

- **Gate A07 is the best space in the game.** Desk, agent, departures screen and
  the aircraft right there through the glass; it reads instantly as a gate.
- **The cafe** is the strongest room: double height, full glazing, the gallery
  above, a real counter with food.
- **The aircraft interior** (business suites, economy, galley, flight deck) is
  the most finished part of the project; its 260-odd small parts are clean.
- **One coherent art direction**: cream walls, slate dado, oak rail, navy and
  teal accents, soft stylised characters. 402 models, no scale errors.
- **Exposure is well controlled**: interiors sit at mean luminance 0.43-0.62
  with no clipped highlights and almost no crushed blacks.

## Big picture: layout and the airport as a place

| # | Finding | Status |
|---|---|---|
| L1 | **No arrivals route.** Every room connects, but a passenger leaving the aircraft can only reach baggage reclaim by walking back out through security. Real terminals segregate arrivals. | **Proposal.** Needs a glazed corridor along the airside facade from Gate 07 to Arrivals and new openings in the shell, which means rebuilding the union from the Blender master (open in your session). |
| L2 | **The terminal sits on a grass bank 3.8 m above the apron**; the jet bridge crosses grass and there is no airside service road. | **Road fixed; bank stays.** The apron is legitimately 3.7 m below the terminal floor (surveyed every 0.5 m, `Verify2_47.json`). A 4.8 m service road is now painted along the bank's toe: white edge lines, dashed centre, y -24..36, clear of the wing and under the bridge. The existing staff zebra crossing stopped mid-road; the lines now break for it and two matching bars carry it to the stand (`After3/T1_road_top.png`, `R1_road_from_gate.png`). A retaining wall still needs the master. |
| L3 | **The landside face is a long blank wall** with a small entrance; from the road the building reads as a warehouse. | **Fixed.** 'SKYWARD AIR' in 0.85 m gold letters on a steel rail frame on the entrance roof, and an 'ARRIVALS / TAXIS & SHUTTLE' fascia over the arrivals exit, which had no sign outside (`After2/F1..F3_*`). From right under the canopy the roof letters are hidden by it; they read from the road and the air. |
| L4 | **The access road stopped in the grass at both ends.** | **Fixed.** Ground traced flat every 10 m from y -600 to +800; the same asphalt now runs on at the same height and width (`Road47.json`). |
| L7 | **The access road was bare asphalt, and every vehicle on it was parked broadside across it**: the three taxis and the 9 m shuttle stood across both lanes, noses into the kerb, the shuttle overhanging the grass. Only visible once the road had lines. | **Fixed.** Road painted for 1.4 km (edge lines, dashed centre). The taxis and shuttle turned to face north in the kerb lane, 0.30 m off the kerb (`Kerb47.json`), inside an amber taxi rank ('TAXI' twice) and bus bay ('BUS') (`After3/L1_*`, `L3_taxi_rank_top`, `L4_bus_bay`). |
| L5 | The world ended in a straight edge 150 m west of the terminal (Pass46 P46-020). | Fixed last pass; ground skirt to the horizon. |
| L6 | Reachability. | **Measured, fine.** With doors open, every public room is 75-100% reachable from the spawn; only the staff baggage room is not, through a 1.15 m service hatch (`Critique47_reach.json`). |

## Spaces

| # | Finding | Status |
|---|---|---|
| S1 | **Every ceiling read mid-grey** (0.37-0.48 in the stills) under near-white walls: every light points down and this renderer has no bounce light. | **Fixed.** Ceiling material emission trialled live at seven values (`Look47.json`); at 15 ceilings come up to wall level (check-in 0.42 -> 0.56, concourse 0.46 -> 0.57, corridor 0.56 -> 0.64); 40 glowed. Set in the asset and its source spec. |
| S2 | **Forecourt trees and two streetlights grew through the canopy roof.** | **Fixed.** Moved out from under the canopy and replanted across the road on the far verge; the road now reads as an avenue. Before/after: `Captures/X1_*` vs `After/X1_*`. |
| S3 | **Two shuttle buses crossed in an X; doubled kerbs, taxis, benches, lights.** These were my Pass46 placements on top of instanced scenery that Pass46's actor-only inventory never saw. | **Fixed.** 31 duplicates removed (`Fix47.json`). |
| S4 | A planter sat dead centre in the concourse alcove mouth (mine, Pass46). | **Fixed.** Removed. |
| S5 | Long corridors (public return 23 m, landside) are bare walls end to end; they feel more hospital than airport. | **Fixed.** Five backlit destination posters (Azure Bay, Highlands, Coral Coast) on the airline's screen frames (2.5 x 1.3 m, z 1.28-2.62), three along the public return and two in the landside corridor (`After2/P1..P3_*`). |
| S6 | Gate 08 seats six near-identical passengers shoulder to shoulder in one row. | **Fixed.** One moves to the free seat on the north bench; one stands at the glazing watching the aircraft, standing proxy with them (`Gate08_47.json`, `After3/G1_*`, `G2_*`). |

## Models and signage (402 models inspected)

| # | Finding | Status |
|---|---|---|
| M1 | **Two flight boards hung backwards** (mine, Pass46); the landside one read as a dead black panel. | **Fixed.** Turned 180; both now show Departures to the room (`After/Z07b_*`, `After/Z13b_*`). |
| M2 | **The arrivals reclaim board said DEPARTURES** (mine, Pass46). | **Fixed.** New Arrivals screen in the house style (calibrated against the original within 1 px), new screen material, new display role (`After/Z31b_*`). |
| M3 | **Sign arrows overprint text** on narrow signs: 'START HERE / CHECK-IN' and 'CAFE / CLOUD NINE'. Root cause in `architecture38._sign`. | **Fixed in game and in source.** New faces for the two signs mount 2 cm proud of the old ones, same laminate and type, only the clashing line moved off the arrow (`After2/S1_*`, `S2_*`); the builder fix carries it into the next rebuild. |
| M4 | Real-world sizes. | **Checked, fine.** 56 meshes against real ranges; every flag was a naming false positive (oven doors, bin doors, gear doors). |

## Ambience

| # | Finding | Status |
|---|---|---|
| A1 | **The airport was silent** between interaction beeps: no room tone, crowd, announcements or outdoor sound. | **Fixed.** Five original loops (room tone, crowd, outdoor, apron APU, PA with chime and four announcements in Windows' offline voice) mixed by where you stand. Verified in-game at ten places (`VerifyAudio47.json`): right context everywhere, all five playing, crowd scaled by room (check-in 0.75, toilets 0.15). Loops checked seam- and click-free. |

## Gameplay found while testing

| # | Finding | Status |
|---|---|---|
| G1 | **A bag dropped in the cockpit falls out of the aircraft in flight.** The cockpit floor is a paper-thin triangle mesh teleported ~1.7 m a frame; the cabin floor is a solid box and holds. | **Fixed.** A hidden `COL_` floor box (the aircraft's own proxy idiom) under the cockpit floor, flying with the aircraft; traced as the first floor in 1,430 cockpit cells at z 0.000. |
| G2 | **A carried bag can snag in the cabin aisle** (seen at the business suites) because it is held 1.25 m ahead at chest height. | **Mitigated.** Aboard and on foot, the bag is held 0.7 m ahead at hip height. Result: see the journey runs in `LEDGER.md`. |
| G3 | The player is a floating 0.70 m sphere at chest height (P46-018). | **Open by choice.** A design decision. |

## Round 2 sweep (after every fix above)

All 40 player-eye stills retaken (`Captures/`, contact sheets `sheet_0.png`,
`sheet_1.png`; round 1 kept in `Captures/round1/`) and the reach flood-fill
rerun (`Critique47_reach.json`). Reach is unchanged room by room except the
two poster corridors (public return 96 -> 91%, landside 92 -> 89%): the
lightboxes stand 11 cm off the wall, so the 0.35 m player sphere loses one
grid row along them. Nothing became unreachable.

| # | Finding | Status |
|---|---|---|
| R2-1 | **The security repack room** (x -36..-32, y 0..10) was bare panel on every wall: a counter, two seats and a case. | **Fixed.** Two more lightboxes, Highlands on the south wall and Azure Bay above the charging counter (`After3/Z11_*`, `Z11b_*`). |
| R2-2 | `Z10_security_back` shows giant red letters filling the frame. | **Not a defect.** The fixed camera stands a few cm from a lettered wall panel; the same frame as round 1, nothing changed there. |
| R2-3 | `Z17`/`Z19` (gate backs) are mostly the backs of seated heads. | **Not a defect.** The fixed viewpoint is behind the seat rows. |

## Corrections to Pass46

- **The forecourt was not bare.** Its landscape existed as instances inside
  `Airport instanced architecture and fittings`. Pass46 counted actors only,
  so "the forecourt held four objects" was wrong, P46-002 (the repeated
  tree-bench-light group) should not have been withdrawn, and 31 of my 35
  forecourt placements were duplicates. All removed.
- Three Pass46 boards: two hung backwards, one showing the wrong content.
