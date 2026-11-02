# Pass51: the landside hall, made legible and lit

Player feedback on Pass50: walking in felt like "a high school gym hall".
There was no clear route, the START HERE / CHECK-IN sign wasn't liked, things
were scattered everywhere, and the lighting was really bad.

## What was wrong
- **Route.** The journey is: door (west) → queue → desks (far east end) →
  back north-west to the security door. Nothing showed the second half. The
  security door had no sign at all from inside the hall.
- **Signs.** A free-standing START HERE board stood in the middle of the
  entrance view, and its arrow pointed sideways at desks that were straight
  ahead.
- **Signs read backwards.** Two signs were seen from behind in mirror
  writing: the one-sided SELF CHECK-IN panel over the kiosks, and the old
  facade lettering "SKYWARD AIR". Raising the hall had put that lettering
  inside the new hall (0.3 m in from the west wall at 4.4-4.9 m), so it showed
  backwards through the clerestory.
- **Lighting.** Exposure is pinned at EV 6.5 for the whole level (Pass45
  removed the white-out at the doors that way). The room grade volumes add a
  uniform "ambient cubemap" fill that lights every surface the same. Twelve
  identical downlights added an even wash on top of that, and the near-white
  terrazzo bounced it all back. The result was flat, white and shadowless:
  the gym look.

## What changed
Scripts are in `Pass51/`. Nothing the journey walks through or uses was moved.

### Layout and wayfinding (`fitout51_blender.py` → `SM_AP_P51Fitout`, no collision)
- **Floor route.** A navy carpet runner with gold edges. Leg 1 runs from the
  entrance door down the middle of the queue lane to the desks. Leg 2 runs
  north from the desks, west along the hall, and into the security door. Warm
  flush "runway" lights run along its centre line, and gold chevrons point
  the way.
- **Check-in gantry.** It hangs over the runner just past the information
  desk. Facing the door: `1 CHECK-IN · BAG DROP ↑`, with "Information and
  self check-in on your left". Facing back: `EXIT · TAXIS · CAR PARK ↑`.
- **Check-in canopy.** An oak canopy over the desks and belts at 3.9 m. It
  gives check-in a human-scale ceiling inside the 6.6 m hall. Lit opal panels
  sit underneath, and the fascia reads `1 CHECK-IN · BAG DROP`.
- **After check-in.** A sign reads `← 2 SECURITY · GATES` with "Have your
  boarding pass ready" (and `1 CHECK-IN ↑` on the back).
- **Security portal.** An oak portal round the screening door. Its navy
  header reads `2 SECURITY`, with "All gates · A07 · A08".
- **Self check-in.** The old one-sided panel is replaced by a two-sided
  `SELF CHECK-IN` sign.
- **Zones.** A sand-stone border runs round the hall, and oak flooring sits
  under the check-in canopy. An oak cove ledge runs along both long walls and
  hides the ceiling uplights.
- **Removed (`cut51_blender.py`, `reimport51_editor.py`).** The START HERE
  face (`SM_AP_P47SignFaces`, 2468 faces) and its board and posts
  (`Hall50.json` extras, retired). The one-sided self check-in panel
  (`SM_AP_RetainedCraft38`, 64 faces). The inside-out facade lettering and
  its frame (`SM_AP_P47Facade`, 5044 faces). Each cut was aimed using a
  piece listing (`Cut51Report.json`) and removed exactly the listed pieces.
- **Rooftop sign.** It got a navy back board, so it no longer reads backwards
  from behind.

### Lighting (`lights51_editor.py`, `Lights51.json`, `glow51_editor.py`)
- **Exposure.** Stays at the level's EV 6.5, so the doors don't pop.
- **Hall grade.** Applied to the hall's three room volumes:
  - ambient fill 0.26 → 0.17
  - warmer white balance (5600 K)
  - vignette 0.3
  - stronger ambient occlusion (0.75, 1.4 m)
  - bloom 0.25
  - The volumes blend over 4 m, so leaving the hall is gradual.
- **Downlights.** The twelve hall downlights are now 3000 K at 85% output.
- **New lights** (labelled `P51 …`, folder `Lighting/Pass51`):
  - spots on both desks, both belts, the queue, the entrance mat, the
    information desk, the kiosks and the security portal;
  - a wash on the check-in back wall;
  - a warm glow under the canopy;
  - ten uplights on the cove ledges washing the wave ceiling.
- **Glow materials.** New finishes that actually glow at EV 6.5:
  `MI_AP_P51SignGlow` (lettering), `MI_AP_P51Soffit` (canopy panels) and
  `MI_AP_P51Runway` (floor lights). The old LED and opal finishes read as
  flat grey.
- **Terrazzo.** Tinted warmer and a little darker (`MI_AP_P43TFloor` Tint
  1.0 → 0.76/0.71/0.64). Every terminal floor uses it.
- **Originals.** The original light, volume and floor values are in
  `HallLights51.orig.json`. A re-run of `lights51_editor.py` sets absolute
  values rather than compounding.

### Pipeline fixes
- **`import_mesh48.py`.** A re-import into an existing mesh keeps the mesh's
  old slot names, so renamed materials were silently not applied. Slots that
  match no build material now fall back to the FBX order.
- **`hall50_blender.py`.** `HALL50_ONLY=1` rebuilds just `SM_AP_P50Hall`,
  without re-cutting the shell.

## Restore
- **Earlier looks.** `Look50` (before this pass) and `Look49` are in
  `SkywardAir/Snapshots`; use `Restore-Look.ps1 -Name Look50`.
- **Per-asset backups.** In `Pass51/Backup/assets`; the level backups are
  in `Pass50/Backup`.

## Pass52: soft, coherent lighting
Player feedback on Pass51: the lighting was super uneven and harsh. Light
came from sources where there obviously shouldn't be one, which was
confusing and gave weird shadows.

### Causes (all from Pass51)
- **Spotlights from nowhere.** Nine spotlights hung in mid-air with no
  fixture. Their 4 cm sources made hard-edged pools and hard shadows.
- **Wall streaks.** The ten uplights sat against the walls and painted bright
  streaks up them.
- **Light through walls.** The canopy glow and the back-wall wash cast no
  shadows, so they reached through walls into the rooms next door.
- **Blown-out panels.** The canopy panels glowed hard enough to blow out to
  white.
- **Stacked crisp shadows.** The 12 ceiling lights each cast a crisp shadow,
  so every person had several.

### Fix (`Lights51.json` 'downlight', 'rects'; `lights51_editor.py`)
- **Spots removed.** All nine are gone. Every light now comes from something
  you can see: the ceiling light channels, the canopy soffit, the cove ledges
  and the portal header.
- **Ceiling lights.** The 12 are one even set: 7000 lm, 3000 K,
  240 x 40 cm panels, with soft shadows (shadow map resolution x0.35 filters
  to a soft edge). They are no longer at mixed strengths.
- **Canopy, back wall, portal.** The canopy glow (3200 lm), the back-wall
  wash (3500 lm) and a light in the security portal header (1600 lm) all cast
  soft shadows, so none of them reach another room.
- **Uplights.** Four wide uplights per side (6 m, 3000 lm, 2800 K) sit at
  the ledge edge, tilted about 13 degrees off the wall onto the wave ceiling.
  They face upward, so they can't reach the lower rooms next door.
- **Canopy panels.** Emission 40 → 5, so they glow instead of blowing out.
- **Hall fill.** 0.17 → 0.20, so it is evenly lit between the light sources.
- **Exposure.** Still EV 6.5.
- **Previous spec.** Kept in `Backup/Lights51.applied.json`.

### Not from this work
- **Broken gate agent.** The gate A07 agent (yellow pilot character) renders
  as a stretched red smear across the room in the 07:45 photos. In the Pass50
  photos the agent stands normally. At the same time another tool was
  changing the project's character runtime (`Content/Python/init_unreal.py`,
  `character_pack_runtime.py`, `friend_action03_*.py`, `FriendAction03/*`
  assets, 07:16-07:44) and running its own Unreal sessions. Those files
  were not touched here.

## Pass53: one warm, even fill (and the lag)
Player feedback on Pass52:
- It was not good lighting: weird things in the corners and at the very top.
- Three large, extremely bright panels at check-in.
- Not cozy or warm: bright, messy, uneven.
- It should blend everything in the room together and be soft and natural.
- It was very laggy.

### Causes
- **Glaring panels.** The three panels were the glowing soffit panels under
  the check-in canopy.
- **Corners and top.** Three separate things were lighting the upper part of
  the room:
  - the cove uplights painted bands up the walls;
  - direct sun through the clerestory threw hard orange patches on the wave
    ceiling, the upper walls and the floor;
  - the ceiling lights sat among the wave slats and flared the slats beside
    them. A show-flag test proved this: the flares vanish with rect lights off.
- **Not warm.** White balance was set the wrong way. In Unreal, `white_temp`
  below 6500 cools the image, so 5600 had made it bluer.
- **Lag.** Pass50 gave every light it lifted into a tall room a 16 m reach,
  and each one re-rendered shadows for everything in that reach.
  - Measured with `Open-Airport38.ps1 -Performance`: check-in 33.8 ms
    (30 fps), concourse 24.1, arrivals 21.9, cafe 19.8.
  - Baseline before Pass50: check-in 20.1 ms, everything else 16.7.

### Fix
- **Accents removed.** All uplights, washes and accent lights are gone. One
  soft glow (1800 lm, unshadowed, 4.5 m reach) remains under the canopy,
  because the canopy shades the desks.
- **Canopy.** Plain oak underneath, with no panels.
- **Room grade.** It now carries the light:
  - warm ambient fill 0.30, tint (1.0, 0.90, 0.76);
  - white balance 7200 K (warm);
  - contrast 0.94;
  - bloom 0.12, vignette 0.18;
  - AO 0.7 at 1.8 m, which blends contact shadows.
  - Exposure is still EV 6.5.
- **Ceiling lights.** The 12 hall lights:
  - 4800 lm, 2900 K, 300 x 120 cm panels;
  - lowered to 5.75 m, below the deepest wave slat, so no slat flares;
  - barn doors at 35 degrees;
  - 9 m reach;
  - soft (0.3) shadows, only on the lights within 3 m of a wall, so nothing
    leaks into the next room.
- **Gates A07, A08 and arrivals.** Their 14 ceiling lights: 9 m reach,
  lowered to 5.65 m, barn doors, softer (0.5) shadows.
- **Sun veil** (`veil53_blender.py` → `SM_AP_P53SunVeil`, "Airport53
  clerestory sun veil"). A shadow-only plane sits behind each of the 16
  clerestory bands. It is hidden in game but casts shadow, so the sky stays
  visible through the glass while direct sun stays out of the tall rooms.
  This is the effect of diffusing clerestory glass.

### Measured after (same probe)
| Room | Frame time |
|---|---|
| Check-in | 17.8 ms (56 fps), better than the pre-Pass50 baseline |
| Arrival, Security, Concourse, Gate A08, Cafe, Cockpit | 16.7 ms (60 fps cap) |

## Pass54: clarity, warm haze, sun shafts, back-to-back seats
Player feedback:
- At a distance things don't look clear.
- Some models look like computer models: very sharp-edged, hard on the eyes.
- The seats in the middle of the hall should be double-sided.
- The lighting should be consistent, hazy and warm through the whole airport.
- Sun rays should shine in through the windows, with light coming from where
  it should.
- Artificial light should complement the outside light.

### Soft edges (`Pass48/mesh48.py`)
- **Round-overs.** Every generated mesh (hall shell, fit-out, features,
  exterior, landmarks) is built with the shared `Mesh` helper. It now
  rounds every edge sharper than 40 degrees with a 12 mm, 2-step round-over.
  Shading is smooth, with face-weighted normals, so flat faces stay flat and
  the edges catch a soft highlight.
- **The bug that hid it.** The bevel first did nothing on boxes, because
  boxes are built without face normals. `bm.normal_update()` runs first now.
- **Turning it off.** `MESH48_HARD=1` restores the old hard output.
- **Backups.** Previous meshes are in `Backup/assets54`; the old helper is
  `Backup/mesh48.before54.py`.

### Distance clarity (`rendering38.py`, both copies)
- **Sharper.** `r.Tonemapper.Sharpen` 0.10 → 0.50.
- **Less smear.** `r.TemporalAACurrentFrameWeight` 0.10 → 0.20, so the
  anti-aliasing blurs less across frames.

### One warm, hazy light (`atmos54_editor.py`, `Atmos54.json`)
- **Every room grade.** Twenty `AP38 warm grade` volumes, plus `Checkin33`
  and `Entrance27`, get the same settings:
  - warm fill 0.28, tint (1.0, 0.90, 0.76), 0.30 in the hall;
  - white balance 7000 K;
  - contrast 0.95;
  - AO 0.7 at 1.8 m;
  - bloom 0.12, vignette 0.18.
- **Outdoor grades.** The two unbound outdoor grades get a matching warm
  tint, 6900 K and 0.96 contrast, so outside and inside are one family.
- **Ceiling lights.** All 74 interior ceiling lights are 2900 K warm white,
  matching the late-afternoon sun (5200 K, warm).
- **Haze.** One exponential height fog gives a light warm haze: density
  0.005, falloff 0.25, from 3 m.
- **No volumetric fog.** It was tried and it only showed as an even haze on
  this renderer (DirectX 11, no Lumen), never as beams, so it is off.
- **Originals.** Original values are in `Atmos54.orig.json`.

### Sun shafts (`rays54_blender.py`, `raymat54_editor.py`)
- **Sun allowed back in.** The Pass53 clerestory sun veil is removed,
  so real sun patches fall on the floors again.
- **Built beams.** 50 shaft volumes, one per sunlit clerestory bay of the
  four tall rooms. Each window opening is swept along the real sun direction
  `(0.587, 0.492, -0.643)` and stops at 90% of the way to the floor. Only
  walls facing the sun get them (west and south).
- **Material.** `M_AP_P54SunShaft` is unlit, additive and two-sided, with
  strength 4.5, warm (1.0, 0.78, 0.5). The beam fades in just inside the
  glass, has soft sides, and fades out before the floor. The shafts line up
  with the sun patches on the floor.

### Seats
- **Back-to-back twins.** The two `Landside corridor bench46` benches now
  stand free in the hall, since Pass50 removed the wall they backed onto.
  Each gets a twin 0.66 m behind it, turned 180 degrees, with the same mesh,
  materials and collision.

## Pass55: all lighting stripped and rebuilt as real, baked light
Player feedback on Pass54:
- Things flicker.
- It looks as if every pixel has its own light source, uniformly.
- Light comes from nowhere: in a room with no visible source, and in bright
  patches on the slat ceilings.
- Rays came out of a wall with window recesses but no glass.
- Strip all the lighting and start again with real light.

### Why it looked fake
- **No global illumination.** The renderer is DirectX 11 (Lumen
  impossible on this GPU driver), and every one of the 218 lights was
  movable. So:
  - the movable sky light lit every surface straight through the roofs (no
    sky occlusion without DFAO or Lumen);
  - each room grade added a flat "ambient cubemap" glow;
  - Pass51-54 stacked accents, a canopy glow, a haze and built "sun shaft"
    cards on top. At gate A08 those cards started from a wall band with
    recesses but no glass.
- **Flicker.** The Pass54 sharpening and anti-aliasing changes
  (Sharpen 0.5, current-frame weight 0.2) made thin slats and edges shimmer.

### What it is now (`bake55_setup_editor.py`, `Bake55.json`, `Bake55.ps1`, `usage55_editor.py`)
- **Stripped.**
  - Every Pass51-54 light, the haze and the sun-shaft mesh are gone.
  - The ambient-cubemap fill is off on all 24 volumes, and the grades are
    plain: 6500 K, contrast 1, AO 0.5, bloom 0.15, vignette 0.15.
  - The anti-aliasing and sharpening cvars are back to their pre-Pass54
    values.
- **Real sources only, baked by Lightmass.**
  - The terminal's 74 own ceiling fittings are STATIC area lights, 3500 K.
  - The sun and sky are STATIONARY: baked bounce and sky occlusion, so sky
    light enters only through the windows, with live shadows for people.
  - 4 bounces, 2 sky bounces, baked AO.
  - A Lightmass importance volume covers the terminal and apron.
  - Real sun patches fall through the clerestories. The upper walls are lit
    by bounce.
- **Not baked in place.** Everything the game moves is set MOVABLE first
  (884 actors): the aircraft (it flies), its lights and crew, doors, belts,
  bags and the bridge. Their own movable lights are untouched.
- **Shadow exclusions.** Sky domes, huge ground skirts and hidden collision
  boxes cast no shadow.
- **Lightmap sizes.**
  - 2048 for the walls, floors, the hall shell and the slats.
  - 1024 for the rest of the architecture.
  - Sized by area for props.
  - 2048 everywhere ran Lightmass out of memory on this 16 GB laptop: 15
    worker threads at about 600 MB each.
- **Dense meshes.** Meshes too dense to pack a lightmap take their light
  from a 50 cm volumetric lightmap instead: the slat ceilings, the hall
  shell (it baked black), and props with overlapping lightmap UVs.
- **Reflections.** A sphere reflection capture in each of the 19 rooms.
- **Materials.** All 106 base materials lacked the "used with static
  lighting" usage flag. With baked lighting every surface fell back to the
  default checkerboard until it was set (`usage55_editor.py`). Material
  backups are in `Backup/materials55`.
- **Bake time.** Preview about 6 min.

## Pass56: softer, fuller baked light
Player feedback on Pass55: ugly dark spots here and there, and a lot of
messy shadows on the ground. Suggestion: a few ambient indoor lights.

- **Ambient panels** (`Bake55.json` 'ambient', placed by
  `bake55_setup_editor.py`).
  - 8 large soft ambient panels, baked STATIC: 3 across the landside hall,
    2 each in gates A07 and A08, 1 in arrivals.
  - Each sits 1 m under the ceiling and is up to 6 x 6 m. That size makes
    their shadows almost invisible.
  - 5000 lm, 3800 K, 11 m reach.
  - They fill the spots the fittings and sun miss.
- **Smoother bounce.** Indirect lighting smoothness 1.0 ? 1.3, which evens
  out blotches in the bounced light.
- **Soft sun on the building** (`sunsoft56_editor.py`).
  - The sun's live cascaded shadows drew the window mullions and plant
    leaves as razor-sharp stripes on the floor.
  - The sun's dynamic shadow distance is now 0, so the building and its
    fixed furniture use the baked sun shadow instead. It is soft, with a 5
    degree source angle.
  - People and moving things still get live per-object shadows.
- **Results.** Journey test 170/170. Saved as Look56.

## Pass57: low rooms brighter and neutral, not orange
Player feedback on Pass56: the other rooms (security and so on) are very
dark and much too orange.

- **Panels in every room.** Each room grade volume outside the four tall
  rooms gets soft ambient panels (`Bake55.json` 'room_ambient'), 31 in all.
  - Each sits 0.5 m under the ceiling, one per 7 m of room length.
  - Up to 6 x 6 m, at 55 lm/m�, 4500 K.
- **Neutral fittings.** The terminal's fittings are 4000 K (were 3500 K).
  The tall-room panels are 4300 K.
- **Less orange bounce.** Bounced light keeps 55% of its colour: Lightmass
  indirect lighting saturation 0.55 on all 106 baked and stationary lights.
  The wood slat ceilings and panelling were tinting whole rooms orange
  through bounce. The wood still looks like wood.
- **Journey test.** One run failed a single in-flight physics check, with
  every journey flag true: the carried bag bounced 2.5 m during
  acceleration. Nothing about physics changed. The re-run passed 170/170.
- **Saved** as Look57.

## Pass58: even rooms, a daylit cafe, lit agents, a cabin lit from fittings
Player feedback on Pass57:
- Half of a room dark and half light, inconsistently, and still too dark
  overall.
- Remove the cafe's floating lights. The cafe is still too dark, as if the
  daylight through the glass does nothing.
- In the plane there are no light sources but light everywhere.
- At the check-in bag desks the people are dark.

### Rooms
- **Panel grid.** Each room's ambient panels are now a grid across the
  whole ceiling, in both directions, 5 m apart, each covering 85% of its
  cell. Before, it was one row down the middle.
- **Brightness.** 110 lm/m� (was 55), boosted for high ceilings by
  (height / 3.2)^1.5.
- **Below the slats.** Panels hang under the slat field: 0.6 m down in
  low rooms, 1.2 m in tall ones. In the cafe they had been sitting inside
  the 6.3 m wave slats, which shaded them.

### Cafe
- **Drums removed.** The hanging drum pendants (3 feature drums and 6 light
  drums) are gone (`Ceilings48.json` 'cafe_flush'). The six cafe lights
  that hung in them are moved up to the 6.63 m ceiling, with flush fittings.
- **Glass.** The glazing (`SM_AP_Glazing38`) no longer casts a baked
  shadow. Lightmass had treated the glass as a partial blocker, so very
  little daylight reached inside.

### Check-in
- **Canopy downlights.** Six small round downlights in the canopy soffit
  (fittings in `SM_AP_P51Fitout`): static, 1400 lm, 4000 K. They light the
  desks and the agents under the canopy.

### Plane (`plane58_editor.py`)
- **Orphaned fills removed.** 41 lights were left at the aircraft's old
  position, x = 0, 16 m from the cabin: "Soft indirect fill", "Ceiling
  bounce approximation" and the lower-hold fills.
- **Cove lights.** The 24 cabin ceiling lights hung in mid-air with no
  fitting. Each now sits on the aisle-side top edge of the overhead bins
  (2.47 m) as a 1.3 m x 6 cm strip, aimed down and inward at 55 degrees.
  Each has a glowing strip fitting (`MI_AP_P58CabinPanel`).
- **Flight.** Lights and strips carry the `Skyward:` tag, so they fly
  with the aircraft. Originals are in `Plane58.orig.json`.

### Results
- Journey test 170/170. Saved as Look58.
- Unreal's commandlet log reports the other tool (FriendAction03) still
  runs its own sessions; one overlap delayed a bake.

## Pass59: lights pointing the right way, no black signs, some warmth back
Player feedback on Pass58:
- Wants a mix of the atmospheric feel of the fake lighting and the real
  light.
- Still too dark.
- The check-in lights shine more on the wood ceiling than down.
- Many things, such as the big signs, are bugged and blacked out.

### Causes and fixes
- **Lights pointing sideways (bug).** Every Pass56-58 ambient panel and the
  check-in downlights were spawned with `u.Rotator(-90, 0, 0)`. In this API
  that is roll -90, not pitch, so they all shone sideways: into walls and
  the canopy wood instead of down. Now `u.Rotator(0, -90, 0)`. This was most
  of the remaining darkness.
- **Black signs and props.** Baked lightmaps failed on props with
  overlapping or missing lightmap layouts, so signs, desks and boards baked
  black. Only the building shell and the ground keep baked lightmaps
  (`Bake55.json` 'keep_lightmaps'). The 333 other static props are lit
  from the volumetric lightmap, which cannot bake black.
- **Some warmth back.**
  - A gentle warm ambient fill on every grade: cubemap 0.08, tint
    (1.0, 0.93, 0.82). Much lower than the fake version's 0.26-0.30.
  - Warmer white balance (6900 K) and bloom 0.2.
  - A light warm height fog: density 0.004, warm inscattering.

### Results
- Journey test 170/170. Saved as Look59.

## Pass60: Cloud Nine cafe redesign and sun shafts
Player feedback: the cafe is bad; redesign it as a specialist in aesthetics
and planning, with a 50 million budget. The natural light is not enough for
such big glass walls, so it needs sun rays.

### Design (`cafe60_blender.py` ? `SM_AP_P60Cafe` with complex collision, `SM_AP_P60CafeFloor`)
- **Zones.** The 17 x 18 m glass box was rows of identical tables on bare
  terrazzo. It is now four zones.
- **Window lounge.** On the sunniest floor, between the stair and the
  dining area: a rug, six armchairs facing the west glass, side tables, two
  floor lamps, and two indoor trees in terracotta planters.
- **Library wall.** On the east wall: teal banquettes on oak plinths, with
  floor-to-4.5 m oak shelving of books and plants. A warm light strip runs
  under every shelf, and there are small round tables.
- **Window bar.** An oak counter along the north glass with seven stools.
- **Counter.**
  - "CLOUD NINE � COFFEE & BAKERY" on the gallery front.
  - Three menu boards (coffee, bakery, tea) hung over the counters.
  - Six downlights in the gallery underside: static, 1300 lm, 3500 K.
  - Two floor-lamp lights: 900 lm, 2800 K.
- **Oak plank floor** over the dining area.
- **Unchanged.** The seated passengers and their chairs and tables, the
  barista, the coffee cart, the cup and luggage pickups, the safety station
  and the gallery are untouched. Two spare table sets are hidden; the
  `ImportJobs48.json` 'hide' list records which.

### Sun shafts (`rays60_blender.py`, `raymat60_editor.py` ? `M_AP_P60SunShaft`)
- **Volumetric fog re-tested.** Tried in the cafe at finer resolution, it
  still shows only as an even haze on DirectX 11, never as beams.
- **Built shafts.** 15 shafts, built only from the cafe's real west glass,
  in 1.25 m bands with gaps for the frames. Each is swept along the real sun
  direction to exactly where that sun lands: the floor, or the gallery deck
  top for the bands above the deck.
- **Material.** Unlit and additive, strength 9:
  - fades in at the glass and out at the far end;
  - soft sides;
  - a depth fade where a shaft meets the floor, furniture or the stair
    (60 cm);
  - fades out within 2 m of the camera, so walking through one never shows
    a flat sheet.

### Pipeline
- **Collision.** `import_mesh48.py` jobs accept `collision: complex`
  (complex-as-simple, BlockAll), for furniture.

### Results
- Journey test 170/170. Saved as Look60.

## Pass61: cafe upholstery and shelving
- **Upholstery mesh.** A new `SM_AP_P60CafeSoft` (complex collision) holds
  the armchair shells, loose seat, back and scatter cushions, and the
  banquette cushions.
  - Built apart from the hard furniture so it can be rounded at 4.5 cm with
    4 segments: `mesh48.SOFT_WIDTH` and the new `mesh48.SOFT_SEGMENTS`.
  - Banquette cushions are split into seat and back pieces about 1.2 m long.
- **Shelving height.** The library wall's shelving tops out at 3.75 m (was
  4.5 m), under the wave slats it used to run into.
- **Shelf plants.** Clusters of four smoother leaf masses instead of one
  faceted ball each.
- **Results.** Journey test 170/170. Saved as Look61.

## Pass62-63: cafe fixes, gate lounges A07 and A08, the gallery
Player feedback:
- The library side of the cafe is dark despite the big window; it needs
  natural light and rays.
- The stair is hard to reach, and the couch layout is bad; move it towards
  underneath the stairs.
- Then renovate every lounge with full freedom.
- Later: "I want the best product, not the fastest one."

### Process
Each space was reviewed in-game from several angles and corrected before
being shown. These were caught and fixed in review:
- A07's first feature wall blocked the apron window.
- The gate rugs were the same navy as the floor, so they were invisible.
- Low-sun shafts fogged the dining area.
- The gallery's north armchairs were hidden behind a bench.
- The sunset bar's solid front blocked the view.

### Cafe (`cafe60_blender.py`, `rays60_blender.py`, `raymat60_editor.py`)
- **Lounge.** Moved under the gallery deck (x -48.8..-42.3, y 25.4..29.3,
  2.87 m deck ceiling):
  - a rounded three-seat sofa facing the west glass;
  - two armchairs facing it, a coffee table, a side table and two floor
    lamps (lights 900 lm, 2800 K).
- **Stair.** The foot and its approach are clear. Two trees in planters
  stand against the glass beside the stair.
- **Floor.** Honey oak (`MI_AP_P43TOak`) with a walnut edge, instead of the
  dark red oak.
- **Golden-hour sun.** The sun's pitch -40 ? -22 and yaw -40 ? -10
  (`Bake55.json` 'sun'), at 4300 K. The low sun reaches across the cafe to
  the library wall. This is airport-wide, so the hall and gates get longer,
  warmer light too.
- **Shafts.** Rebuilt for the new sun. Each ray stops at the first surface
  it meets: the floor, the deck top, the north glass or the east wall.
  Strength 4.0, fading out 1.2-5 m from the camera.

### Gate A08 'North Coast' (`lounges62_blender.py`)
- A slatted oak gate wall behind the desk, with 1 m gold "A08" and "NORTH
  COAST � 10:55".
- A sage rug under the bench groups.
- A long planted island with cushioned seat edges and a tree.
- A work bar with six stools and power points along the apron window.
- Two armchairs, a side table and a lamp in the north-east corner, and
  trees in the corners.

### Gate A07 'Azure Bay'
- The apron window stays clear. "A07 � AZURE BAY" goes on the plaster band
  above it.
- Two armchairs and a side table face the glass and the aircraft.
- Power side tables at both bench ends, a sage rug, a lamp and two trees.

### Gallery (Pass63, `SM_AP_P63Gallery*`, lifted onto the 3.17 m deck)
- An open sunset bar with five stools along the west glass.
- A screen of three planted trees along the north glass behind the bench.
- A conversation group of two armchairs and a coffee table facing the
  east bench.
- A sage rug, two lamps and a tree.

### Unchanged
Benches with fitted passengers, gate desks, the boarding door and bridge
control, luggage and cup pickups, the coffee cart, the travel shop, and
every walking route.

### Hidden
- A07/A08: the old sofas, coffee tables, charging tables and plants.
- Gallery: chairs, tables, charging table and planter.
- All listed in `ImportJobs48.json` 'hide'.

### Results
- Journey test 170/170. Saved as Look62.

## Pass64-65: lounges redone, cafe stair turned, jitter line, wall display

### Gate A08 'Viewing Terrace' (`lounges62_blender.py` `a08()`)
- The bench rows are gone. Three oak tiers step up toward the west wall
  (tops 0.45 / 0.90 / 1.35 m, fronts at x -29.15 / -30.05 / -30.95, from
  y 22.5 to 31.3), so every seat sees over the one in front to the apron.
- Each tier has segmented seat pads, lean cushions against the riser behind
  and a few accent cushions. A soft glow strip sits under every nosing.
- Planters break the tiers into bays: tier 1 at y 22.5-23.15, tier 2 at
  22.5-23.15 and 26.6-27.6.
- Behind the top tier: an oak slat wall and a 'North Coast' artwork
  (painted bands, a gold sun, the words NORTH COAST).
- The north end has steps, a window bar with ten stools, a small play-plane
  corner, two armchairs and a tree.
- Thirteen passengers were moved onto the tiers and the bar
  (`npc64_editor.py`, from `Lounge64Seats.json`, checked with
  `npcprobe64_editor.py`).

### Gate A07 'Wave bench' (`a07()`)
- One long bench snakes along the window as a curve,
  `c(x) = 7.55 + 0.7 sin(2 pi (x + 22) / 7)` for x from -21.7 to -15.3. It
  is lofted as a single surface, not tiled boxes.
- Seats along the curve, side tables, a lamp and trees. The gate sign is on
  the band above the glass, so the window stays clear.

### Cafe stair (`stair64_blender.py`, `SM_AP_P64CafeStair`)
- The stair is turned into an L that faces you as you enter. Flight 1
  starts at x -42.9 and rises west; a landing at x -47.7 to -45.3; flight 2
  rises north to the gallery deck at 3.17 m. 18 risers.
- The cafe trees now stand on the floor (`Airport60 cafe tree`, z 0.6 to
  the pot).

### Fixes
- **Inward bookshelf.** Removed; `RetailShelf24_1834` is on the hide list.
- **Jittering line at door heads and around rooms.** This was z-fighting:
  the hall's datum band and trim shared faces with the walls. The trim now
  stands 0.07 m proud (was 0.05; `hall50_blender.py`). `cut51_blender.py`
  `against` found and removed 10 coplanar faces.
- **Wrong-way information stand.** Removed (`Concourse information
  totem46` hidden) and replaced by a flat departures display on the east
  concourse wall (x -26.14, y 11.9).
- **Posters.** Cut out of `RetainedCraft38` where they clashed with the new
  fit-out (`Cut51.json`).

## Pass66-69: the aircraft cabin, lit like a cabin

Player feedback along the way:
- "Soft, very soft light strips on the ground and the roof."
- The strips looked like painted lines; "as if every pixel has its own
  light"; the roof patchy, some bins light sources themselves; shadows harsh.
- Reference: Dear Passengers, where buttons and panels are luminous.
- The roof was far too bright; then "it looks like a rib cage - remove the
  light source from the ceiling".

### Why the cabin looked lit from nowhere (`Look/LX68`)
The same cabin shots were taken with one source switched off at a time
(show flags). With the sky light off, the cabin is lit by its fittings; with
baked bounce, ambient fill, the sun or reflections off, almost nothing
changes. The terminal's sky light is stationary, its shadowing baked; the
aircraft flies, so it is movable and was never in that bake, and to the sky
light the whole cabin was open air.

### What it is now
- **Sky** (`Content/Python/cabin68.py`, every -AirportRepair38 session,
  captures included): while the camera is inside the cabin (a box found from
  the cabin's own lights, so it flies with the aircraft) the sky light fades
  to 10% over ~0.4 s, and back outside.
- **Cabin grade** ('P69 cabin grade', unbound post-process, priority 5000,
  faded in by cabin68): bloom 0.9 (threshold 1), ambient occlusion 0.85 /
  70 cm, white balance 5200 K (the terminal's 6900 K turned the cabin
  sepia), no flat ambient fill, vignette 0.25.
- **No light on the ceiling** (`cabin69_editor.py`, rev 69f): the 24 'Cabin
  broad practical' lights sit tucked under the bins' aisle edge (1.97 m),
  shining straight down onto seats and aisle, 280 x 12 cm, shadowless,
  barn-doored. Washing the ceiling (rev 69a-e) blew it out and lit every
  arch rib; the glowing 'P58 cabin strip' bars on the bin edges are hidden.
  `plane66_editor.py` builds no ceiling strip, glow or fill (CEILING = False).
- **Floor path lights** (`plane66_editor.py`): along both edges of each
  aisle runner (economy +-0.33 m, business +-0.70 m, inside the cream trim):
  a low brushed channel with a glowing diffuser (MI_AP_P69PathGlow, emission
  260, so it blooms at the level's fixed EV 6.5), and a soft warm spill on the
  carpet. The pale line printed down each economy aisle centre (it read as a
  light) is covered with a 3.5 cm strip of the carpet's own material.
- **Luminous details** (per actor, cabin only): read / call keys (warm /
  blue), their indicators, the seat-belt icons, the galley oven and coffee
  lights, the lavatory lamps. At EV 6.5 on-screen = emission / ~110, so these
  run at 55-260.
- **Reading lights** stay skyward_runtime controls (E toggles them):
  cabin68 gives their On state a glowing lens and switches ~40% on as you
  board, except in validation runs. (Rev 69b swapped the lens slot in the
  level instead; the runtime then could not find its control slot and the
  game stopped starting. Caught by the photo run; reverted.)
- **Ceiling heights** for the earlier strips came from an in-game trace
  (`Pass48/ceil66_probe.py`); aisle 17.105 had hit a window wall 0.46 m
  low and now borrows its mirror aisle's height.
- Originals: `Cabin69.orig.json` (lights and every swapped material).

## Pass66: Gameplay66, playful first person (`Content/Python/gameplay66.py`)

This follows the direction agreed in the interview: first person, snappy
and bouncy, a R.E.P.O.-style floaty tether on almost everything, items you
equip in either hand, comedy-only reactions, and a journey with no timer.
It hooks into `airport_runtime.py` with `install()` in `start()` and
`tick()` after the characters. It is off in every automated run (QA,
capture, `-RenderOffscreen`, `-Repair39*`, validation, other tools'
demos), so journey tests and photos behave as before. `-P48_game66*` turns
it on for its own probe.

| Key | What it does |
| --- | --- |
| W A S D | Move. Snappy acceleration (52 m/s^2) and braking (90 m/s^2); walk 4.0 m/s, 2.5 aboard |
| Shift | Sprint 7.2 m/s (4.0 aboard). The FOV kicks from 88 to 100 |
| Space | A springy hop (0.69 m). You land on whatever you hop onto (terrace tiers, benches, tables) and drop off its edge |
| Shift + Ctrl | A cartoon slide: 10.5 m/s easing out over 0.75 s, the eye drops 0.5 m |
| E (on any seat-height surface) | Sit there, turned round as a person would. Space stands you up |
| Hold Left Mouse | Tether-grab a loose object. It floats on a spring in front of you, lags and swings; heavy things sag |
| Mouse wheel | Pull the held object nearer or push it further away |
| Right Mouse | Throw the held object (light things fly further) |
| F | Equip what you hold (right hand first, then left). With nothing held, take the hand item back on the tether. Also works on the airport's E pickups (cups, bags) |
| Right Mouse (hand item) | Use it. A hammer or mallet swings and knocks things flying (BONK); a cup is sipped; anything else is turned over and admired |
| G | Give your right-hand item to the person you are aiming at |
| Q | Toss your right-hand item |

- **Camera.** A springy head-bob tied to speed, an under-damped landing
  squash, a dip when you grab, and a small pop when you throw.
- **Look-at feedback.** A centre dot (`P66 crosshair dot`,
  `M_AP_P66Dot`, no depth test) springs larger and turns warm when it finds
  something grabbable. That object gets a breathing warm rim
  (`M_AP_P66Highlight`, a fresnel overlay material).
- **Legs.** The pawn's collision sits at eye height, so low things never
  blocked you. A knee-height check now stops you at anything taller than a
  0.3 m step and slides you along it; lower things you just step onto.
  Stairs keep their smooth nav slope.
- **Reactions.** Passengers flinch with a quick cartoon duck and a line
  ("Oi! That nearly hit me!") when something flies past. They thank you for
  gifts and complain about bonks. There are no penalties.
- **Sandbox.** Anything that is a separate, simple-collision object under
  about 2.4 m and 2.2 m^3 can be grabbed. Architecture, people, doors, the
  journey's working props and the extinguisher are excluded. Mess stays
  where it lands.

### Loose props (`loose66_blender.py`, `loose66_editor.py`)
44 new separate physics props, so the tether has real things to play with:
- mugs and takeaway cups on the cafe window bar, the round tables, the
  gallery sunset bar, the A08 work bar and the A07 side tables;
- books and magazines on the coffee tables;
- square throw pillows on the library banquette, the cafe sofa and the
  terrace tiers;
- small potted plants;
- a toy plane and two balls in the kids' corner;
- a 'renovation corner' by the departures display: a toolbox, a hammer, a
  mallet and a wet-floor sign.

They spawn simulating with believable masses (a cup 0.3 kg, the toolbox
6 kg) and settle on the furniture when play starts.

### Sounds (`sfx66.py`, `sfx66_editor.py`)
Nine cartoon effects, synthesised locally with numpy (no downloads, no paid
generation) and imported to `/Game/Airport38/Gameplay66/Audio`:
- **Hop:** a boing.
- **Land:** a soft thud, louder for bigger drops. It also plays as the
  'thunk' when a thrown object hits something, pitched by its mass.
- **Grab:** a bloop, lower for heavy things.
- **Throw:** a whoosh. **Slide:** a long whoosh with a squeak.
- **Bonk:** a wood block, for hammer hits. **Clang:** for hammering walls.
- **Sip:** for cups. **Equip:** a double click.

Every play varies its pitch by up to 6%, so repeats never sound identical.

## Pass68: camera feel and the charge throw (from "the grail")
The Crossing engine's first-person code (Desktop, "the grail - crossing
engine code.md") ported into `gameplay66.py`:
- **Camera life** (feel.js HeadMotion): a footfall gait whose stride grows
  with speed; the head rocks with each step, leans into sidesteps and
  corners, lags a push-off and nods on a hard stop or a landing, and breathes
  hard after a sprint; hands lag fast looks. Every effect has a FEEL scale.
- **Aim is separate from the sway**: grabs, throws, hammer hits and the
  crosshair use the true aim, so breathing never moves what you point at.
- **Aim assist**: when the exact aim finds nothing loose, a 9 cm sphere along
  the same line does (a hammer lying flat, a magazine).
- **Sprint FOV** follows real speed (none against a wall).
- **Charge throw**: hold Right Mouse to wind up (the object draws back over
  your shoulder, the crosshair swells, the view leans back), release to
  throw: 20-100% of the old speed, plus your own running speed, tumbling end
  over end, the whoosh louder with the charge.
- The "F equip" hint shows only where F does something.
- Probe (`Pass48/game66_probe.py`): grab, 73% wind-up throw at 11 m/s, hammer
  equipped by aim assist, swing, toss, sit; 0 errors. Journey 170/170.

## Pass70: the player's Pass69 list

### Movement and feel (`gameplay66.py`)
- **Sprint** 7.2 -> 6.0 m/s (cabin 4.0 -> 3.4), slide 10 m/s.
- **Jumps** take off at walking pace at most and steer at 40% acceleration in
  the air: a sprint no longer launches you across a room.
- **Shorter player**: eye 1.62 -> 1.50 m (gameplay only; the NPCs keep 1.62).
- **Hop in the cabin**: a hop rides on top of the flight code's deck snap; the
  hop is taken off before that code runs, or it reads it as a new deck.
- **Lower hold**: the plane's floor picker only accepts a surface within
  0.28 m of the feet, so one long frame on the 42-degree hold stair stranded
  the player in mid-air, and coming back up could leave them at the last stair
  sample. After it runs, the height is re-read from the stair, hold and deck
  geometry, gliding on the stair.
- **Spectator exit**: with no authored floor under you, the floor code used to
  treat your current height as the deck (hovering, air jumps). Now you fall to
  the real ground below.
- **Stairs** in the terminal glide instead of stepping.
- **Walking through stools and desks**: the pawn's collision rides at eye
  height, and the leg check was two thin line traces that slipped between stool
  legs and under desk tops. It is now three 14 cm sphere sweeps (shin, stool
  seat, desk top); loose props are pushed, not walls.

### Grabbing, hands and prompts
- **One rule**: suitcases (the airport's own E / click pick-ups) are held like
  everything else: hold left click. Bag drop still works: the belt accepts a
  bag that rests on it, held by nothing.
- **Springy carry** (damping ratio ~0.35); it lets go when snagged 2.6 m away.
- **The hand** reaches toward the item at arm's length instead of following it.
- **Idle hands** sink out of view; they come up when you aim at something
  grabbable or hold it.
- **Prompts under the crosshair** (`hud70_editor.py`): two centred lines, what
  you can do ('Hold left click  pick up    then F  equip') and what just
  happened, on TextRender actors with a no-depth-test font material and a soft
  drop shadow. The developer-style top-left text is off in play.

### Cabin (`cabin69_editor.py`, `cabin68.py`)
- The overhead controls above the economy seats are gone (300 parts hidden;
  their reading-light / vent / call prompts removed at run time).
- The light comes from visible sources: each of the 24 under-bin lights sits
  just under its own bin (found by bounds; bay seams tolerated) behind a
  glowing diffuser bar, casting shadows, barn doors open (their hard cone edges
  drew an X on the galley wall). The door bay has no bins: dimmer, no bar.
- The upward 'bounce' stand-in is a faint trace (600 lm); exposure EV 6.0.
- The flight deck is inside the cabin box: no light change at the cockpit.

### A08 jitter, play plane, receptionist
- **A08 sign**: the slat wall's black backing sat exactly on the wall plane and
  z-fought the room's cream band (a noisy band behind the slats). It is now a
  thin sheet 1.2-1.8 cm proud of the wall (also behind the terrace).
- **Terrace**: the light strip under each nosing shared the tier front's plane;
  it now stands 2.5 cm proud, under the nosing.
- **Play plane** (`props70_blender.py`): the kit's plain cylinder with flat
  wings is gone; a cartoon play plane (teal fuselage, cream nose and wings, gold
  propeller and stripes, navy canopy, portholes, wheels, oak stairs) sits on the
  kids' mat.
- **Receptionist**: the A07 gate agent is drawn by another tool's character pack
  with its 'Red_Suit' model, whose 1 Nov model update broke the skinning (a
  burgundy sheet across the gate). `fixes70.py` re-dresses that NPC alone in the
  pack's working 'Coat_Character' model; the pack's files are untouched.

### Fire extinguishers (`props70_editor.py`)
A new 6 kg extinguisher (red body, label band, valve head, lever, gauge, hose
and nozzle) on a new floor stand (tray, cream backboard with red border, strap,
red FIRE sign with a flame mark). Each of the five stands stands with its back to
its nearest layout wall and faces into the room (a probe's nearest hit caught
benches and a receiving station, so the layout's wall lines decide).

### Security, the WC passage and the washrooms (`rooms70_blender.py`)
A 50 million brief, built around everything that works (lanes, belts,
scanners, portals, receiving stations, queue, operator, staff door, cubicles,
doors, vanity), with every opening clear:
- **Security, 'calm screening hall'**: sage fabric acoustic bays with brass
  capping above the oak wainscot; a backlit 'SECURITY / SAFE TRAVELS START
  HERE' feature wall with divest pictograms; double-sided lane signs hung over
  both lanes; an oak divest counter per lane with a lit instruction panel; a
  recompose bench with a mirror strip and tray ledge; planters; brass lane
  inlays; a lit SECURITY header over the entry on the corridor side.
- **WC passage, 'gallery passage'**: three backlit landscape artworks with
  picture lights, a projecting lit WC blade sign with pictograms, a bottle-refill
  station, a living green wall, a sunrise mural on the end wall, a teal runner.
- **Washrooms, 'spa washroom'**: walnut slat cladding on the cubicle fronts with
  brass lintels, lit numbers; a sage tile wainscot with grout lines; a
  large-format tile floor; three backlit round mirrors on a stone splashback,
  two globe pendants, hand dryers; a baby-change table; planters.


## Pass 71/72 (2 November): panic lights, security, toilets, extinguishers

Player brief: the bathroom was lazy; the seats outside faced the wall; the extinguishers were badly placed and
modelled; security had no effort in its materials and was hard to see in; the cabin lights should glow, the
cockpit's green and red buttons should light what is around them, and a second line of lights at the ceiling
should be off until a panic, then panicky red while the floor lights stay a lower white. Later: remove the bars
across the cabin ceiling; the toilet side was raw wood; the toilets were too big, make more stalls; the
hand-dryer wall needed improving.

- Measured, not assumed: Pass48/rooms71_probe.py traced every wall and ceiling of security, the WC passage and
  the washrooms (Rooms71.json). Real faces sit 0.09 m inside the layout lines (Pass70 assumed 0.18, so its
  panels floated); the washroom ceiling is 2.8 m; the cubicle back wall is 0.37 m in. The hall's beige wall
  panels have no collision, so cladding in security is a solid 0.14 m slab that covers them.
- Security (rooms70_blender.py security(), rooms71_editor.py): deep sea-green stone cladding with joints, oak fins
  and a light reglet; a cool backlit feature wall with captioned divest roundels; lit LANE blades with a green
  OPEN; slate lanes with light lines and brass footprints; white divest benches. Machines re-skinned (white
  shell, slate tunnel, smoked curtains, glowing green portal LEDs, by slot material, security actors only). Nine
  'P71 security *' lights (two shadowed lines under the ceiling light lines, four wall washers, the feature
  spill, a light in each scanner tunnel). 'AP38 warm grade security' was 6900 K: now 5600 K at EV 6.0.
- Washrooms: five stalls on a 1.3 m module set out from the two real doors (1 accessible and 4 walk-in; 2, 3, 5
  drawn closed with red OCCUPIED lights, since the building's front wall cannot open there); walnut joinery with
  brass reveals, cornice and light line; stalls 1.9 m deep with teal tiles, a concealed-cistern ledge, a lofted
  wall-hung porcelain toilet, brass fittings, grab rails in stall 1. A 5.8 m stone vanity with arched backlit real
  mirrors (MI_AP_P71Mirror, metallic); a built-in amenity wall with lit dryer niches, flush waste slots,
  baby change and a pilaster over the building's old dryer; a teal feature panel. Old vanity, toilets and recycling
  unit hidden (no collision). Cubicle doors walnut with brass.
- Passage: 'WC passage bench46' is an SM_AP_Bench27 (seat faces -Y at yaw 0), so yaw -90 faced the wall: now 90,
  its back 3 cm off the measured wall.
- Extinguishers (props71_*): SM_AP_P71Extinguisher in SM_AP_P71ExtCabinet on walls measured by walls71_probe.py
  (two-height agreement; Station 3 by the near-wall fallback). Bug found: props71 changed only existing actors, so
  save_current_level skipped the save while reporting success; editor scripts now modify() and save_map().
- Cabin (cabin72_editor.py, cabin68.py): the panic line along every aisle at the ceiling, dormant grey glass;
  in a panic (airport_flight39 abort, or cabin68.S['force_panic']) it pulses red at 9000 lm per 5.8 m, the floor
  path lights drop to a lower white, the under-bin lights dim and the cabin sky dims further. Floor glow up-lights;
  bloom 1.3. Cockpit: no material swaps on controls (skyward_runtime finds control slots by material name);
  instead glowing collars and coloured point lights at the status pushlights and emergency buttons, warm lights at
  the side pushbuttons, phosphor green at the radar. The 13 'Cabin frame10' arch ribs are hidden.
- fixes70.py: the gate agent's mesh swap could trip SkeletalRenderGPUSkin 'Index == 1' (one start in about five);
  now hide, swap a frame later, show a frame after.
- Verified in game: photo sets Look/S71, Look/P72, Look/A71; journey 170/170. Slider: Slider71
  (https://claude.ai/artifact/3itPgtZay5Sv8FMZoj2ALq).
