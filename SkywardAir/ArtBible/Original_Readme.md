# Dear Passengers-Inspired Visual Style & Production Bible

**An extensive, implementation-oriented README for creating an original, polished, stylized 3D airline-comedy game with Blender + Unreal Engine 5**

> **Purpose:** Collect the complete visual-art breakdown of *Dear Passengers* and translate its general visual principles into a practical, reproducible art pipeline. This is **not** the official art bible, source code, asset specification, or rendering configuration of FLEXUS. It is an independent analysis and a set of recommendations for developing **your own original game**.
>
> **Research baseline:** 22 October 2026. Official Steam listing, publicly published screenshots/trailer, and public FLEXUS posts. The Steam listing identifies FLEXUS as developer/publisher, 2026 as the planned release window, and co-op/physics/weather as major features. A public FLEXUS post included a screenshot described as being straight from Unity, supporting the statement that *Dear Passengers* is made with Unity. **This guide uses Unreal Engine 5 as a proposed engine for your game, not as a claim about *Dear Passengers*.**
>
> **Honesty key throughout:** **[OBSERVED]** = apparent in official screenshots/media; **[CONFIRMED]** = explicitly described by the developer/Steam; **[RECOMMENDED]** = proposed design rule for your production; **[ESTIMATE]** = approximate numeric starting point, *not* a measured value from the original game.

---

## Table of contents

1. [Executive art-direction statement](#1-executive-art-direction-statement)
2. [What is confirmed, observed, and unknown](#2-what-is-confirmed-observed-and-unknown)
3. [The visual identity, distilled](#3-the-visual-identity-distilled)
4. [Characters: shape language and faces](#4-characters-shape-language-and-faces)
5. [Eyes, pupils, expressions, and hair](#5-eyes-pupils-expressions-and-hair)
6. [Clothing, uniforms, passengers, and crew](#6-clothing-uniforms-passengers-and-crew)
7. [Environment design and aircraft interiors](#7-environment-design-and-aircraft-interiors)
8. [Cockpit, terminals, outdoor scenes, and damage](#8-cockpit-terminals-outdoor-scenes-and-damage)
9. [Colour system and palette](#9-colour-system-and-palette)
10. [Material language and PBR presets](#10-material-language-and-pbr-presets)
11. [Geometry, bevels, normals, and texture density](#11-geometry-bevels-normals-and-texture-density)
12. [Lighting design: daylight, cabin, night, emergencies](#12-lighting-design-daylight-cabin-night-emergencies)
13. [Camera, first-person hands, composition, readability](#13-camera-first-person-hands-composition-readability)
14. [Post-processing, effects, and final image quality](#14-post-processing-effects-and-final-image-quality)
15. [Animation, interaction, and physical comedy](#15-animation-interaction-and-physical-comedy)
16. [Blender: the complete asset-production workflow](#16-blender-the-complete-asset-production-workflow)
17. [Unreal Engine 5: import and visual assembly](#17-unreal-engine-5-import-and-visual-assembly)
18. [Blender → Unreal: exact handoff checklist](#18-blender--unreal-exact-handoff-checklist)
19. [Suggested asset list and naming conventions](#19-suggested-asset-list-and-naming-conventions)
20. [Performance, multiplayer, and scalability](#20-performance-multiplayer-and-scalability)
21. [Quality gates, comparison tests, and acceptance criteria](#21-quality-gates-comparison-tests-and-acceptance-criteria)
22. [Production roadmap and milestone deliverables](#22-production-roadmap-and-milestone-deliverables)
23. [Frequent mistakes and how to fix them](#23-frequent-mistakes-and-how-to-fix-them)
24. [Complete reusable art-direction brief](#24-complete-reusable-art-direction-brief)
25. [Sources, image references, and caveats](#25-sources-image-references-and-caveats)

---

## 1. Executive art-direction statement

**Target aesthetic:** A modern, polished, colourful, physically tangible **3D animated comedy**, with recognisably constructed everyday environments and intentionally absurd characters. Imagine a playful sculpted-figure character cast placed inside a credible, pleasantly lit airline world. It should look like a commercially polished game, *not* an untextured prototype, a low-poly geometry exercise, a pixel-art game, a cel-shaded comic, or a gritty realistic flight simulator.

**Core combination:**

- **[OBSERVED] Simplified, highly stylized characters:** oversized protruding eyes, small mouths, large clean shapes, sculpted hair, and soft round skin.
- **[OBSERVED] More believable environments than characters:** recognisable cabin panels, seats, windows, luggage bins, controls, glass, carpet, and believable object placement.
- **[OBSERVED] Soft-but-volumetric lighting:** convincing highlights, indirect illumination, contact shadows, depth, and clear lighting separation.
- **[OBSERVED] Controlled colour:** pale neutral structure; navy and saturated blue seats/floor; vivid character/prop colour accents; cyan skies and warm hazard lights.
- **[CONFIRMED] Physics-enabled comic chaos:** loose passengers, luggage, and objects interact with turbulence and moving aircraft.
- **[RECOMMENDED] Strong gameplay readability:** characters, interactable props, and hazards should remain recognisable in under a second.

**Golden rule:** Make characters **simpler than the world**, but light and shade both with the same visual language.

**Stylistic one-liner:** *Soft, toy-like cartoon people + clean semi-believable aircraft architecture + attractive contemporary 3D lighting + readable physical comedy.*

### What *not* to build

Avoid a game where everything is angular and faceted; a game whose people have ordinary human eyes; a game with uniformly flat unlit colour; a game whose cockpit has no recognisable structure; a game where every surface reflects like polished chrome; a game where all colours are equally bright; a game whose shadows destroy visibility; or a game where random high-resolution photogrammetry assets clash with sculpted characters.

## 2. What is confirmed, observed, and unknown

### Confirmed by public primary sources

| Claim | Status | Supporting location |
|---|---|---|
| *Dear Passengers* is developed/published by FLEXUS | **[CONFIRMED]** | Official Steam store page |
| It is a first-person airline game with solo and online co-op features | **[CONFIRMED]** | Official Steam listing |
| Players can pilot and/or work in the cabin, serving passengers and handling cargo | **[CONFIRMED]** | Official Steam listing |
| Physics-based passenger/cargo interactions, dynamic weather, turbulence and air pockets are central features | **[CONFIRMED]** | Official Steam listing |
| Public media depicts airliner cabins, cockpit views and stylized characters | **[OBSERVED]** | Official trailer and screenshots |
| The developers have shown a screenshot described as taken straight from Unity | **[CONFIRMED]** | FLEXUS Steam community announcement |

### Interpretation of the media (not hidden developer specifications)

The broad material feel, perceived roughness, proportions, apparent shadow softness, lighting colour, camera wideness, texture simplicity, animation quality, and perceived polygon density are **visual analysis**. A public screenshot cannot tell us the exact light-intensity values, engine shader graph, texture channel formats, skeleton definitions, field of view, polygon counts, real-time global-illumination technology, or Blender usage.

### Unknown—do not invent these facts

- FLEXUS's exact 3D modelling software or whether every original asset was made in Blender.
- The complete art pipeline, render pipeline, shader graph, texture authoring packages, or post-process settings of the shipped/under-development game.
- Exact character polygon budgets, original UV layouts, bone counts, asset textures or rig structure.
- Whether a particular reflection or lighting feature uses a specific Unity render feature.
- Final release-only visual changes or specifications not published in a primary source.
- A confirmed maximum co-op player count from the cited Steam listing.

**Important correction:** Blender is a **3D content creation application**; Unity and Unreal Engine are **game engines**. Blender is absolutely appropriate for making this art style. Your Blender-generated meshes, UVs, rigs and animations can be imported into Unreal Engine 5; the original game's use of Unity does **not** make Blender inappropriate.

## 3. The visual identity, distilled

### The six layers

1. **Silhouette:** clean, smooth, legible shape with large recognisable character features.
2. **Proportions:** large heads and eyes, compact bodies, soft limbs, simplified hands, and recognisable clothing.
3. **Shading:** materially believable 3D response without photorealistic surface noise.
4. **Environment:** credible real-world spatial relationships, rounded architectural details, seats and fixtures.
5. **Lighting/colour:** strong illumination and separation, neutral surroundings, vibrant accents.
6. **Motion:** cartoon characters moving through a physical world with surprising, comedic consequences.

A screenshot passes the style test when the viewer can instantly identify who is a character, what can be picked up, where the plane's boundaries are, what is happening, and why it is funny. It should remain readable as a small social-media thumbnail.

### Relative recreation priorities—not scientific measurements

The following are **[ESTIMATE] subjective art-direction weights**, only to help prioritize production effort:

| Visual ingredient | Suggested weight |
|---|---:|
| Character shape language, eyes and faces | 30% |
| Lighting and materials | 22% |
| Environment shapes and construction detail | 18% |
| Colour organization and contrast | 12% |
| Animation and physical comedy | 12% |
| Camera framing and finishing effects | 6% |

These values are not developer statements and are not a claim of perceptual measurement.

## 4. Characters: shape language and faces

### Broad shape language

**[OBSERVED]** Human passengers have recognisable human silhouettes but strongly distorted cartoon facial anatomy: inflated eyes, simplified cheek and nose structure, sculpted hair, restrained skin detail, and easily readable clothing. Highly stylized crew/avatar characters can be more abstract, with vivid bodies and very simple rounded limbs.

**[RECOMMENDED]** Use rounded cylinders, tapered capsules, ellipsoids and gently bevelled block forms as the basic character vocabulary. Preserve enough landmarks to read the pose, but remove pores, anatomical grooves, realistic tendons and detailed small wrinkles.

- **Head:** larger than naturalistic; broadly rounded, soft cheek transitions, simple jaw.
- **Torso:** compact and simple; avoid complicated muscular volumes.
- **Neck:** subordinate to face; avoid a hyper-realistic, tendon-heavy neck.
- **Shoulders:** rounded instead of mechanically squared.
- **Arms:** clean capsule/cylinder transitions; enough taper for clear hand positions.
- **Legs and feet:** simple, legible forms with visibly planted shoes where appropriate.
- **Hands:** smooth and expressive, with enough finger definition to hold props but no detailed veins or knuckles.
- **Mouth:** small curve, line or shallow cavity; expression relies heavily on eyes and body movement.

### Example proportions for an ORIGINAL passenger [ESTIMATE]

These are modelling **starting bands**, not source measurements:

| Feature | Starting suggestion | Why |
|---|---|---|
| Character height | ~5–6.5 head units | Exaggerated and approachable silhouette |
| Face width | ~0.75–1.0 head height | Broad readable cartoon features |
| Eye pair span | ~45–70% face width, depending on overlap/protrusion | Instantly recognizable expression |
| Hand length | ~0.65–0.9 realistic-proportion equivalent | Emphasize first-person interactions |
| Mouth height | Very small relative to the eyes | Eyes dominate expression |
| Body construction | Few large smoothly transitioning masses | Easy to rig, read and animate |

Do not interpret these as a recipe for copying FLEXUS's proprietary designs. Establish your own unique hairstyles, face silhouette, clothing cuts, colour identities, and character personalities.

### Passenger versus crew hierarchy

**Passenger models:** recognizable shirts, hoodies, floral outfits, trousers, belts, shoes, hairstyle variation and seated posture; more recognisably human anatomy.

**Crew/avatar models:** stronger colour blocking; visually identifiable at a distance; simpler, cartoonier silhouettes; clear readable uniforms, hats and work accessories. First-person arms/hands may be more saturated and abstract than passengers.

### What ruins character cohesion

- Realistic human eyes inserted into an otherwise smooth cartoon face.
- Ultra-high-detail skin scans alongside stylized hands.
- Random low-poly triangular faces on some characters but smooth mesh shading on others.
- Excessively thin limbs that do not support believable rig deformation.
- Poor silhouettes where hair and facial features merge into an unclear shape.

## 5. Eyes, pupils, expressions, and hair

### The eyes are a signature visual device

**[OBSERVED]** Large, prominent, nearly spherical white eyeballs with small dark pupils dominate the face. Round eye surfaces catch smooth specular highlights and create natural 3D shadowing. Simple pupil positions make the same head feel shocked, confused, unnerving or indifferent.

**[RECOMMENDED] eye construction:**

1. Make one clean, nearly spherical eyeball mesh with normal-smooth shading.
2. Duplicate or mirror for the second eye, while preserving some asymmetry in positioning when desired.
3. Allow part of the eyeball to protrude from the face silhouette; avoid fully flattening it into the head.
4. Use a nearly neutral white, not a perfectly glowing/unlit white material.
5. Create small black/dark pupils as a slightly raised surface or eye material region.
6. Set pupils to track targets subtly—not instant random jitter.
7. Add a minimal outer lid/rim only if your original design benefits from it.
8. Validate from front, profile, three-quarter, and extreme close-up camera views.

**Expression system:** neutral, glance left/right, look up/down, surprised, worried, annoyed, distracted. Most can be accomplished with coordinated pupil direction, modest eyelid/mouth shapes, and head turn. Avoid too much micro-animation that makes eyes frantic or nauseating.

### Suggested eye shader [ESTIMATE]

- White base: warm off-white to avoid clipping to pure paper white.
- Roughness: approximately **0.15–0.30** for relatively clear highlights; tune against scene lighting.
- Metalness: **0**.
- Pupil: dark charcoal/black with a clean edge and optional very subtle highlight.
- Eye shadowing: preserve a little shading where eye meets head; do not outline every eye with thick dark ink.

### Sculpted hair

**[OBSERVED]** Hair often reads as a limited number of sculpted clumps rather than individual groomed strands. The silhouette and colour mass matter more than strand simulation.

**[RECOMMENDED] workflow:** build a base helmet-like form matching scalp, create 5–20 broad stylized locks depending on style, bevel/smooth edges, avoid hundreds of thin strands, and separate hair materials into one main shade plus optional subtly darker underside. Sideburns, bangs and curls are especially important silhouette features.

### Facial variation library

Create distinct designs for 8–12 passengers by varying head width, hairline, cheeks, nose bump, eye spacing, pupil size, neck, outfit colour, glasses/hats, and facial expression. Do not rely exclusively on changing clothing colours.

## 6. Clothing, uniforms, passengers, and crew

Clothing should feel like actual garments while staying visually clean.

**[OBSERVED]** Public imagery contains recognisable hoodies, coloured shirts, tropical prints, shorts, trousers, shoes and flight-themed uniforms. Fabric and clothing are simpler than real-world close-up garments; silhouettes carry much of the identity.

**[RECOMMENDED] garment rules:**

- Build garment geometry around a simplified body mesh, with enough clearance to avoid clipping during animation.
- Represent hoods, collars, cuffs, belts and pockets as larger recognizable forms, not needle-thin details.
- Use 1–3 major folds per large region, not realistic micro-wrinkles everywhere.
- Reserve dense prints for a few attention-grabbing outfits; avoid visual noise on the entire cabin cast.
- If using normal maps, keep stitching/cloth weave subtle and only where visible in ordinary gameplay.
- Establish readable role markers: crew cap, tie, badge, colour, nameplate, headset or tool belt.
- Use costume silhouettes that remain distinct even if colours are removed from the screenshot.

**First-person hands:** create a dedicated viewmodel rig when appropriate; foreground hands have separate framing, animation and collision needs from full-body meshes. Use shape exaggeration carefully: larger hand volume and a readable grasp are useful, but hands should not cover the task object or screen center unintentionally.

## 7. Environment design and aircraft interiors

### Why the backgrounds look more complex than the characters

**[OBSERVED]** The airplane cabin feels like an aircraft because numerous real structures are present: curved wall sections, repeating windows, ceiling and lighting panels, storage bins, rows of seats, armrests, carpet, signage and doors. Objects are less exaggerated than the characters; this is central to the style.

**[RECOMMENDED]** Build **structural plausibility**, not a perfect engineering replica. Use repeated modular assets with rounded forms and consistent measurements.

### Cabin art-direction hierarchy

| Layer | Examples | Detail priority |
|---|---|---|
| Primary architecture | Fuselage shell, floor, window wall, ceiling, cockpit opening | Extremely high: defines scene |
| Repeating modules | Seats, windows, overhead bins, wall panels, lights | High: defines texture and rhythm |
| Interaction props | Drinks, trays, luggage, equipment, tools, trash | High: close-up and physics |
| Supporting fixtures | Signs, belts, rails, vents, hinges, trims | Medium: environmental believability |
| Microscopic detail | Screws, tiny seams, fabric grain, unseen components | Low: optional and sparse |

### Recommended modular cabin kit

- Aisle floor section with carpet material and lane/edge accents.
- Window-wall segment with bevelled oval/rounded window frame.
- Ceiling and overhead light strip module.
- Upper luggage compartment module in open/closed states.
- Seat row: shell, blue cushion, armrests, headrests, rails, buckles.
- End-of-cabin door surround and emergency exit sign.
- Cabin partition/cockpit doorway with rounded edge construction.
- Trim and panel modules with subtle shadow seams.
- Modular luggage, drink cups, food trays, extinguishers, and miscellaneous interactables.

### Repetition without monotony

Maintain accurate spacing and alignment of seats/windows. Vary small selected details such as seat fabric tint, luggage presence, passenger outfit or overhead compartment state. **Do not** randomly distort the fuselage or tilt every module simply to create visual noise.

### Interior lighting anchors

White/light grey walls, cool blue seating, dark navy aisle floor, softly glowing upper lights, warmer lower lights and occasional red emergency signage create immediate legibility.

## 8. Cockpit, terminals, outdoor scenes, and damage

### Cockpit

**[OBSERVED]** A denser area than the cabin: clusters of dials, illuminated screens, switches, buttons, throttles, yoke/control surfaces and cockpit framing. Displays and warning lights are graphically clear rather than visually overloaded by microscopic real instrument complexity.

**[RECOMMENDED] modelling rule:** create functional-looking groups with readable hierarchy—primary screens/dials first, secondary switch banks next, tertiary rivets/seams last. Match the cockpit's proportions and ergonomics to your **fictional** aircraft. No need to reproduce an exact real-world cockpit.

**Cockpit priorities:** instrument panel silhouette; glare shield; front windows and pillars; control device and throttles; avionics screen; visible warning/emissive lights; seat profile; a few believable secondary controls.

### Terminal

**[OBSERVED]** Airport environments use open spatial arrangements: tall windows, clear floors, baggage and seating, people, signage and colourful props. Large straight architectural forms contrast with soft cartoon characters.

**[RECOMMENDED]** Build a small, believable gate first: glass wall, tile floor, waiting seats, check-in counter, boarding door, luggage and signage. Prioritize the “airport at a glance” read over massive map size.

### Outdoor and skies

**[OBSERVED]** Bright cyan/blue skies and clouds, colourful greenery/landscapes, smooth-painted aircraft and clear natural lighting contribute to the game's pleasant visual feel.

**[RECOMMENDED]** Use sky atmosphere, directional sunlight, softly separated distant terrain, varied but controlled greenery, and an aircraft livery of 2–3 major hues. Resist photoreal ground scans that overpower the stylized look.

### Damaged environments

**[OBSERVED]** Media includes damaged fuselage/interiors, exposed dark surfaces and structural elements, debris, and more dramatic light.

**[RECOMMENDED]** Implement localized damage variants, not indiscriminate procedural dirt on every wall:

1. Clean intact wall module.
2. Cracked/creased trim variation.
3. Torn-open hole module with thick broken perimeter.
4. Exposed frame/rib and dark interior edges.
5. Small burnt/scorched material decals.
6. Selectable loose panel physics prop.
7. Particle and emergency-light response.

Always preserve rounded stylized geometry and high colour readability even in disaster scenes.

## 9. Colour system and palette

**[OBSERVED]** A consistent relationship dominates: whites and cool greys for walls/architecture; strong blues for seats and aisle; red/yellow/green/blue for characters and highly salient props; sky cyan/blue outdoors; warm red/orange warnings during chaos.

The following hex codes are **[ESTIMATE] illustrative swatches** approximating a matching visual direction, **not sampled official palette values**.

| Role | Sample swatch | Suggested use |
|---|---|---|
| Cabin off-white | `#E6E8E8` | Main fuselage panels and broad surfaces |
| Cool panel grey | `#AEB8C5` | Frames, trim and soft metallic fixtures |
| Deep navy | `#23365B` | Carpeting, shadow accents, dashboard groups |
| Airline blue | `#2476CA` | Seat upholstery and key branded props |
| Crew red | `#D92E34` | A distinct playable character or role |
| Crew green | `#55BE36` | Distinct teammate colour |
| Crew yellow | `#F6D047` | Distinct teammate or high-salience prop |
| Daylight sky | `#83C7EF` | Background sky reference hue |
| Warm caution accent | `#F6A43B` | LEDs, warning equipment, selected highlights |
| Almost-black graphite | `#242936` | Displays, controls and secondary shadows |

### Colour hierarchy [RECOMMENDED]

- **~60–70%** of a typical cabin frame: neutral light/dark environment structure.
- **~20–30%:** stronger blue seating, floor or repeated brand accent.
- **~5–15%:** brightly saturated characters, props, warning lights and other attention anchors.

These are not measured pixel ratios; treat them as a **starting principle**. The ratios can change for outdoor scenes and emergencies.

### Palette mistakes

Bad: full saturation on every surface; pure-white emissive walls; dark-blue shadows so black that geometry disappears; warning-orange light used constantly; background colours competing with eye white and crew colours.

Good: saturated forms against legible neutrals; warm/cool contrast; material-specific brightness; clean white eye read; deliberate attention targets.

## 10. Material language and PBR presets

**[OBSERVED]** Surfaces show volumetric light response and recognizable material distinctions, while texture noise remains subordinate to the geometry. Skin and coloured bodies read like matte/satin sculpted clay or rubber; seat upholstery suggests synthetic material; walls suggest painted plastic; cockpit indicators are brighter/emissive.

**[RECOMMENDED]** Use physically based shaders with **stylized values**. Don't interpret “cartoon” as “unlit.”

### Starter material table [ESTIMATE]

| Surface | Base-colour direction | Metallic | Roughness range | Key treatment |
|---|---|---:|---:|---|
| Cartoon skin | Warm, clean, gently varied | 0.0 | 0.50–0.75 | Soft, satiny highlights |
| Coloured crew body | Rich flat hue, gentle shading | 0.0 | 0.45–0.70 | Smooth rubber/clay |
| White eyeball | Warm off-white | 0.0 | 0.15–0.30 | Bright but not glowing |
| Pupil | Black/graphite | 0.0 | 0.20–0.45 | Clean dark disk |
| Painted cabin plastic | Off-white/light cool grey | 0.0 | 0.45–0.70 | Controlled satin response |
| Synthetic seat cushion | Airline blue | 0.0 | 0.45–0.70 | Subtle normal/noise if needed |
| Navy carpet | Dark blue | 0.0 | 0.80–0.95 | Matte, fine low-contrast texture |
| Cockpit buttons | Dark/coloured plastic | 0.0 | 0.25–0.50 | Small precise highlights |
| Painted airframe | White + branding | 0.0–0.10 | 0.20–0.45 | Broad clean highlight |
| Bare metal details | Cool metallic | 0.7–1.0 | 0.20–0.55 | Use sparingly |
| Window glass | Neutral transparent | Contextual | Contextual | Controlled reflection/refraction |
| Emissive indicator | Warning/display colour | 0.0 | Contextual | Intensity in Unreal, not only bright base-colour |

Roughness is normally a **0–1 shader parameter**; values above are artist-tuning guides. Real appearance depends strongly on lighting, exposure, reflection environment, normal intensity and tonemapping.

### Material rules

1. Keep skin and rubber **metalness zero**.
2. Avoid huge variations in roughness across one toy-like character.
3. Add microtexture only after the broad shapes look correct at gameplay distance.
4. Use real emissive contribution for instrument/warning lights, but don't compensate for broken exposure with unlimited bloom.
5. Differentiate materials through roughness and value as well as colour.
6. Tune materials **inside the actual engine lighting**, not only under Blender studio HDRIs.
7. Test night lighting. A material that looks great in sunlight may become visually crushed in an aircraft emergency.

## 11. Geometry, bevels, normals, and texture density

**Not simply “low-poly.”** The visual style uses relatively economical forms but plenty of smoothly shaded rounded surfaces. Clean normals and edge highlights matter more than intentionally visible polygon facets.

### Recommended geometry standards

- Use **Shade Smooth** on rounded surfaces and appropriate sharp-edge handling on hard-surface props.
- Use bevels on visible rigid edges; a perfectly sharp cardboard-box corner lacks the intended polish.
- Preserve clear silhouette landmarks in character meshes even when optimizing.
- Give large fuselage segments enough resolution to maintain a visibly smooth arch.
- Keep concave geometry and internal collisions simple and physically stable.
- Avoid needlessly subdividing flat walls and unseen undersides.
- Favor simple, reusable components rather than unique unoptimized parts everywhere.

### Bevel guidance [ESTIMATE]

For hard-surface props, try a bevel width that is roughly **0.5–3% of the local visible object's width**, then compare in-engine. A large luggage piece may warrant a visibly rounder bevel than a small cockpit switch. This is a relative design heuristic, **not an exact Dear Passengers measurement**.

### Topology standards

- Keep quads where practical on deforming characters.
- Add supporting loops around shoulders, elbows, knees and eyelids only where deformation needs them.
- Apply consistent smoothing practices to hard edges and UV splits.
- Test deformation with extreme poses, not only an idle T-pose.
- Prefer more polygons on close-up eyes and curved head silhouettes than on hidden sole geometry.

### Texturing strategy

Use a **hybrid** of material colours, masks, decals, limited normal textures and occasional printed designs. A clear base-colour palette plus believable shading can carry most of the art. Printed shirts, cockpit display graphics, warning signs and small icons may require dedicated textures. Text and signage should remain readable at gameplay distance.

### Texture-resolution heuristics [ESTIMATE]

| Asset class | Prototype target | Possible final target |
|---|---:|---:|
| Small prop | 256–512px | 512–1024px |
| Medium prop/seat | 512–1024px | 1024–2048px if justified |
| Close-up passenger | 1024px | 1024–2048px if justified |
| Large shared architecture | Tile/trim based | Tile/trim based; avoid giant unique maps |
| UI-like cockpit display | Depends on viewing distance | Resolution dictated by text legibility |

These are budget starting points. Do not use 4K textures by default; optimize from evidence and profiling.

## 12. Lighting design: daylight, cabin, night, emergencies

### A. Bright sunny exterior

**[OBSERVED]** Strong daytime sky light and good separation of colourful surfaces.

**[RECOMMENDED] UE5 setup:** Directional Light for sun, Sky Atmosphere, Sky Light, optional volumetric cloud/fog, plausible shadow softness and coherent exposure. Test white aircraft paint against sky so it does not clip or disappear. Ensure the underwing/underside has some fill light.

### B. Daytime aircraft cabin

**[OBSERVED]** White ceiling lights, window contribution, relatively bright light-coloured interior walls and darker navy floor.

**[RECOMMENDED] setup:** Natural light entering window apertures plus modest rectangular/area-like practical fixtures, spatially consistent ceiling strips and enough fill to preserve readability. Give fixtures visible luminous geometry but don't rely solely on emissive meshes to light the level. Use real light actors where needed.

### C. Cockpit

**[OBSERVED]** Dials and displays pop against darker panels; exterior sky remains bright beyond windows.

**[RECOMMENDED]** Balance instrument legibility against exposure at the windows. Make dials visibly luminous without completely washing out the cockpit. Check from seated first-person eye height.

### D. Night/damage scene

**[OBSERVED]** Dark, cool exterior, warm local glows, exposed structure, and more dramatic contrast.

**[RECOMMENDED]** Use a clear cold/warm separation: blue-grey ambient environment, warm overhead damage/fire hints, red hazard light, and highly selective pools of light. The playable actions must still be visually legible.

### E. Emergency lights

Use rhythmic flashing sparingly, avoid excessive flicker and offer accessibility-friendly settings. Hazard colour should correspond to gameplay information. A flashing scene should remain readable in still images and during motion.

### Lighting mistakes

- Multiple gigantic shadowless point lights making everything look flat.
- Excessive ambient occlusion causing grey-black dirt in every edge.
- Auto-exposure radically changing brightness whenever the camera moves a few degrees.
- Pure-white lights flattening coloured materials.
- Bloom that turns cockpit LEDs into huge smeared orbs.
- Dramatic dark lighting so strong that physical comedy is invisible.

## 13. Camera, first-person hands, composition, readability

**[OBSERVED]** Many official views are first-person. The player sees oversized saturated hands holding objects or operating controls, with a nearby passenger in the middle ground and recognizable aircraft architecture behind.

### Composition layers

1. **Foreground:** bright hand, cup, tool, tray or lever—clearly readable interaction.
2. **Middle ground:** oversized-eyed passenger, other crew member, seat row or animated prop—primary comic subject.
3. **Background:** repeating seat/aisle structure, cabin opening, signs, other passengers—sense of place.

**[RECOMMENDED]** Use a first-person camera wide enough to show the task but not so wide that heads look grotesquely stretched at all times. Validate FOV with side-by-side images. Test UI-safe zones so hands and held props do not cover a prompt or face.

### FOV starting values [ESTIMATE]

- Gameplay horizontal FOV: try around **85–105 degrees** and tune for display format/comfort; engine settings may define FOV differently.
- Viewmodel FOV: can be different if your rendering architecture allows it, but monitor clipping and perspective mismatch.
- Camera bob: mild and accessibility-tunable.
- Camera shake: subtle normally, stronger but controlled during turbulence; accessibility option to reduce it.
- Depth of field: minimal during routine gameplay; avoid blurring interactive objects.

These FOV values are **not extracted from *Dear Passengers***.

### Thumbnail test

Shrink screenshots to the size of a phone social-media preview. Can you immediately find the eye expression, held object, cabin location and central problem? If not, fix shape/colour/framing before adding detail.

## 14. Post-processing, effects, and final image quality

**[OBSERVED]** Bright readable colours, smooth surfaces, attractive contrast, subtle localized luminous indicators and clear model silhouettes.

The exact original post-process stack is unknown. Recommended equivalent directions:

| Feature | [RECOMMENDED] goal |
|---|---|
| Tonemapping | Filmic or comparable highlight handling; preserve saturated colours |
| Exposure | Stable interiors/exteriors, with controlled adaptation |
| Bloom | Modest on LEDs, bright windows, some emergency lights |
| Ambient occlusion | Restrained localized contact shading |
| Anti-aliasing | High-quality anti-aliasing to preserve eye and character curves |
| Reflections | Selective and plausible; avoid mirror-like plastic everywhere |
| Colour grading | Gently vibrant, minimal lifted-black washout |
| Sharpening | Moderate, without crunchy outlines |
| Vignette | None or very subtle for normal gameplay |
| Film grain | Minimal/none for a clean animated look |
| Motion blur | Minimal/optional; preserve visual clarity in physics chaos |
| Depth of field | Primarily cinematic, not constant gameplay blur |

### Effects palette

- Emergency spark: short, localized, bright.
- Fire: warm saturated accents with controlled light response and smoke.
- Smoke: supports depth but avoids obscuring important controls for long stretches.
- Wind/decompression cues: particles, moving loose props, subtle environmental movement.
- Debris: chunks that read at normal camera distance instead of tiny visual noise.
- Weather: rain/snow/cloud/fog should alter the mood while preserving the cartoon materials.

**Avoid the common misunderstanding:** A stylized rendered look is not produced by a single “cartoon shader.” It comes from the full model–material–light–camera system.

## 15. Animation, interaction, and physical comedy

**[CONFIRMED]** The game emphasizes physics-based interactions between the moving plane, passengers and cargo, including turbulence. The developer has discussed the difficulty of physics in a moving aircraft in public Q&A reporting; consult original publisher messages for updates.

### Why movement is part of the visual aesthetic

Simple shapes and eyes remain legible while falling, leaning, tumbling or reacting. A believable airplane cabin acts as a stable baseline; chaos is visually funny because it disrupts that organized baseline.

### Character animation language [RECOMMENDED]

- Start with readable idle/breathing, look-around, reach, pick-up, hand-over, walk and sit cycles.
- Favor noticeable poses and anticipation without extremely rubbery squash/stretch on every action.
- Separate head/eye focus from body movement; pupils can lag or lead a reaction.
- Give physical interactions a clear beginning, contact moment, follow-through and recovery.
- Use controlled ragdoll blending for falls and impacts where appropriate.
- Ensure arms/hands do not intersect cup, trolley or passenger face during service animations.
- Build soft impacts and funny reactions from pose timing, not constant chaotic screen shake.

### Props and collisions

Physics props need believable contact shapes and mass relationships. A suitcase should not spin like a sheet of paper; a coffee cup should not behave like a bowling ball. Avoid unnecessarily complex mesh collision. Add a few exaggerations only when their comedic payoff is clear.

### Moving-aircraft implementation warning

A physical cabin mounted inside a moving plane creates difficult **coordinate-frame, gravity, velocity, replication and collision** problems. Decide early whether the entire aircraft physically moves through the world or whether gameplay is simulated in a stable local frame with outside scenery moving relative to it. There is no universally correct approach; test your chosen architecture before creating hundreds of physics actors. The simplest prototype should answer: can a character walk, stand, throw a cup, and ragdoll during turbulence without exploding or jittering?

### Animation versus simulation boundaries

Script intentional actor behaviour (sit, serve, walk, react); simulate targeted chaos (loose luggage, dropped tray, turbulence knockback); blend physics into authored recovery. Unlimited uncontrolled physics usually damages gameplay and networking quality.

## 16. Blender: the complete asset-production workflow

**Blender makes the models, UVs, textures, rigs and animations. Unreal Engine makes them part of the interactive rendered game.** Blender is not inferior because the original game uses Unity.

### 16.1 Project setup

1. Create a source-assets directory with separate folders for Characters, Props, Cabin, Cockpit, Airport and Animations.
2. Choose a physical scale convention. **[RECOMMENDED]** In Blender, build at a coherent metric scale; in Unreal, one Unreal Unit is typically one centimetre. Verify the FBX conversion with a test cube or character before authoring a large library.
3. Establish origin/pivot conventions and asset orientation (forward, up) and test FBX export rather than trusting a magic fixed axis setting.
4. Save a reusable `.blend` file for materials, proportions, camera reference and naming standards.
5. Preserve unapplied/modifier source versions when applying transforms or mesh changes for export.

### 16.2 Blockout first

Make a cabin from primitives and add a rough character plus seat. No textures beyond neutral colours. Test real first-person scale in Unreal. If the cabin feels miniature, overly narrow or uncomfortable to navigate, fix that before detailed modeling.

### 16.3 Model one hero passenger

1. Create an elliptical head with modest face shaping.
2. Add eye sockets/contact surface to accommodate large eye spheres.
3. Place two oversized eye spheres and simple pupils.
4. Add a restrained mouth and small nose form.
5. Sculpt/blend rounded torso, arms, hands, legs and shoes.
6. Give the model a recognisable hoodie/shirt and simple pants.
7. Create a silhouette-distinct hairstyle from sculpted masses.
8. Set smooth normals and local bevels where needed.
9. Test from 1 m and 3 m distances; do not obsess over cheek topology hidden in play.
10. Build 3 expressions and 3 poses before expanding the character library.

### 16.4 Model a seat module

1. Block out cushion, seat back, seat shell and rail.
2. Add rounded armrests with contrasting material.
3. Model cushion silhouette and separation seam at the simplest readable level.
4. Add buckle/lap-belt geometry only where visible/interactive.
5. Test a passenger seated in it; verify knees, hands and head clearance.
6. Add modest bevels; confirm shading and UVs.
7. Export static/interactive components separately if they need separate movement.
8. Duplicate into a test cabin row and assess visual rhythm.

### 16.5 Model the cabin modularly

1. Model one correct cross-section of the fuselage.
2. Segment sidewall into a repeatable module with window/trim.
3. Create ceiling module with fixture positions.
4. Make an overhead luggage bin with open and closed parts.
5. Create floor/aisle segment and seat attachment layout.
6. Duplicate repeatedly in Blender only as a preview; assemble with instances/prefabs or actors in-engine for flexibility.
7. Build transition/end pieces for emergency doors and cockpit entry.
8. Verify collisions and player traversal at engine scale.

### 16.6 UV unwrap and texture authoring

- Mark seams along hidden or structurally plausible edges.
- Avoid massive texture distortion on eye whites, clothing logos and cockpit screens.
- Keep similar texel density among similarly important assets.
- Use trim sheets/tileable materials for repeated panels and architecture.
- Prefer simple material IDs and instances for colour variation where possible.
- Export compatible normal-map formats and check handedness/orientation in Unreal; fix flipped channels rather than painting over wrong shading.
- Keep source texture files editable and organized.

### 16.7 Rigging

- Use a standard deformable humanoid skeleton for original passengers.
- Establish correct shoulder, hip, hand and head pivots.
- Use a clean parent hierarchy and avoid needless bones on rigid props.
- Weight paint against extreme seat/reach poses.
- Separate pupil/eye movement using bones or driven material/mesh offsets as appropriate.
- Consider shape keys for brows/mouth if useful, but don't require an elaborate facial rig for a deliberately minimalist face.
- Test animation retargeting with your own consistent skeleton.

### 16.8 Animation

Author a compact animation library: idle, walk, sit, stand, reach, pick up, offer, recoil, stumble, grab handhold, lean, fall transition, and recover. Make sure export includes only the intended animation action/take. Verify root-motion requirements before generating lots of clips.

### 16.9 Export to Unreal

1. Save your editable `.blend` file.
2. Select the object(s)/armature you intend to export, not scene cameras/lights/helpers.
3. Apply or bake transforms in a controlled manner, preserving skeleton integrity.
4. Export to FBX using a **project-tested** unit/axis recipe.
5. For skeletal meshes, export mesh + armature and intended animation data; avoid unrelated Blender control rig nodes.
6. For static meshes, use simple clean mesh FBX, sensible pivot placement and collision plan.
7. Import first into an Unreal **test map** and confirm size, upright orientation, material slots, smoothing, animation and physics.
8. Record the tested settings in a team export preset rather than inventing new ones for each artist.

**Do not blindly rotate every mesh 90° because a random tutorial said so.** Forward/up conversions depend on your project's coordinate setup, FBX exporter version and importer. A validated test asset is the reliable source of truth.

### 16.10 Blender preview rendering

Use Blender's preview renderer/HDRI for quick model checks, but don't attempt to perfectly match an Unreal look inside Blender. Unreal lighting, tonemapping, reflection methods and exposure will alter the final appearance. The **game engine is the source of truth for final art sign-off**.

## 17. Unreal Engine 5: import and visual assembly

### 17.1 Establish a clean project

- Choose a template that matches the gameplay plan (first-person or third-person prototype).
- Record UE version and plugin dependencies in version control.
- Create folders for Meshes, Materials, MaterialInstances, Textures, Characters, Animations, FX, Blueprints, Maps and UI.
- Use source control before making a large asset library. Avoid manual overwrite of unrelated assets.
- Set target hardware early; rendering decisions change dramatically between high-end PC and lower-spec devices.

### 17.2 Import meshes

For **static meshes**: verify import scale, smoothing/tangents, pivot, mesh collisions, lightmap considerations if using baked illumination, and material slot names. For **skeletal meshes**: verify skeleton orientation, joint naming, skinned deformation, animation import, physics asset, and retargeting. Unreal supports FBX asset pipelines including skeletal meshes imported from Blender; see Epic documentation linked below.

### 17.3 Master materials

Build a small system of common master shaders and instances:

- `M_StylizedOpaque` — skin, plastic, clothing and painted surfaces by parameter.
- `M_StylizedFabric` — upholstery/clothing variant with optional subtle normals.
- `M_Eye` — glossy off-white with independently controlled pupil system.
- `M_EmissivePanel` — cockpit LEDs, status lights and emergency signage.
- `M_WindowGlass` — controlled glass for actual gameplay camera usage.
- `M_DecalWear` — limited damage/marks without altering clean base materials.

Prefer parameterized Material Instances over creating dozens of identical hand-written materials. Expose base colour, roughness, metallic, normal strength, detail frequency and emissive amount as needed.

### 17.4 Lighting test map

Make a permanent `L_ArtLookdev` test level containing a character, eyes, one seat, white/grey wall, navy floor, metal piece, plastic cup, cockpit LED and sky window. Include side-by-side **day cabin**, **night cabin**, and **daylight exterior** lookdev scenes if practical.

Use the same view distances and exposure every time you evaluate assets. A material cannot be judged fairly if the camera and lighting change unpredictably between versions.

### 17.5 UE5 lighting implementation

Choose project rendering features based on GPU budget and current UE support. You can test Lumen or other supported methods for indirect lighting/reflections, but **do not assume Lumen is mandatory** to achieve a polished stylized look. A clean intentional mix of direct lighting, skylight, bounce approximations, reflection capture strategy and sensible exposure may be sufficient for your target hardware.

For each map, tune:

1. Primary directional/outside illumination.
2. Skylight/environment fill.
3. Practical cabin overhead lights.
4. Interior window contribution.
5. Local warning/instrument lighting.
6. Contact shadow quality and ambient occlusion.
7. Exposure and tone mapping.
8. Final material response in motion.

### 17.6 Rendering quality and post-process setup

Use a Post Process Volume with explicit, recorded settings for exposure, colour grading, bloom, ambient occlusion, vignette and other effects. Test under real gameplay camera motion. Use anti-aliasing appropriate to your project. If a temporal technique introduces ghosting around big eyes or fast-moving luggage, test alternatives or quality settings.

### 17.7 Blueprint/gameplay integration

Keep asset ownership clear: art defines the visual mesh; gameplay owns health/states/interaction rules; physics owns collision/mass; audio owns feedback. Use reusable interaction interfaces/components so cups, boxes and buttons behave consistently, without requiring bespoke code for every prop.

### 17.8 Physics assets

Set collision primitives for the actual gameplay shape; simplify rigs and collision per mesh. Create ragdoll constraints that bend naturally enough for comedy without severe stretching and jitter. Test dropped objects on moving surfaces and replicated pickup/throw behaviour early.

### 17.9 Visual debugging

Capture before/after screenshots at fixed camera positions. Debug shading problems by changing one variable at a time: normals, roughness, exposure, light direction, AO, tone mapping, LOD or anti-aliasing. Resist adding more post-processing to hide a broken base asset.

## 18. Blender → Unreal: exact handoff checklist

The following checklist is a **repeatable studio QA gate**, not a promise that one export preset works for every Blender/Unreal combination.

### Blender before export

- [ ] Naming follows project prefix conventions.
- [ ] Mesh dimensions match agreed physical scale.
- [ ] Origin/pivot is intentionally placed.
- [ ] Mesh has correct forward/up orientation according to project test asset.
- [ ] No accidental negative scale or mirror deformation.
- [ ] Normals are correct; no dark/broken shaded faces.
- [ ] Material slots are cleanly named.
- [ ] UVs exist, are non-overlapping where required, and have reasonable texel density.
- [ ] Optional LODs/collisions created if needed.
- [ ] For characters, only intended deform rig and mesh data included.
- [ ] Skin weights tested in extreme poses.
- [ ] Actions exported individually/according to animation convention.
- [ ] Editable `.blend` source saved and backed up.

### Unreal after import

- [ ] Scale verified against reference mannequin/cabin seat.
- [ ] Imported asset points the intended direction.
- [ ] Materials and textures assigned to expected slots.
- [ ] No flipped normal maps / missing tangent data.
- [ ] Collision works without snagging the player.
- [ ] Character rig poses correctly; no armature artifacts.
- [ ] Animation/root motion matches gameplay architecture.
- [ ] Eye geometry and pupil tracking work from first person.
- [ ] Performance and texture memory are acceptable.
- [ ] Asset looks correct in day/night lookdev maps.
- [ ] Changes reimport cleanly without hand-fixing many things.

### Example source-to-runtime file map

```text
Project/
├── README.md
├── ArtBible/
│   ├── ReferenceLinks.md
│   ├── Palette.md
│   ├── QualityGates.md
│   └── ScreenshotComparisons/
├── SourceAssets/
│   ├── Blender/
│   │   ├── Characters/
│   │   ├── Cabin/
│   │   ├── Cockpit/
│   │   ├── Airport/
│   │   ├── Props/
│   │   └── Rigs/
│   └── Textures/
├── Exports/
│   ├── FBX/
│   └── Textures/
└── UnrealProject/
    └── Content/
        ├── Art/Characters/
        ├── Art/Environments/
        ├── Art/Props/
        ├── Art/Materials/
        ├── Characters/
        ├── Gameplay/
        ├── FX/
        ├── Maps/
        └── UI/
```

**Source of truth:** `.blend` and texture source files belong in `SourceAssets/`; Unreal asset `.uasset` files belong inside the Unreal project. Do not attempt to use Blender project files directly as runtime assets.

## 19. Suggested asset list and naming conventions

### First playable-quality art slice (recommended)

| ID | Asset | Type | Minimum visual bar |
|---|---|---|---|
| CH_001 | Original passenger A | Rigged skeletal character | Eye/facial look, 3 expressions, idle/sit |
| CH_002 | Original crew character | Rigged character | Clear role colour, first-person compatibility |
| FP_001 | First-person arms/hands | Skeletal viewmodel | Pick-up, hold, offer, release |
| ENV_001 | Cabin wall with window | Modular static mesh | Smooth arch, trim, believable scale |
| ENV_002 | Overhead locker | Static + movable parts | Open/closed states |
| ENV_003 | Ceiling lights | Static + lighting logic | Readable practical fixtures |
| ENV_004 | Aisle flooring | Modular static mesh | Navy, correct contact grounding |
| PROP_001 | Seat row | Static mesh assembly | Cushion/armrest/rails and character fit |
| PROP_002 | Coffee cup | Physics prop | Hands can grip correctly |
| PROP_003 | Suitcase | Physics prop | Easy to spot during turbulence |
| PROP_004 | Food tray | Interaction prop | Strong foreground silhouette |
| PROP_005 | Emergency sign | Static + emissive material | Highly readable |
| FX_001 | Turbulence effect | VFX/gameplay combo | Controlled motion and feedback |
| LVL_001 | Cabin lookdev scene | UE level | Day/night A/B comparison |

### Naming conventions [RECOMMENDED]

- `SM_` for Static Mesh (`SM_Cabin_WindowWall_A`).
- `SK_` for Skeletal Mesh (`SK_Passenger_A`).
- `SKEL_` for skeleton.
- `AN_` for animation (`AN_Passenger_SitIdle`).
- `M_` for master material.
- `MI_` for material instance (`MI_Seat_Blue`).
- `T_` for texture (`T_Cockpit_Display_BaseColor`).
- `BP_` for Blueprint gameplay asset.
- `NS_` for Niagara FX systems if using Niagara.
- `L_` for maps/levels.

Consistency saves time and prevents AI agents or teammates from importing incompatible duplicates.

## 20. Performance, multiplayer, and scalability

Visual polish does **not** require maximum polygon counts. It requires stable frame rate and consistent quality.

### Performance priorities [RECOMMENDED]

1. Optimize the number of expensive active lights casting shadows.
2. Reuse cabin modules and material instances.
3. Build LODs/HLODs or use appropriate engine mesh reduction/virtualized geometry on supported assets where beneficial.
4. Use sensible texture sizes and atlases/trim sheets.
5. Reduce translucent overdraw and excessive particles in compact interiors.
6. Limit shadow-casting unnecessary tiny props.
7. Use simplified collision even for visually detailed objects.
8. Profile CPU physics, animation and replication—not just GPU rendering.
9. Validate low/medium settings visually; a stylized game can retain identity without ultra effects.
10. Test scenes with many passengers, luggage props and emergency effects simultaneously.

### Multiplayer considerations

For multiplayer, make physics and interactions authoritative according to the networking model. Simulating every tiny cup and fragment with perfect full-rate replication can become extremely expensive. Replicate gameplay-significant states and use interpolation/prediction or cosmetic local effects where appropriate. Avoid client/server divergence that makes cups float, snap or teleport.

### Performance budget example [ESTIMATE]

Define a specific target (for example, 60 FPS at 1080p on a chosen reference PC) **before** committing to expensive rendering features. Use measured Unreal profiling captures. Hardware selection, not arbitrary polygon numbers, should determine the final budget.

### Accessibility and clarity

Support reduced camera shake; adjust sensitivity and FOV; keep bright emergency lights from becoming hazardous strobe patterns; maintain colour-independent role cues where possible; and avoid relying on tiny cockpit text as the only interaction signal.

## 21. Quality gates, comparison tests, and acceptance criteria

### Gate 1 — Character recognisability

- [ ] At thumbnail size, character expression is immediately legible.
- [ ] Eyes are large, rounded and visually integrated, not floating disconnected spheres.
- [ ] Pupil direction communicates a reaction.
- [ ] Hair is made of readable sculpted clumps.
- [ ] Character silhouette is distinctive even without textures.
- [ ] The body doesn't look like a realistic scanned human.

### Gate 2 — Material and lighting

- [ ] Plastic, carpet, cloth, metal, eye white and skin are visually distinct.
- [ ] Highlights are present without making every surface wet/shiny.
- [ ] Light-coloured panels remain visible under daylight.
- [ ] Eye whites retain shape/detail and do not overexpose.
- [ ] Ground contact shadows make seats and props feel substantial.
- [ ] Night scenes still permit clear interaction.

### Gate 3 — Cabin credibility

- [ ] Sidewalls, windows, seats and bins repeat in believable scale.
- [ ] The aisle feels navigable from first-person perspective.
- [ ] Seats support believable seated character posture.
- [ ] Lights have visible sources.
- [ ] The space reads as an aircraft cabin from one screenshot.

### Gate 4 — First-person interaction

- [ ] Hands hold objects without obvious clipping.
- [ ] Nearby passengers remain fully legible.
- [ ] Object size is plausible and recognisable.
- [ ] Crosshair/prompts remain visible and don't cover faces.
- [ ] Interaction animations have clear timing and weight.

### Gate 5 — Physics/comedy

- [ ] A tossed cup collides stably with a seat/floor.
- [ ] Suitcase tumble makes physical sense and is visible.
- [ ] Passenger stumble/fall remains humorous and readable.
- [ ] Loose props do not destroy performance.
- [ ] Multiplayer clients agree on the outcome of important interactions.

### Screenshot comparison matrix

Capture the same in-engine angle before/after each art pass:

| Shot | What to evaluate |
|---|---|
| Close-up passenger and offered cup | Eyes, face, viewmodel hand, depth, shading |
| Wide cabin aisle | Structural rhythm, colour hierarchy, shadows |
| Pilot's instrument panel | Gauge readability, emissive effects, window exposure |
| Sunny exterior by aircraft | Airframe material, sky, ground shadows, character saturation |
| Night damaged cabin | Warm/cool lighting, damaged geometry, retained legibility |
| Turbulence with loose luggage | Motion readability, physics stability, VFX restraint |

### Acceptance scores

Use a simple internal score from **1 to 5** for (a) visual cohesion, (b) gameplay readability, (c) silhouette/design, (d) material/lighting polish, (e) engine performance and (f) animation/physicality. **Do not** approve an asset solely because it looks good in Blender if it fails in the engine.

## 22. Production roadmap and milestone deliverables

### Phase 0 — Gather visual references and lock the rules

**Deliverable:** reference board, palette, original character silhouette sheet, sample material definitions, and 6 benchmark screenshots. Make explicit which visual principles are inspirations and which features are original.

**Definition of done:** everyone can tell a 2-sentence story about the visual direction; there is no confusion about Blender vs Unreal roles.

### Phase 1 — First art-quality character

**Deliverable:** one original passenger with huge eyes, sculpted hair, outfit, rig, one idle animation and eye look-around. Import into Unreal and test under representative lighting.

**Definition of done:** recognisable, readable, smooth, no broken shading or weights.

### Phase 2 — The beautiful small cabin

**Deliverable:** 4–8 seats, 2–3 window modules, overhead fixtures, aisle, one crew avatar, a cup and a suitcase. Include strong materials and camera/composition.

**Definition of done:** one stationary screenshot already conveys the complete art style.

### Phase 3 — First-person interaction

**Deliverable:** hands, pickup/hold/drop, serving a drink, passenger reaction, simple interaction cues.

**Definition of done:** user can serve an object convincingly; no hand/face clipping in normal views.

### Phase 4 — Turbulence and comedy

**Deliverable:** one scripted turbulence event, loose luggage, cup physics, passenger stumble/ragdoll transition.

**Definition of done:** funny, readable, repeatable and technically stable.

### Phase 5 — Cockpit and exterior

**Deliverable:** cockpit instrument section and basic outside sky/airframe view.

**Definition of done:** same materials, lighting principles and colour organization survive outside the cabin.

### Phase 6 — Lighting modes and emergencies

**Deliverable:** sunny cabin, evening cabin, night/damage cabin and controlled warning VFX.

**Definition of done:** identity remains consistent across modes and all gameplay cues readable.

### Phase 7 — Optimization and scale

**Deliverable:** 10+ passengers/outfit variations, more props, LODs, replicated interactions, profiled target frame rate.

**Definition of done:** extra content feels like the same game, not an assortment of inconsistent assets.

### Phase 8 — Art polish and final presentation

**Deliverable:** consistent post-process, rich animation timing, passable comfort options, screenshots, trailer-quality shots and final asset QA.

**Definition of done:** polished **during gameplay**, not just in posed screenshots.

### Recommended first 48-hour prototype scope

Do not build the entire airliner first. Build **one seat, one cabin wall/window, one passenger, one cup, and one camera**. That combination is enough to determine whether the core art direction works. Next create a tiny test where a stylized hand gives the cup to the passenger. A polished five-second interaction proves more than a huge unfinished airport.

## 23. Frequent mistakes and how to fix them

| Mistake | Visual symptom | Corrective action |
|---|---|---|
| “Make it low-poly” interpreted as faceted geometry | Cheap angular look | Smooth core silhouettes and use restrained bevels |
| Too much photorealism | Characters/environment seem from different games | Reduce microtextures, simplify forms, retain material categories |
| Eyes too small | Generic stylized humans | Rework eye/head ratio and expression system |
| Eye whites pure glowing white | Flat disks, no 3D form | Use off-white shaded PBR material with highlights |
| Mouth/facial detail too elaborate | Busy face | Reduce details; move expression to pupils/body pose |
| All surfaces high gloss | Plastic showroom | Differentiate roughness; carpet/cloth matte, eyes smoother |
| Very flat ambient light | No volume or grounding | Add directional shape and contact shadows |
| Massive AO | Dirty grey seams everywhere | Reduce AO radius/intensity; fix lighting |
| Excessive bloom | LED haze and washed-out colour | Reduce bloom/exposure; keep localized highlights |
| Too much saturated colour | No focal hierarchy | Neutralize architecture; reserve vivid hues for agents/props |
| Unreal scene only looks good in one static shot | Weak gameplay read | Test moving FPP camera and changing light |
| Beautiful Blender render, ugly engine import | Pipeline mismatch | Use in-engine lookdev as final check |
| Bad FBX scale/axis | Tiny/rotated meshes | Validate with test asset; document conversion recipe |
| Overly detailed cockpit | Tiny unreadable noise | Build primary instruments before tiny switches |
| Hundreds of independent high-cost physics bodies | Lag/jitter/network desync | Simplify collisions, cull/sleep/limit active props |
| Ragdolls only, no animation | Uncontrolled floppy comedy | Blend authored poses, impacts and recoveries |
| Copying identical designs or branding | Looks derivative / IP problems | Make original characters, airline identity, livery and assets |

## 24. Complete reusable art-direction brief

> ### ART DIRECTION — ORIGINAL STYLIZED 3D AIRLINE COMEDY
>
> Create a visually cohesive, high-quality stylized 3D world inspired by modern colourful cooperative physics-comedy games. The result must resemble a professionally produced 3D animated comedy made interactive. Avoid aggressive low-poly faceting, pixel/voxel looks, thick comic-book outlines, unlit flat colours, overly gritty photorealism, and inconsistent asset styles.
>
> **Characters:** Build charmingly exaggerated anatomy with clean, smooth silhouettes, large rounded heads, prominent spherical off-white eyes, simple dark pupils, restrained mouths, minimal facial features, and expressive body motion. Use skin with subtly shaded clay/satin response. Sculpt hair in a few readable broad clumps instead of simulating thousands of strands. Make clothing recognizable and colourful, with modest seams and folds. Distinguish stylized crew avatars from more recognisably human passengers, while maintaining consistent shading across both.
>
> **Environment:** Create a believable yet simplified world. Aircraft cabins should have curved wall sections, repeated windows and seats, overhead storage, carpeting, lights, doors and signs. Cockpits should have clear clusters of primary instruments and controls. Terminals should be airy and structured, with glass, signage, seating and luggage. The world should be more structurally detailed than the characters without becoming a high-frequency photoreal simulation.
>
> **Geometry:** Use efficiently subdivided smooth meshes, bevelled hard edges, clear silhouettes, appropriate normals, modular architectural assets and stable collision shapes. Do not deliberately reveal triangles on curved organic features.
>
> **Materials:** Use restrained physically based materials. Skin and rubber-like avatar bodies are softly satin/matte; eyes are smoother and brighter; painted cabin walls are neutral and softly reflective; upholstery is clear saturated blue; carpet is dark and matte; gauges have focused emissive highlights. Limit texture noise and avoid making everything equally shiny.
>
> **Lighting:** Create bright outdoor scenes with appealing skies, credible sunlight and ambient fill. Interiors need readable overhead practical fixtures and sunlight entering windows. Preserve strong 3D shape via highlights, shadow gradients and light contact shading. During emergencies, use warm/cool lighting contrast and controlled hazard accents without destroying legibility.
>
> **Colour:** Give most structural surfaces pale neutral or controlled navy values. Reserve vivid red, green, yellow, blue and other bright hues for characters and gameplay-important props. Use sky cyan and warm emergency colours selectively. Keep focal hierarchy clear.
>
> **Camera:** Prioritize first-person readability. Show stylized hands holding or offering objects in the foreground; expressive passengers in the middle ground; convincing cabin architecture behind. Use a comfortable moderately wide gameplay perspective and avoid heavy always-on depth of field or camera shake.
>
> **Motion:** Implement clean author-driven animation, eye tracking, readable gestures, stable item pickups, appropriately weighted luggage collisions, occasional ragdoll/comedic reactions and turbulence. The game should be funny through the interplay between simple cartoon inhabitants and a physically understandable space.
>
> **Tools:** Author meshes, rigs, UVs, masks, textures and animations in Blender. Export validated assets into Unreal Engine 5, where materials, lighting, first-person interaction, physics, networking, post-processing and performance are assembled and evaluated. Blender is the authoring tool; Unreal is the rendering/gameplay runtime.
>
> **Quality target:** Every gameplay screenshot should feel colourful, friendly, tangible, visually clear, cohesive, soft-lit, and premium-polished without requiring photorealistic assets. Favor excellent shape language, material consistency and attractive lighting over gratuitous detail.
>
> **Originality:** Create unique faces, costumes, props, airline branding, environment layouts, iconography, animations and gameplay identity; take inspiration from the **general visual principles**, not proprietary copies of characters or marketing art.

## 25. Sources, image references, and caveats

### Primary sources used

1. **Official Steam store listing for *Dear Passengers* (FLEXUS):** https://store.steampowered.com/app/4534960/Dear_Passengers/ — developer, description, features, promotional trailer and original screenshots.
2. **FLEXUS's Steam community page/announcements:** https://steamcommunity.com/app/4534960 — public developer updates, including a statement accompanying a screenshot described as captured from Unity.
3. **SteamDB gallery of the game's official screenshots:** https://steamdb.info/app/4534960/screenshots/ — convenient links to the game's published Steam screenshots. SteamDB is a third-party catalogue; screenshot assets originate from Steam.
4. **Epic Unreal Engine FBX Skeletal Mesh Pipeline:** https://dev.epicgames.com/documentation/en-us/unreal-engine/fbx-skeletal-mesh-pipeline-in-unreal-engine — Epic's export/import guidance.
5. **Epic Unreal Engine Importing Skeletal Meshes Using FBX:** https://dev.epicgames.com/documentation/en-us/unreal-engine/importing-skeletal-meshes-using-fbx-in-unreal-engine — includes external 3D applications such as Blender and compatibility notes.

### Suggested official-image comparison shots

- **Passenger close-up with blue crew hand/cup:** prominent protruding eyes, soft skin, small mouth, bright blue viewmodel hand and crisp cabin framing. Public Steam screenshot: https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/4534960/05aaeb9bad531cef7286d9cc5484c134213975ee/ss_05aaeb9bad531cef7286d9cc5484c134213975ee.jpg
- **Cabin/service/chaos:** use the other screenshots in the official Steam gallery to study repeated seat rhythm, overhead bins, damage, objects and lighting.
- **Cockpit views:** use official game screenshots to compare instrument graphic density, clean readable buttons, bright exterior sky and first-person positioning.
- **Exterior/terminal scenes:** use official screenshots to compare outdoor saturation, scale contrast, architectural simplicity and high-level colour distribution.

**Image use:** Screenshots and trailer footage belong to their respective rights holders. Keep them as attributed references; do not bundle their artwork as your own assets or reproduce the original characters, logos or exact designs as if they were original.

### Important caveats

This document provides qualitative style analysis and actionable creative recommendations, not measurements of a proprietary engine project. All numerical proportions, roughness ranges, colour hex values, FOV bands, detail budgets, bevel guides, priority percentages and milestone plans are **estimates for your implementation**. Treat them as parameters to test and tune. The look of *Dear Passengers* may evolve after the screenshots used here. Software version numbers, export interfaces and Unreal lighting systems also evolve, so consult documentation for your actual tool versions.

---

## Fast reference: the complete answer in 10 rules

1. **Use Blender for 3D asset creation.** It is absolutely suitable.
2. **Use Unreal Engine 5 for your game's rendering, lighting, animation integration, physics, multiplayer and interaction.** Unity is a valid alternative; the reference game has publicly shown Unity use.
3. **Prioritize eyes and silhouettes.** Giant spherical eyes and simplified faces produce much of the recognisable personality.
4. **Keep characters simple but environments believable.** This contrast is the core aesthetic.
5. **Use smooth rounded shapes, not crude faceted geometry.** Bevel where highlights should catch.
6. **Use PBR materials, not universal flat colours.** Different surfaces need different roughness and highlights.
7. **Light softly but meaningfully.** Daylight, overhead fixtures, ambient fill and contact shadows make the scene solid.
8. **Control saturation.** Neutral cabin architecture makes vivid passengers, crew and props pop.
9. **Animate for comedy and maintain stable physics.** The visual identity includes motion, not just still meshes.
10. **Prove the style with one excellent interaction before building an entire world.** One passenger + one cup + one seat + one cabin window + first-person hands + tuned lighting is the ideal first milestone.

**Recommended next production task:** Build `L_ArtLookdev` in Unreal Engine with one Blender-made original passenger, one blue aircraft seat, one window-wall section and one interactive cup; compare four fixed screenshots (close-up, aisle, day and night) against the art-direction rules above.
