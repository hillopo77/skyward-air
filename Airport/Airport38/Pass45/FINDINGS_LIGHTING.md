# Pass 45 — entrance lighting defect, reproduced with evidence

Written 2026-10-30. Engine from the live session log: **UE 5.8.3, D3D11, SM5,
RTX 3060 Laptop, driver 522.06.**

**Status: reproduced.** The user confirmed the white-out by walking the
entrance in an ordinary play session. A scripted probe then captured the
boundary at 2 cm resolution with the player camera. No repair has been applied.

Evidence in this folder:

- `exposure45_review.py` — the probe (read-only; captures and one JSON only)
- `Run-ExposureProbe.ps1` — launcher; refuses to start if an engine is running
- `Captures/` — 26 native frames, player camera, 2.2 s settle each
- `ExposureProbe45.json` — per-frame position, zone, volume, sha256; live cvars
  and the full post-process volume table
- `LuminanceCurve45.json` — mean luminance of a central crop of each frame

---

## Correction to my earlier source-only reading

My first pass read `Fixes/` and `SourceAssets/`, found no volume created with
`unbound=True`, and concluded that outside the rooms the camera fell back to
engine default auto-exposure at roughly EV 13–15, giving a 7–9 stop cliff at
the doors.

**That was wrong.** The live level contains three unbound volumes that no
longer have creating code in those two directories:

| Label | Unbound | Priority | Exposure min/max | GI method |
|---|---|---:|---|---|
| `Airport clean daylight grade` | yes | 1000 | 6.5 / 6.5 | LUMEN |
| `Airport26 journey overlay` | yes | 500 | -10 / 20 | LUMEN |
| `PostProcessVolume` | yes | 0 | 6.5 / 6.5 | LUMEN |

The highest-priority unbound volume wins outdoors, so exposure outside is
pinned to **EV 6.5**, not auto. Against **EV 6.0** inside a room that is a
difference of **half a stop**, not seven to nine. Exposure adaptation is in
fact disabled almost everywhere in this level, since `min == max` on every
volume that wins.

The symptom is real and the mechanism is still a camera-bound volume boundary.
But the dominant term is not exposure.

---

## What actually changes at the boundary

`AP38 warm grade entrancefoyer` is centred at (-46, -13, 1.8) with half-extent
(2.98, 4.98, 1.8), so its **west face sits at x = -48.98**, 2 cm inside the
authored zone rect and 2 cm inside the entrance portal line at x = -49.0.

Crossing that face, three things change at once:

| | Outside (x < -48.98) | Inside (x > -48.98) |
|---|---|---|
| Winning volume | `Airport clean daylight grade` (prio 1000, unbound) | `AP38 warm grade entrancefoyer` (prio 1538) |
| Exposure | EV 6.5 | EV 6.0 |
| Ambient cubemap | **none** | **0.22, tint (1.0, 0.98, 0.94)** |
| Ambient occlusion | not overridden | 0.22, radius 38 |
| GI method | LUMEN (inert on SM5) | NONE |

The decisive one is the **ambient cubemap**. It is the room's entire fill
light, and it is applied by a camera-bound post-process volume.

This matters more than it sounds, because of how the practicals are built.
`rendering38.py` `light_specs` gives every fixture `direction = [0, 0, -1]`,
and `native38_rendering.py` spawns each as a `RectLight` with `pitch = -90`,
i.e. **facing straight down**. The ceiling therefore receives almost no direct
light. Its entire appearance comes from the ambient cubemap — a term that
exists only while the camera is inside the room volume.

So when the camera steps 2 cm outside, the ceiling and upper walls lose their
only light source and go dark and cold, while the player's body is still
standing in the room.

---

## Measured

26 frames, player camera (not the detached capture camera), 2.2 s settle at
each position so nothing below is adaptation lag. The sweep holds a fixed look
target at (-43.0, -12.5, 1.55) and moves the eye along y = -12.5, so framing
barely changes across the samples.

Mean luminance of the central half of each frame:

| eye x | in grade volume | mean luma |
|---:|---|---:|
| -53.000 | no | 83.38 |
| -52.000 | no | 86.20 |
| -51.000 | no | 86.15 |
| -50.000 | no | 82.71 |
| -49.600 | no | 79.72 |
| -49.400 | no | 78.06 |
| -49.200 | no | 75.95 |
| -49.100 | no | **75.02** |
| -49.050 | no | 96.15 |
| -49.000 | no | 113.02 |
| **-48.980** | **yes** | **118.57** |
| -48.960 | yes | 118.46 |
| -48.900 | yes | 117.50 |
| -48.800 | yes | 116.25 |
| -48.600 | yes | 114.33 |
| -48.400 | yes | 112.41 |
| -48.000 | yes | 109.60 |
| -47.000 | yes | 104.32 |
| -46.000 | yes | 100.16 |
| -45.000 | yes | 91.13 |

**75.02 to 118.57 — a 58% jump in mean luminance over 12 cm of camera travel.**

The ramp occupies x = -49.10 to -48.98, which is exactly the authored
`blend_radius` of 12 cm. That the measured transition width matches the
authored blend radius is the confirmation that the volume boundary is the
cause, not scene content.

At a normal walking pace of about 3 m/s the player crosses that 12 cm in
roughly **40 milliseconds**. A 58% brightness step in 40 ms is the white-out.

Compare `Captures/B_sweep_x-049.100.png` against
`Captures/B_sweep_x-048.980.png`. The two frames show the same information
desk, the same flight information screen, the same START HERE sign, the same
archway and the same extinguisher cabinet. One is dim, blue-grey and murky;
the other is warm, bright and readable.

The straddle pair is the same story over 60 cm: `A5_DoorwayStraddleOut`
at 76.85 against `A6_DoorwayStraddleIn` at 115.17.

---

## The consequence that matters most

Look at `B_sweep_x-049.100.png` on its own. Dark navy ceiling, cold cast,
heavy contrast, murky dado. **That is the "horror lighting" the user rejected
back at the complaint stage** — `complaint_horror_lighting.png` in the
reference pack shows the same character of image.

That look was never actually fixed. A camera-bound warm grade was placed over
the interior, so the horror version stopped being visible *from inside a
room*. It is still exactly what the building looks like from anywhere the
camera is not inside a room volume: the forecourt, the doorway, and the ~4 cm
dead bands at every internal threshold where the inset volumes fail to meet.

The user is seeing both renderings of the same building and reporting the
difference. Both halves of the complaint — "blinding on entry" and "looks
different from outside" — are one defect.

---

## Live settings, read from the running game

The contradiction I flagged earlier between `DefaultEngine.ini` and the
Airport38 profile resolves in the profile's favour. Read back in-session:

| cvar | live value | ini | profile |
|---|---:|---:|---:|
| `r.ScreenPercentage` | **100.0** | 125 | 100 |
| `r.Tonemapper.Sharpen` | **0.100** | 0.2 | 0.10 |
| `r.DynamicGlobalIlluminationMethod` | 0.0 | 0 | — |
| `r.SSGI.Quality` | 3.0 | 3 | — |
| `r.AntiAliasingMethod` | 2.0 (TAA) | 2 | 2 |
| `r.TemporalAASamples` | 16.0 | 16 | 16 |
| `r.Shadow.MaxResolution` | 4096.0 | — | 4096 |
| `...AutoExposure.ExtendDefaultLuminanceRange` | 1.0 | True | — |

So the recorded performance figures are consistent with their stated
conditions, and sharpening is at the intended 0.10. **P45-004 is closed as not
a defect.** The extended luminance range confirms the exposure values are
EV100.

---

## Two further observations from the volume table

1. `Checkin33 warm welcoming grade` (prio 1200, blend 55) is still in the level
   underneath `AP38 warm grade checkin` (prio 1538). It is dead weight today
   because the AP38 volume outranks it, but it holds a different exposure
   (5.9) and would take over if priorities were ever changed. Worth removing
   deliberately rather than leaving as a trap.
2. Every unbound volume sets GI to `LUMEN`, which cannot run on SM5. These are
   inert. Anyone reading the level and seeing "LUMEN" may reasonably but
   wrongly conclude the project has global illumination.

---

## Repair direction (not applied, not yet approved)

The fix is not to brighten the exterior or to widen the blend. It is to stop
the room's fill light from being camera-bound.

1. **Give the fill a world-space existence.** The ceiling needs light that does
   not vanish with camera position: either practicals that actually illuminate
   it (the current ones all face down), a skylight contribution shaped for the
   interior, or baked lighting. On SM5 this is the honest option.
2. **Restore screen-space GI** on the room grades, as revision 32 had it before
   revision 33 turned it off. Cheap, already configured, gives real bounce.
3. **Make the volumes meet.** Remove the 2 cm inset so adjacent room volumes
   share their face, eliminating the dead bands at internal thresholds.
4. **Match the exterior and interior grades** so that whatever difference
   remains is deliberate and small, with a blend radius sized for walking
   speed rather than 12 cm.
5. **Remove the superseded `Checkin33` volume** and the inert LUMEN settings.

Each needs a matched before/after capture from this same probe at the same
positions, plus a separate performance sample, before being claimed as fixed.
The probe is re-runnable and the before-frames are already on disk.

---

# REPAIR APPLIED — 2026-10-30

## What was changed

Native-only edit to the saved map (`light45b_fix.py`), plus the matching
source changes in `Fixes/04_rendering/rendering38.py` and
`native38_rendering.py` so a rebuild reproduces it. The level was backed up to
`Pass45/Backup/` before each attempt.

| | Before | After |
|---|---|---|
| Ambient fill | room grades only, intensity 0.22 | **every grade incl. unbound**, 0.26 |
| Ambient cubemap | constant, `angular_variance: 0` | **vertical gradient**, variance 0.0134 |
| Exposure | EV 6.0 inside / 6.5 outside | **EV 6.5 everywhere** |
| Blend radius | 12 cm | **120 cm** |
| Volume inset | 2 cm per side | **none, volumes meet** |
| GI method | NONE | NONE (see below) |

The decisive change is the first two. The fill now exists on the unbound
grades as well, so it cannot appear or vanish at a camera-bound boundary; and
it carries real angular variation, so surfaces facing up, sideways and down
receive different light. That is what produces form, and it costs exactly the
same as the constant cubemap it replaces: one texture fetch.

## A revision that was tried and rolled back

Revision A restored `SCREEN_SPACE` GI at the revision-32 intensity of 2.0. It
worked visually but cost far too much on this laptop:

| view | before | with SSGI |
|---|---:|---:|
| Check-in | 59.3 fps | **22.5 fps** |
| Concourse | 59.4 fps | 30.2 fps |
| Gate A08 | 59.4 fps | 33.0 fps |
| mean | 59.3 fps | 35.1 fps |

Rolled back. The gradient cubemap gets most of the same visual benefit for
roughly nothing, which is why revision B is the one that shipped.

## Measured result

Entrance boundary, same probe, same positions, 2.2 s settle, central-crop mean
luminance:

| | x = -49.100 | x = -48.980 | step |
|---|---:|---:|---:|
| Before | 75.02 | 118.57 | **+58.0%** |
| After | 106.12 | 104.66 | **-1.4%** |

The 12 cm discontinuity is gone. The whole sweep from x = -53 to x = -45 is
now smooth and monotonic, with no step larger than 2.7% between adjacent
samples anywhere.

Performance, seven airport views, 12 s of ordinary uncaptured runtime each:

| view | before | after | delta |
|---|---:|---:|---:|
| Arrival | 59.2 fps | 59.9 fps | -1.1% |
| Cafe | 58.9 fps | 59.9 fps | -1.6% |
| Check-in | 59.3 fps | 49.8 fps | +19.2% |
| Cockpit | 59.4 fps | 59.3 fps | +0.1% |
| Concourse | 59.4 fps | 59.7 fps | -0.5% |
| Gate A08 | 59.4 fps | 59.7 fps | -0.5% |
| Security | 59.4 fps | 59.9 fps | -0.9% |
| **mean** | **59.3 fps** | **58.1 fps** | **+2.1%** |

Six of seven views are at or above baseline. Check-in is 19% slower at 49.8
fps; that is the one view with a measurable cost and it has not been
investigated further.

## What this does and does not fix

Fixed: the entrance white-out, the inside/outside mismatch, the exposure step
at every internal doorway, the un-graded band where volumes failed to meet,
and the complete absence of directional shading on large surfaces.

Not fixed by this change, and still open: the practicals all still point
straight down, so the ceiling is lit only by ambient; the far landscape is
still bare; and the large blank wall and floor areas are a composition
problem, not a lighting one. The "horror lighting" appearance is gone because
the fill no longer disappears, not because the direct lighting design changed.

**Honest limit:** this was reviewed in still captures and measured
numerically. It has not been walked through in ordinary play by a person.
