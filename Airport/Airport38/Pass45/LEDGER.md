# Pass 45 defect ledger

Started 2026-10-30. Owner: Opus 5 (receiving agent for `Opus_5_5_Handoff`).

Status of this file: **Pass 1 in progress.** P45-001 is now REPRODUCED with
native evidence; the rest remain source-read diagnoses. No repair has been
made to the game. See `FINDINGS_LIGHTING.md` for the full reproduction, and
`Captures/` for the before-frames.

Baseline binding: `Airport_Repaired38.blend` sha256
`52d50fa72e86610db32ca5d89e8e8d8e85e98df39876c74419e2a0a445741610`,
map `/Game/Airport38/L_Airport_Repair38`, layout sha256
`37a70bcaa86e64177a54875e97b291492bfe6f953d4c9be35a03ba41a26ec446`.

---

## P45-001 — Entrance white-out — CONFIRMED, **FIXED**

**Repaired 2026-10-30: the 58% luminance step across the entrance is now
-1.4%**, at a 2.1% mean frame-time cost. Full detail in
`FINDINGS_LIGHTING.md`. Original diagnosis below.


**Severity:** P0. Addresses the user's "blinding on entry / interior looks
different from outside" complaint.

**Where:** `Fixes/04_rendering/native38_rendering.py:107-130` (`apply_native`),
spec in `Fixes/04_rendering/rendering38.py` (`ambient_specs`).

**What the code does:** for every entry in `D['zones']` it spawns a
`PostProcessVolume` scaled to that zone's rect and sets

```
override_auto_exposure_min_brightness = True,  auto_exposure_min_brightness = 6.0
override_auto_exposure_max_brightness = True,  auto_exposure_max_brightness = 6.0
```

Min == max pins exposure to a fixed value for any camera inside a zone.

**The gap:** there are 19 zones, all interior. `forecourt` is **not** a zone,
although 9 lights are assigned to it, and a further 9 lights have `zone: null`.
A grep across `Fixes/` and `SourceAssets/` finds **no unbound post-process
volume**, so outside the 19 interior rects the view falls back to the project
default auto-exposure, which adapts to daylight.

**Why this produces the reported symptom:** the volumes are camera-bound, not
world-space. Standing on the forecourt looking in, the interior is rendered
under daylight-adapted auto-exposure, so it reads dark. Stepping across the
threshold puts the camera inside `entrancefoyer`, which clamps exposure to a
fixed 6.0 — the same surfaces jump brightness in one step. `blend_radius` is
12 cm, so there is effectively no transition. This matches the complaint
exactly, including the "looks different from outside" half, which an isolated
still-image adjustment cannot fix.

**Second-order defect in the same code:** each volume is scaled to
`(x1-x0-.04)/2`, i.e. inset 2 cm per side. Adjacent zones share an exact
boundary (`entrancefoyer` x ends at -43, `checkin` x starts at -43), so every
shared wall and doorway has a ~4 cm band covered by no volume at all. A player
walking through a doorway crosses it in one or two frames and the exposure
falls back to global for that moment. This is a candidate cause of the
reported flicker/instability at thresholds, distinct from the AA settings.

**REPRODUCED 2026-10-30.** The user confirmed the white-out in ordinary play,
and a scripted probe captured the boundary at 2 cm resolution with the player
camera, 2.2 s settle per sample.

**Measured: mean luminance 75.02 -> 118.57, a 58% step over 12 cm of camera
travel**, at x = -48.98 where the `AP38 warm grade entrancefoyer` volume face
sits. The measured ramp width matches the authored `blend_radius` of 12 cm
exactly, which is what identifies the volume boundary rather than scene
content as the cause. At walking pace the player crosses it in about 40 ms.

**My original magnitude estimate was wrong and is corrected.** I had read
`Fixes/` and `SourceAssets/`, found no `unbound=True`, and inferred a 7-9 stop
cliff against default auto-exposure. The live level in fact holds three
unbound volumes created elsewhere; the winner outdoors pins exposure to
EV 6.5 against EV 6.0 inside. That is **half a stop**, not seven to nine.

**The dominant term is not exposure, it is the ambient cubemap.** The room
grade supplies `ambient_cubemap_intensity = 0.22` with a warm tint, and that
is the interior's entire fill light. Every practical is a RectLight pitched
straight down (`direction = [0,0,-1]`, `pitch = -90`), so the ceiling gets
almost no direct light and is lit only by that camera-bound term. Step 2 cm
outside the volume and the ceiling loses its only light source while the
player is still standing in the room.

**Consequence worth noting separately:** the outside-the-volume render is the
"horror lighting" the user rejected earlier. It was never fixed, only covered
by a camera-bound grade wherever a room volume exists. Both halves of the
complaint are one defect.

## P45-002 — Interiors have global illumination disabled and are lit by a flat constant cubemap

**Severity:** P0 (contributes to "everything looks plain / unfinished").

**Where:** `Fixes/04_rendering/native38_rendering.py:124-126`;
`rendering38.py` `write_constant_hdr` and `ambient_specs`.

**What the code does:** every room grade sets

```
dynamic_global_illumination_method = NONE
```

so there is no bounced light indoors. The replacement fill is
`T_AP38_NeutralIndirect`, generated by `write_constant_hdr` as a 64x32 Radiance
image of a single constant value, applied as an ambient cubemap at intensity
0.22 (0.26 in the 6.8 m café). The docstring states its
`angular_variance` is 0.

**Why this matters:** a constant-radiance cubemap delivers identical light from
every direction. It adds brightness but no gradient, so it cannot produce form,
falloff down a wall, or the sense that a surface is near a window or deep in a
room. Combined with GI off, every large flat surface receives a near-uniform
value and reads as an unshaded blockout. The supplied *Dear Passengers*
references get much of their appeal from exactly the opposite: visible gradients
across the ceiling and sidewalls, warm bounce off the floor, and strong contact
shading. The original style bible names this failure directly under "Lighting
mistakes" — "very flat ambient light → no volume or grounding".

**Note:** this is a plausible major contributor to the "plain walls and floors"
complaint that has survived several passes of adding panel detail. If the cause
is the lighting model rather than missing geometry, adding more wall panels
will keep failing to fix it.

**CORRECTED 2026-10-30.** Lumen is not available: the live session log
confirms **D3D11 / SM5**, and Lumen requires SM6. The earlier suggestion to
A/B against Lumen was wrong.

**Traced to a specific regression instead.** Revision 32
(`Lighting32/SourceAssets/native32.py:35`) set the room grade to
`SCREEN_SPACE` GI with a real `indirect_lighting_intensity`, and its QA test
at `Content/Python/lighting32_qa.py:29` still asserts that bounce is enabled.
Revision 33 (`Warm33/SourceAssets/native33.py:41`) flipped that same volume to
`NONE`, and revisions 34, 35 and 38 applied `NONE` to every room. The pass
intended to make the terminal warm and welcoming is the one that removed
indirect light. See `FINDINGS_LIGHTING.md` section 2.

**Verification still outstanding:** restore SCREEN_SPACE on the room grades,
capture a matched A/B, and take a separate performance sample before claiming
it as the fix.

---

## P45-003 — Lavatory VACANT plate interpenetrates the PRIVACY plate, with orphaned fasteners

**Severity:** P1. Reference: `Opus_5_5_Handoff/References/latest_lavatory_privacy_glitch.png`.

**Observed in the supplied image, not yet traced to source:** the VACANT
indicator housing's lower edge and the PRIVACY plate occupy the same space;
the seam between them is a torn band of pixels consistent with either exact
coplanar overlap or true interpenetration. Separately, two small fasteners sit
on the bare door above the VACANT housing, attached to nothing — the PRIVACY
plate has its own four corner screws lower down, so these two are orphans.
The "VACANT" lettering is small enough to alias badly at this distance.

**Not yet established:** whether the band is z-fighting, interpenetrating
geometry, or a texture/alpha defect. The handoff explicitly asks that these be
isolated before a repair is chosen. Both vacancy states and every instance of
the assembly need checking, not just this one door.

---

## P45-004 — CLOSED, not a defect

The ini / profile disagreement on `r.ScreenPercentage` and
`r.Tonemapper.Sharpen` resolves in the profile's favour. Read back from the
running game: `r.ScreenPercentage = 100.0`, `r.Tonemapper.Sharpen = 0.100`.
The recorded performance figures are consistent with their stated conditions,
and sharpening is at the intended value. Closed.

---

## P45-005 — Superseded grade volume still present under the active one

**Severity:** P3, a trap rather than a current fault.

`Checkin33 warm welcoming grade` (bounded, priority 1200, blend 55, exposure
5.9) is still in the level beneath `AP38 warm grade checkin` (priority 1538).
The AP38 volume outranks it so it has no effect today, but it would take over
if priorities were ever reordered. Remove it deliberately rather than leaving
it to be rediscovered.

Separately, all three unbound volumes set GI method to `LUMEN`, which cannot
run on SM5. These are inert and misleading to read.

---

## P45-006 — Jetbridge has 131 confirmed walk-off points — CONFIRMED, **FIXED**

**Repaired 2026-10-30: 131 confirmed walk-offs reduced to 1**, and that one is
the authored aircraft doorway. Twelve joint-closure panels built in Blender
and imported; full detail in `FINDINGS_BRIDGE.md`.


**Severity:** P0. Full detail and evidence in `FINDINGS_BRIDGE.md`.

Verified with the game's own `airport_journey38.floor_at_source`, not inferred
from geometry. Of 174 perimeter candidates: **131 confirmed** (reachable at
waist height, no authored floor, no physical support), 12 correctly blocked by
a wall, 31 supported.

88 of the 131 are on the four articulated parts — cab mitre (45), pivot (26),
docking cab (17) and elbow (10). `Captures/E7_cab_north.png` shows the docking
cab's north side from inside at eye height: no wall, no railing, no glazing,
deck ending at a bare edge over the apron.

The floor polygons were carried through the chambers; the side enclosure was
not. One defect, not 131 points.

---

## P45-007 — The jetbridge was never probed at all

**Severity:** P1, process.

`perimeter_probes` (7) and `flow39_probes` (48) contain **no jetbridge probe**.
They cover WC and security walls, baggage windows, 29 sealed-roof steps and
doorway head heights. Bridge containment rested on one centreline walk in the
journey test plus two stills. A centreline walk cannot detect a missing side
wall, which is why P45-006 survived every pass that reported success.

---

## Method errors made and corrected during this pass

Recorded so the numbers are not reused.

- **418 "containment escapes" — discarded.** Swept `set_actor_location` on the
  player pawn. The pawn has no capsule (it is `FloatingPawnMovement`), so the
  sweep did nothing and every push reported full travel. `Collision45.json`
  shows capsule traces do block against bridge walls.
- **16.12 m² of "uncovered deck" — reclassified as benign.** Real measurement
  (8761 deck cells rastered in-engine), but `update_floor` has a 0.42 m
  physical fallback that supports those ~0.37 m edge strips. Also compared
  against the dead `D['floors']` copy rather than the deployed polygons,
  though the two are byte-identical.

---

## P45-008 — Carried bag intermittently abandoned at security; the frozen build's headline route does not reproduce — CONFIRMED

**Severity:** P0. Found while regression-testing the bridge repair.

The handoff presents a frozen build that passed a 174-check fresh
entrance-to-airborne route. **That does not reproduce.** The route was run
twice here and failed the same check both times, in two different ways:

| run | check | measured |
|---|---|---|
| 1 | Scanned airport bag physically carried aboard in flight | bag 2.93 m from player |
| 2 | same | bag **3366.93 m** from player |

166 of 167 checks pass in both runs, so the route itself completes; the
failure is specifically the carried bag.

**Run 2 traced.** The bag is released at t = 94 s, step 59, at source
position **(-47.31, -0.14, 1.34)** and never moves again. That is inside the
security zone (x -49..-36, y -4..10). The player walks on; by step 64 they are
7.8 m away, by step 72 they are 28.9 m away. The bag is later dragged down the
runway in world space as the aircraft accelerates, which is why the final
distance is kilometres.

**Run 1 is a different failure.** There the bag *is* aboard, resting at
(15.03, -4.29, 1.50) inside the cabin, and only fails a distance threshold
because the player moved 2.93 m away from it.

So there are two distinct intermittent faults: the bag being abandoned during
the security hand-back, and a threshold that fails when a stowed bag is merely
a few metres from the player.

**Not caused by the Pass45 bridge repair.** In the failing run the bag is
abandoned at x = -47.3 and never enters the bridge corridor at x -14..+14 at
all. Both runs were after the closure panels were placed, and the bag reached
the cabin successfully in run 1.

**What this means for the existing evidence:** a saved report asserting the
route passes is not reproducible on this machine today. Treat the 174-check
figure as a record of one run, not a property of the build.

---

## Still to do in Pass 1

- P45-002: confirm the screen-space GI restoration A/B and its cost.
- Bridge: re-test containment in stowed and mid-stow poses, and while the
  player carries luggage.
- P1: lavatory vacancy/privacy assembly, traced to source.
- P1: upper-level cafe and charging furniture.
- P1: unfinished broad surfaces.
- Whole-scene inventory beyond the five examples the user supplied.
