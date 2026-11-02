# Airport38 work in progress

User explicitly requested five critical review agents followed by five NEW fix agents. Four total concurrent slots include root, so the agents run in batches. No questions requested. Continue implementation through native tests and genuine screenshots; do not stop at reports or plans.

## Review phase complete

Five read-only agents finished: audit1_layout (10 findings), audit2_equipment (13), audit3_airside (7), audit4_rendering (7 +2 unproven risks), audit5_journey (9). Reports/findings.json are in Audits/01_layout through05_journey. Some findings overlap; do not claim46 distinct bugs. Read them and track issue coverage.

Native baseline evidence: Audits/AuditInventory38.json (all StaticMeshComponents/ISM world bounds, materials/collision), SourceInventory38.json (134 effective asset part bounds), BaselineCapture38.json (60 real captures+live traces), BaselineAnalysis38.json. Screenshots in Audits/BaselineScreenshots. Fixed-frame ceiling sequence34 proves material alternation: pixel900,300 [48,51,59] ->[17,21,29] ->back; mean frame delta10.82/255. Roof35 underside and Room37_gate08foyer/cafefoyer ceilings bothz3.4. Scanner transforms stayed fixed;6mm bright gaps cause separate edge shimmer risk, not proven physical jitter. Both WC east/security west breach traces are unblocked. Baseline capture15_A08Cubby eye was inside a wall; don't use it as evidence. Other relevant captures were reviewed by agents.

## Fix phase

Three NEW fix agents dispatched and running:

1. fix1_architecture owns Fixes/01_architecture: coherent full shell/ceilings/floors/roof, actual perimeter seams, A08 foyer merge, signs/planters, role-based visible fixtures. Rebuild rather than patch old caps. Plan extends amenitylobby y-top to-1 and reserves baggage bay[-26,-22,-18.5,-12], arrivals main[-22,-14,-22,-12], return[-25,-22,-22,-18.5].
2. fix2_equipment owns Fixes/02_equipment: modeled scanners/belts/controls, counters, shelves, bin apertures, plant grounding, cabinet gaps. Bagdrop01 movesy-13,02stays-16.
3. fix3_airside owns Fixes/03_airside: complete bent enclosed bridge/dock, aircraft source/native/data +X16m, correct point-vs-delta conversion, swept forward clearance/interlocks, orphan ramp removal and tug parking.

STILL MUST SPAWN TWO NEW FIX AGENTS when slots free:

4. fix4_rendering: own Fixes/04_rendering, implement audit4 final AA authority, lighting roles, warm ceiling fill/shadow consistency, actual runtime profile, temporal/coplanar validation. Coordinate fixture metadata with1. Do not hide structural flicker with AA or freeze props falsely.
5. fix5_journey: own Fixes/05_journey, implement audit5 authoritative auto-door/access and WC locking, queue availability and service truth, actual bagdrop continuation/storage and scan state, honest A08 information action/coffee outcome, bounded floor policy (remove global Cabin deck fallback, old Compact floor ghost), translated crossing coordination with3. Add baggage annex equipment/transfer belt after2 front belts; use service openings supplied by1. This is real implementation, not merely tests.

Contract for all fixers is Fixes/CONTRACT.md. Agents write only their folders/modules, no shared Unreal/live Blender. Root assembles all plans, then builds equipment/airside/journey geometry and architecture last in one Blender source; native import serialized by root. Small factory-empty Blender tests allowed in agent folders.

## Root work remaining

- Build source/native integration harness using ctx API in contract: D,before,scene,a,R,A,P; require/replace/move/remove/add/new_collection. Moves must adjust related interaction points/labels. Capture baseline diffs, remove obsolete AP COLL proxies for replaced meshes, import fresh names/paths to avoid FBX retained material ordering.
- Run all five source modules and applicable native hooks; new saved source Airport_Repaired38.blend, new map /Game/Airport38/L_Airport_Repair38. Preserve37source/map and prior originals.
- Aircraft prepare_plane(P,D) goes after plane18_runtime.install and before configure; translate absolute data fields, NOT P.vector (used for deltas too), then append airport floors. Shift native/Blender aircraft roots once, including lights/cameras/proxies/attached objects. Fix legacy hardcoded boarding/spawn/gating coordinates only in38.
- Real tests: full entrance/checkin/physical bag transfer/security/boarding, denied door states before permission, WC lock, A08/info/coffee, both lanes, stairs/seat/pilot controls/window shade after aircraft translation; boundary wall traces and attempted crossings; geometric attachment/desk/bridge/grounding assertions; entire forward swept aircraft envelope vs terminal; parked tug/bags and meaningful prop interaction; same fixed and moving native frames for flicker/edges. Existing93route checks are insufficient alone.
- Publish issue coverage ledger distinguishing verified fix / unproven risk / remaining gap, genuine before/after photos and motion evidence, editable/runnable outputs, current launcher and review preview. No perfect/commercial/FPS claim without proof.

## Environment / cautions

Workspace C:/Users/zaran/Documents/Codex/2026-10-22/referenced-chatgpt-conversation-this-is-an. Blender5.2 at C:/Program Files/Blender Foundation/Blender5.2/blender.exe (actual directory has spaces: Blender Foundation/Blender 5.2). Python C:/Users/zaran/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe. UE C:/Users/zaran/Documents/Codex/UE/Engine/Binaries/Win64/UnrealEditor[-Cmd].exe. .uproject outputs/SkywardAir/UnrealProject/SkywardAir.uproject. UE helpers need require_escalated; normal workspace source edits don't.

No Unreal MCP tools available (searched); existing commandlet/runtime CLI used. Skill read earlier, recovery by separate source/map. Only one rendering game at a time. Default Get-Process may hide unsandboxed processes; require_escalated Get-Process with SkywardAir MainWindowTitle works. Avoid CIM (approval timed out earlier). No local HTML browser workaround: source/links verified, no browser-render claim.

Read-only diagnostic airport_audit38.py was added to Content/Python and temporary '-AirportAudit38' hook to airport_clarity37.py; preserved original in Airport38/SourceAssets/RecoveryBefore38/airport_clarity37.py. Restore this37module before final delivery; no permanent38fix is in baseline yet. Diagnostic game finished successfully and quit. Source/native inventory commandlets also finished.

## Update after first full assembly
All five review agents and all five NEW fix agents have been dispatched. Fixers1–4 delivered modules/tests; fixer5 source stable and runtime tests in progress. Full source assembly succeeded42newfamilies/381instances, but cross-asset checker detected structural interface candidates; fix1 reactivated to repair roof/plenum/corner interfaces. Fix4 corrected checker multi-plane aggregation and passes9tests. Native38 import is deferred until corrected source. Root wrote SourceAssets/native38.py, build_native38.py, install_runtime38.py, airport_repair38.py, repair38_review.py, review_native38.py, build_config38.json. Need copy journey_logic38 runtime dependency. All five source modules wired; architecture retains bridge light metadata. Current saved38source is interim, not final native/playable yet.

## Native integration update
Final Source38 SUCCESS43families,381instances, zero Coplanarity38 candidates. Native38 map/import success; final5servicefresh-path update synced source SHA01972fe14760b1ffe87218ce0d09e292fec2c5121c02b8e68d276df56d3276c3. Native/source hashes matched. Runtime installer wires38-only path and skips old capture/QA initialization after customreview setsG.CAPTURE/QA; oldcapture initially causedKeyError20_SeatBack17, corrected withoutnative rebuild. All65nativephotos capturedScreenshots; Photos38 SUCCESS all7geometryprobes PASS. Temporal38: fixedceiling mean.1853/255 vsbaseline10.816, probepixel900,300 constant27/31/38; curtain.1286 vs.3277 (new samplecadence.12s vsbaseline.6s, repeatfinalwithmatchedcadence). Inspected01,07,14,16,17,28nativeimages. 14camera too close/upcropped; changeeye[-29,10.8,1.62] target[-29,14,2.8]. Ceilingstilldarkwithwarmhalos: fixer4 reactivated nativeambientIBLrefinement.
FreshQA38 reachedstep19: realentrance/queue/freecounter/checkin/pickup/bagdropaimpassed20checks but bag02stalled COM[-28.53,-13.01,1.00] poweredtrue; nofalseacceptance. Fixer5reactivated and authored native apply_conveyor_physics lowfrictionPM_AP38_ConveyorRollers .045/.055 MIN; root MUST apply with4lightingrefinement thenrerunfreshQA. Newruntimeboundedconveyormotor/supportdiagnostics mustrecopy. MainQA containsnojourneyflagsetup,pawnteleports,bagtransforms. Targetednegative SafetyQA38 nowrunning separate scenarios (explicitsetupteleports); result pending. Must not runconcurrentgame.
Root newhelpers SourceAssets/safety38_review.py and journey38_review.py, review_native38.py --qa/--safety. install_runtime38 copies runtimefiles+qa_contract+newreview; character38usescurrentDplacements and fix5removescompetingqueuewalkers. Need finishpositivebag/security/boarding/seatQA,fixanyfailures,safetycases,fullvisualreview,motion/artifactcoverageledger/gallery/launcher. Source/scriptdeliverables not yet finalized.
