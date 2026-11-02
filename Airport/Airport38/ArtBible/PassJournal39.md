Final release check: all seven sessions in `FinalChecks44.json` completed successfully on source `52d50fa72e86610db32ca5d89e8e8d8e85e98df39876c74419e2a0a445741610`, with actual process exit 0. The final visual review, imports and capture manifest are pinned separately. The historical pending/rejected entries below remain provenance, not the current status.

# Latest whole-scene scrutiny —30 October2026

This opening entry is the current state. Older entries below describe historical stages and earlier failures; their pending notes do not override the completed current tests.

Five independent original audits and separate fix assignments were followed by repeated architecture, equipment, airside, characters and rendering reviews. The latest user-example pass repaired chair-armrest fins, fitted warm paneling, quiet physically scaled floors and blue-grey lounge carpet, modeled baggage portals and identities, non-pointed window returns, genuine low lap belts, PSU covers, supported luggage handles/zippers, a planar cockpit fascia, clean character cuffs/blouse/elbows, local self-shadow quality and adjacent passenger variety. A later visual sweep caught the opaque exterior-window alias and corrected all48native bays; editable source optics were already transmitting.

Six current combined-build sessions completed and exited0:27assembly checks,174fresh entrance-to-airborne checks,92scanner checks,28safety checks,93scene captures and15detail captures, plus uncaptured performance samples. The physical route used zero test teleports and zero direct luggage-transform assignments. Current airport timing is about42–60median FPS at1080p on this machine; airborne cockpit/chase about29/26median FPS remains a limitation. Full per-view percentiles and scope are recorded separately. NoSound automated tests do not prove audible playback.

The final exterior scrutiny also found incorrect lengthwise shoulder normals on the straight pressure tube. A focused normal repair is in progress, separate from the already completed function tests. Final source hash/captures must follow that repair; do not infer final approval from this journal paragraph.

---

# Airport / aircraft / character refinement journal

Documentation snapshot: **29 October 2026**. This records actual construction,
detail, fit and scrutiny passes, including defects discovered after earlier tests.
It is a work/evidence journal, not a declaration that the latest combined build
has completed native flight, visual-fit or performance review.

The parent runner owns the installed runtime, source/native integration and the
current native retests. This documentation pass changed no geometry, runtime,
editor state or launch defaults. Earlier source and all original body37 assets
are retained, as confirmed by the parent; the current work does not replace that
preservation history with a claim of a clean-room proprietary asset match.

## Current source boundary

- Airport source SHA256:
  `2061e993d13418a469e83ca52e41a859393313b116e03dafc705a369da6a211d`.
- Character source SHA256:
  `d7da5506392424fab45bee3583105d98f5d518246c6171c1046020e7ae56dde2`.
- `Characters09Source.json` records the current character placement/source pass.
  `Characters/Revision39/ArtBible/JoinRepair39.json` and `UVPrimaryAll39.json`
  identify the character source above.
- Reports from an earlier source remain evidence of that run. They do not clear
  newly changed character meshes, UV import copies or carry-on behavior. Final
  capture and validation manifests must bind the final airport source, character
  source, report hashes/mtimes and installed-runtime hashes where available.
  If a native character/UV report declares the character-source hash, its parent
  validation can pin `source_sha256` to the airport snapshot and
  `report_source_sha256` to that declared character source; both are verified.

Paths below are relative to `Airport38` unless they begin with
`outputs/Characters/Revision39`.

## Actual refinement passes

### 1. Coherent terminal construction

Rebuilt floors, walls, ceilings and roofs from the final room footprints and real
portals rather than retaining multiple generations of caps. Physically sealed
the east WC and west security envelope gaps, retained true baggage feed openings,
and removed phantom structural surfaces. The source plan has 19 regions and
1,696 square metres with single floor ownership. Room footprints and useful
furniture were preserved.

Evidence: `Fixes/01_architecture/REPORT.md`, its `test_result.json`,
`ArtBible/Source38.json`, `ArtBible/Photos38.json`. Source coverage and bounded
native probes were recorded. Those records are versioned earlier checks, not a
complete visual approval of every later assembly.

### 2. Equipment modeling and attachment scrutiny

Rebuilt real counter/cabinet backs and shelves, scanner support links and captured
pivots, bakery bearers, supported service labels, fitted vanity/drain construction
and furniture feet. Corrected screen routing/defaults and actual place-setting
support heights. The preparation instruction board was separately replaced with
a compact, supported desktop guide. The secondary equipment pass inspected
1,473 evaluated parts across 38 prop families and registered 19 changed families.

Evidence: `Fixes/02_equipment/SECONDARY_REVIEW.md`, `secondary_findings38.json`,
`display_routing_results38.json`, `ArtBible/SecondaryAssembly38.json`,
`ArtBible/GuidanceMount38.json`. Twenty equipment source checks and seven display
routing cases were recorded. Native imports are recorded in `Native38.json`;
latest combined-build visual/state checks remain separately scoped.

### 3. Jetbridge, aircraft support and actual contact fits

Extended bridge decks beneath the walls, fitted carpet into the kick seals,
reseated unsupported bearings, and remodeled the docking membrane/ribs against
measured fuselage skin. Corrected aircraft tyre/apron, bridge truck and ground
power contacts. Relocated the seven stale cabin/business preview passengers that
had remained seated on the apron after the aircraft translation.

Evidence: `Fixes/03_airside/SECONDARY_CONTACTS39.md`,
`ContactRefinement39_Test.json`, `ActualAssemblyScrutiny38.json`,
`ActualGearContacts39.json`. The real-source test covers 11 export families and
94,250 evaluated faces without zero-area faces. The earlier source floor/roof
coverage sampled 4,390 points for each. These measurements are not substitutes
for a current full native boarding/departure run.

### 4. Whole-shell roof/glass union and differentiated room flow

The Flow39 pass remodeled 29 unequal-height roof-step/plenum boundaries and
merged/unioned 67 glazing-frame solids so repeated corners/transoms no longer
share visible faces. Widened the first check-in opening from 1.9 to 2.6 metres.
Built six differentiated curved/asymmetric openings, continuous fitted reveals,
protected bases, a supported cafÃ© arrival ledge, a welded route inlay and clearer
mounted destination cues. Removed the overlapping cafÃ© title and 18 retired
direct scene labels. Corrected stair riser/tread contacts, gallery table bases,
canopy fits and degenerate thin retained profiles.

Evidence: `Fixes/01_architecture/Flow39/REPORT.md`, `Validation39.json`,
`Coplanarity39.json`, its eight genuine Blender source previews, and
`ArtBible/Flow03Source.json`. The expanded source suite passed 48 physical probes
with no planar overlap candidates in its stated architectural scope.

Native distinction: the first assembly probe run was **47/48**, not a complete
pass. The disputed roof ray began within a lower roof solid and exposed native
one-sided complex-collision behavior. `ArtBible/NativeRoofProbe39.json` records
the saved two-sided shell collision policy, both directions blocking, and nine
neighbor samples blocking. No extra geometry was added for that discrepancy.

### 5. Exterior/window fitting and cockpit-view reconstruction

Removed the six added cockpit tube outlines while preserving the six true panes
and pressure-shell apertures. Remodeled hollow curved shade pockets, actual open
C guides, fitted returns and felt mouths; moved shade stow travel into those
pockets. Restored opaque weather seals and rolled the actual bored door leaves.

Evidence: `Fixes/03_airside/Exterior39/IMPLEMENTATION.md`,
`Exterior39_FivePasses.json`, `ArtBible/Exterior05Source.json`. Source regression
checked 48 shade mechanisms at 21 positions, including 290,304 slat samples;
the closest sampled stowed point remained about 47 millimetres inside the skin.
Native swaps are recorded. Current native shade motion, seal/glass appearance and
cockpit visibility still require their own final reviewed captures.

### 6. Procedural flight, rigid carrier and modeled actuators

Added coherent supporting apron/taxiway/runway geometry, actual cockpit procedure
controls, a rigid moving parent, 13 control surfaces, seven instrument needles,
seven gear/door assemblies, camera modes, original local audio and departure
interlocks. The same command/operate API drives both modeled controls and the
bounded procedure driver. Later flap-hinge work corrected the actual moving
surface pivots instead of relying on a scalar animation state.

Evidence: `Fixes/05_journey/Flight39/INTEGRATION39.md`,
`SourceGeometryPass39.json`, `ModelFlightPasses39.json`,
`ArtBible/Flight04Source.json`, `Flight08Source.json`. The source/control suites
are separate from native visual, collision or performance proof.

An earlier `FlightQA39.json` contains a native PASS for its own driver/attachment
run. Its captured frame statistics include capture pauses and are not steady
performance approval. The later fresh `FlightJourney39.json` failed at departure
because `Physical luggage 01`, already carried aboard, was classified as an
exterior obstruction. That failed run records source
`3da6d6d3427e7956f90d4a2ee48f7a136169b6042e1ee37374e9d9748e61d052`;
it does not certify the latest source named above. Current native retests are
pending, including the corrected carry-on behavior.

### 7. Original character forms, rigging, pose and chair calibration

Produced original modeled body/garment forms, large soft eyes,
restrained expressions, sculpted hair/caps, tailored costumes and authored slouch
poses. Built a shared 42-bone rig, seven actions, facial and seat-fit morphs,
color variants and actual chair-specific pose/contact checks. Remodeled upper
bench/cafÃ© chair depth while preserving contact datums and actor placements.

Evidence: `outputs/Characters/Revision39/HANDOFF39.txt`, its
`ArtBible/FinalBuild39.json`, `ChairFit39.json`, `Roundtrip39.json`,
`PlacementTests39.json`, and `ArtBible/CharacterAssets39.json`. Earlier native
mesh/animation imports and generated LOD counts are recorded. They do not prove
the appearance or fit of the later repaired joins below.

### 8. Real connected character joins after independent criticism

Replaced independently capped neck/forearm/palm joins with connected manifold
head/neck and arm/wrist/hand skin surfaces. The report covers **six base models,
65 posed collections and 24 chair fits**. All 24 recorded body/chair triangle-pair
counts are zero; the remodeled join regions report zero nonmanifold edges.
Original animation files, the 42-bone rest structure and protected face/lower-leg
details were retained and checked rather than rescaling limbs to hide contacts.

Evidence: `outputs/Characters/Revision39/ArtBible/JoinRepair39.json` and its
genuine close-up source captures. Source status is
`CONNECTED_MANIFOLD_JOINS_RIG_POSED_LIBRARY_AND_CHAIRS_PASS`, bound to character
source `d7da5506â€¦`. **Native reimport, generated-LOD behavior and final world
visual/contact review remain pending.** Publisher finding: `CH39-09`.

### 9. Primary UV import metadata across every base path

Verified all six frozen base FBX import paths. PassengerHoodie already had the
authored UV set in the primary slot. Five separate import copies promote the
existing authored set through UV-set name metadata only; player color aliases use
the verified PlayerBlue path. No source vertices, topology, weights, morphs,
material slots, animation files or UV coordinate arrays were replaced by this
adapter. The original frozen FBXs/master remain preserved.

Evidence: `outputs/Characters/Revision39/ArtBible/UVPrimaryAll39.json` and
`UVPrimaryTests39.json`. Four source/import-copy tests pass, including stale-input
rejection. **Native reimport, warnings from newly generated LODs and actual
appearance remain pending.** Publisher finding: `CH39-10`.

### 10. Queue and carry-on behavior corrections discovered on the fresh route

- Served queue passengers had been parked in the route toward security. Their
  runtime waiting endpoints now return to check-in at `[-34.4,-9.2]` and
  `[-35.7,-9.2]`, with subsequent spacing from the same rule. Visible rigs and
  their collision proxies must leave the security route clear. Finding `J39-01`.
- Holding a real carry-on could consume a seat/use interaction as a drop. The
  parent reports a runtime correction; seating and other aimed interactions while
  holding the bag require native retest. Finding `J39-02`.
- A carry-on inside the cabin falsely blocked the exterior departure sweep.
  The parent reports a runtime classification correction. The positive onboard
  bag case and a genuine exterior-obstruction negative case both require native
  retest; external obstructions must still prevent departure. Finding `J39-03`.

Evidence/provenance: installed `airport_journey38.py`, `airport_runtime.py`,
`airport_airside38.py` under the project `Content/Python`, the parent-reported
runtime corrections, and the earlier failed `ArtBible/FlightJourney39.json`.
These are recorded as corrections awaiting native retest, not new native passes.

## What is still required on the latest combined source

The parent is preparing final manifests after native retests. No final gallery is
published by this documentation pass. Current open checks include connected
character/UV imports and LODs; queue corridor clearance; held-bag seat/use; onboard
baggage departure versus real external obstructions; and the full fresh
entrance-to-airborne route. A starting-aboard debug flight remains separate from
that fresh route.

Performance needs an uncaptured run with hardware/build/settings and measurement
method recorded. Automated `-NoSound` review launches do not establish an audible
review. Final captures must be explicitly selected and hash-checked through
`FinalCaptures39.json`; failure, hold and move frames stay excluded. Source
previews remain labeled as source previews. Older successful runs cannot be used
to mark the latest joins, UV adapters or runtime corrections as finished.
