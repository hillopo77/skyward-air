# Pass 45 — jetbridge containment, confirmed

Written 2026-10-30. **131 confirmed walk-off points** on the jetbridge, found
independently and verified with the game's own floor resolver and with native
captures.

The headline image is `Captures/E7_cab_north.png`: a view from inside the
docking cab at eye height, looking north. There is no wall, no railing and no
glazing. The deck ends at a bare edge over the apron, with the aircraft engine
and gear visible straight ahead.

---

## 0. Two method errors I made first, and what they cost

Recorded because both produced confident wrong numbers, and because the
handoff asks that agent judgments be distinguished from established facts.

**Error 1 — the 418 "escapes".** My first containment audit teleported the
player pawn to the bridge centreline and attempted swept lateral moves with
`set_actor_location(..., sweep=True)`. It reported 418 escapes out of 436
samples, every single one travelling the full 4.0 m push.

A capsule never blocked anywhere, in any direction, is not a plausible defect
distribution. The diagnostic in `Collision45.json` settled it: the same
capsule trace blocks against bridge walls with simple collision everywhere
tested, and the pawn query returned
`'NoneType' object has no attribute 'get_scaled_capsule_radius'`.

**The player is not a Character and has no capsule.** It is a pawn with
`FloatingPawnMovement` under a plane constraint. Sweeping its root does
nothing. All 418 results were an artifact. Discarded.

**Error 2 — the 16.12 m² of "uncovered deck".** I rasterised the bridge deck
in-engine (8761 cells of real deck geometry) and compared it against the
`Bridge38 *` entries in `D['floors']`, finding 16.12 m² of deck with no
covering polygon in four long strips down both edges of both banks.

Two things were wrong with treating that as the defect. First, those
`D['floors']` entries are dead: `airport_journey38.py:458` explicitly excludes
every floor whose name starts with `Bridge38 `, and the runtime builds its own
from `D['aircraft38']['bridge']['floor_polygons']` instead. (They happen to be
byte-identical, so the measurement survived, but the reasoning did not.)
Second, and decisively, `update_floor` has a physical fallback: when no
authored floor is found it traces 0.42 m down for real geometry before
applying gravity. Those ~0.37 m strips of deck beyond the polygon edge are
caught by that fallback. They are benign.

Both errors came from inferring behaviour from geometry instead of asking the
running game. The confirmed findings below do the latter.

---

## 1. There were never any jetbridge containment probes

`D['repair38']['perimeter_probes']` holds 7 probes. `flow39_probes` holds 48.
I read all 55. **Not one of them is on the jetbridge.** They cover the east WC
wall, the west security wall, two baggage windows, two "no partition" checks,
29 sealed-roof steps and a set of doorway head-height pairs.

The handoff says "existing bounded bridge checks did not catch every route".
The actual position is that bridge containment was never probed at all. It
rested entirely on the single centreline walk in the journey test, plus two
still captures (`28_BridgeInside`, `29_DockingJoin`).

A centreline walk cannot find a missing side wall. This is why the defect
survived every pass that reported success.

---

## 2. How containment actually works

Worth stating, because it is not engine collision and that misleads.

- The player is a `FloatingPawnMovement` pawn with a plane constraint locked
  to the current floor height.
- Each tick `airport_journey38.update_floor` resolves a floor by calling
  `floor_at_source`, which tests authored floor zones.
- Authored zones are tested by **rect** in `skyward_runtime.floor_at_source`;
  the bridge zones additionally carry a `polygon`, handled through
  `journey_logic38.choose_floor` and `airside_math38.in_polygon`.
- If no authored floor is found, `update_floor` line-traces 0.42 m down for
  physical support.
- If that also finds nothing, it accumulates `fall_velocity` and the player
  falls.

So containment is: polygon floors, then a short physical trace, then gravity.
Walls are the only thing preventing the player from reaching a point with no
floor. Where a wall is missing, nothing else stops them.

---

## 3. The confirmed test

`walkoff45_probe.py` takes each candidate from the wall probe and, for
outward steps of 5 cm to 1 m, asks three questions:

1. **Reachable** — is a horizontal trace at waist height (0.95 m) from 0.18 m
   inside the polygon edge to this point unblocked?
2. **Floor** — what does the real `airport_journey38.floor_at_source` return?
3. **Physical** — does `update_floor`'s 0.42 m fallback find support?

A point that is reachable, has no authored floor and no physical support is a
confirmed walk-off. Of 174 candidates:

| Result | Count |
|---|---:|
| **Confirmed walk-off** | **131** |
| Blocked by a wall (correctly contained) | 12 |
| Supported by floor or physical geometry | 31 |

### Where they are

| Bridge part | Confirmed | Note |
|---|---:|---|
| Cab mitre | 45 | both outer faces, the largest cluster |
| Pivot chamber | 26 | both outer faces |
| Bank A | 21 | far end, at the elbow |
| Docking cab | 17 | north face — see `E7_cab_north.png` |
| Bank B | 11 | both ends |
| Elbow chamber | 10 | inner face of the dogleg |
| Terminal neck | 1 | corner sample, low confidence |

Largest contiguous clusters:

| Part | Samples | Extent | Floor ends at |
|---|---:|---|---:|
| Cab mitre north | 28 | x 8.95..11.64, y 1.64..2.10 | 0.05 m |
| Cab mitre south | 17 | x 10.00..11.58, y -1.03..-0.76 | 0.05 m |
| Pivot north | 16 | x -12.08..-10.61, y 1.59..1.88 | 0.05 m |
| Docking cab north | 13 | x 10.50..11.60, y 1.93 | 0.05 m |
| Bank A north (at pivot) | 11 | x -11.64..-10.71, y 1.44..1.82 | 0.05 m |
| Bank A outer (at elbow) | 10 | x -2.52..-1.86, y -4.74..-4.50 | 0.05 m |
| Pivot south | 10 | x -12.55..-11.67, y -1.05..-0.88 | 0.05 m |
| Elbow inner | 10 | x -1.90..-1.00, y -1.87..-1.85 | 0.05 m |

**The pattern is clear: the three articulated chambers — pivot, elbow and cab
mitre — plus the docking cab are open along their outer faces.** 88 of the 131
confirmed points are on those four parts. The straight sleeve runs of bank A
and bank B are mostly contained; their failures are at the ends, where they
meet a chamber.

In 55 of the 131 cases the floor ends 5 cm outside the polygon edge, i.e. the
deck stops exactly where the authored floor stops, with no wall above it.

---

## 4. Visual confirmation

- `Captures/E7_cab_north.png` — from inside the docking cab at eye height.
  No wall on the north side. Clear view over the apron to the aircraft engine
  and main gear. The teal deck ends at a bare edge.
- `Captures/E3_elbow_outer_exterior.png` — the elbow from outside. The outer
  cover reads as a plain flat slab laid across the joint rather than modelled
  structure, and the glazing does not continue through the corner.
- `Captures/E1_elbow_outer_inside.png` — the same corner from inside. A black
  slot runs along the base where the wall panel fails to meet the floor, and a
  dark wedge opens where the elbow wall meets the bank wall.

---

## 5. Why this is one defect, not 131

The chambers are the parts that articulate. Their wall geometry appears to
have been authored for the joint itself rather than as a continuous enclosure,
so the floor polygons were extended through the chambers while the walls were
not. Repairing this means giving the pivot, elbow, cab mitre and docking cab
continuous side enclosure that follows their floor polygons through the full
range of deployed poses — not patching 131 points.

The acceptance test is the probe chain in this folder, which is re-runnable:

```
Run-Wall45.ps1       perimeter openings
Run-Walkoff45.ps1    confirmed walk-offs using the game's own resolver
Run-Verify45.ps1     captures at the known spots
```

A repair is complete when `Walkoff45.json` reports zero confirmed points with
the bridge both stowed and deployed, and `E7_cab_north.png` shows enclosure.

**Not yet established:** these runs were all with the bridge in its deployed
pose. Stowed and mid-motion poses are untested, and `floor_enabled()` gates
the bridge floors by state, so mid-stow behaviour needs its own check. I have
also not tested whether the player can reach the open edges while carrying
luggage, which changes movement.

---

# REPAIR APPLIED — 2026-10-30

## Result

| | Before | After |
|---|---:|---:|
| Perimeter samples open at all four heights | 229 | 76 |
| **Confirmed walk-offs** | **131** | **1** |
| Correctly blocked by a wall | 12 | 9 |
| Supported by floor or geometry | 31 | 30 |

The single remaining point is `Bridge38 docking cab` at x = 13.916, normal
+X — the **aircraft doorway**. That opening is authored and must stay open;
it is where the player boards. Containment is complete everywhere else.

## What was built

Twelve joint-closure panels, `SM_AP_P45B_Closure00..11`.

The chambers already carry Shell and Glass geometry; the openings were at the
**junctions between parts**, not along whole edges. So the repair is a set of
small panels at those junctions rather than new walls down the polygon edges,
which would have doubled up against walls that are already there. Total added
enclosure is 16.4 m.

Each panel follows the existing sleeve language so a closed junction reads as
the same structure rather than a patch: trim kick, solid shell wall, the teal
band at the sleeve's height, a glazed upper section on steel mullions, and a
trim header. 234 cm tall, 11 cm thick, bevelled edges.

Pipeline: built headless in Blender from factory-empty data
(`build_closure45.py`), exported per-panel at the origin with no baked
rotation, imported with the project's own FBX flags, assigned the project's
existing `MI_AP_P38B*` materials rather than FBX copies, collision set to
`UseComplexAsSimple` to match the rest of the bridge, and each panel attached
to the bridge part it closes with `KEEP_WORLD` so it follows the deployed
pose without a doubled transform.

**The 614 MB airport master was not opened or modified.** These are new
standalone assets, which keeps the repair reversible and avoided a long
rebuild. The level was backed up before every mutation.

## Two bugs found and fixed during the work

- FBX paths were recorded relative to Pass45 while the engine's working
  directory is elsewhere, so every import silently failed with
  "Can't find file". Resolved to absolute at import time.
- The first export baked each panel's yaw into its mesh, and the importer
  then applied the yaw again. Caught by comparing imported bounds against the
  authored dimensions: a 309 cm panel came in 63 cm "thick" instead of 11 cm.
  Panels are now exported unrotated at the origin. Bounds now match the
  authored length exactly, with 11.0 cm thickness and 234.0 cm height.

## Regression check: boarding still works

Full entrance-to-airborne route, run twice: **166 of 167 checks pass** both
times. The single failure is unrelated to this repair — see P45-008 in the
ledger. The bag's own trace proves it: in the failing run it is abandoned at
(-47.31, -0.14), which is the security area, and it never reaches the bridge
corridor at all.

## Not yet established

- All runs were with the bridge **deployed**. Stowed and mid-stow poses are
  untested, and `floor_enabled()` gates the bridge floors by state.
- The panels were not checked against the bridge's full articulation range,
  only its current pose.
- Visual fit at the panel-to-existing-wall joins has been reviewed in one
  capture (`E7_cab_north.png`), not across all twelve.
