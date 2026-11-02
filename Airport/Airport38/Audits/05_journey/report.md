# Review5 — the playable journey

The journey has real interaction foundations, but several success/availability states are disconnected from their promised physical outcomes. The existing93-check pass cannot certify the whole map because it begins after check-in and does not cover these negative paths.

This is a read-only code, layout and evidence review. It does not pretend that this agent independently operated every control in-game.

## J01 — P1: Automatic proximity doors override the room access policy before animation

Status: verified_code_path; native_approach_test_required.

- airport_runtime.physics: automatic doors assign target solely from pawn distance, then interpolate fraction.
- airport_rooms24.physics calls its base first, then assigns the access24 target. The following base call overwrites that policy before moving the door again.
- Both screening entry leaves are automatic and access24=checked_in; both exit leaves are automatic and access24=security. Manual act denial does not govern their automatic motion.

Correction: Evaluate proximity AND access state once, before interpolation. Put the access policy in the authoritative door target function; remove the competing post-animation assignment.

Acceptance:

- Approach screening entry without checking in: both leaves remain closed and block walking.
- With a ticket, entry opens normally. Approach exit before completing the lane: it stays closed.
- After full valid screening, exit opens; no frame or slow-frame condition briefly opens a denied leaf.

## J02 — P1: Walking mode has a global invisible zero-height floor and stale outdoor terminal coverage

Status: verified.

- floor_at_source adds the Cabin deck at z0 whenever abs(feet_z)<.28, without testing x/y against the cabin footprint.
- When no candidate exists it returns the previous feet height/name rather than a bounded physical floor or gravity behavior.
- Clarity37 floors still include Compact terminal rect[-49,-14,-22,18] and Service ramp rect[-18.4,-15.6,18,53], even though the revised north-east region is exterior. Audit3 separately confirms the obsolete bridge/service platform context.

Correction: Bound the cabin fallback to its actual translated deck; derive terminal floor regions from current occupied room footprints, with intentional apron/ramp floors only. Decide an explicit behavior for leaving physical walkable surfaces; never silently preserve a floating deck height.

Acceptance:

- Perimeter sweep includes positions outside every room and bridge: no phantom z0 support appears over exterior grass/void.
- Both WC/security envelope breaches are sealed geometrically and do not rely on a hidden floor to conceal them.
- Gallery and lower aircraft hold still preserve correct eye height and use only their connected surfaces.

## J03 — P1: Security equipment reports a screening process that is not connected to baggage clearance

Status: verified.

- airport_runtime.act(scanner/security) sets screening_armed=True and says baggage screening active.
- A repository search finds screening_armed only at that assignment; no simulation or validation consumes it.
- airport_journey22.physics grants security solely from checked_in plus full portal traversal. It does not check carried baggage, tray use, a scanner result or the supposedly armed state.

Correction: Create one coherent prepare/load/scan/collect policy. Keep checked-baggage drop optional, but require any carried cabin bag to pass the scanner before person clearance; allow an unencumbered passenger to traverse normally. Either make the scanner control meaningful or remove the false Start screening promise.

Acceptance:

- A checked-in passenger carrying an unscanned bag cannot obtain security_cleared merely by walking the detector.
- A bag placed on the scanner belt visibly passes through, is marked scanned only after valid transit, and can be collected.
- Empty-handed screening remains simple; duplicate press/traverse actions cannot award false completion.

## J04 — P1: A bag is irrevocably registered before the promised physical transfer occurs

Status: verified; overlaps equipment EQ01.

- airport_journey22.physics accepts any unheld supported bag anywhere inside a bag-drop rectangle, sets bag_accepted, appends the bag to checked_bags and registered_bags.
- act(pickup) then rejects retrieval of a registered bag, although the verified belt ends against a wall and there is no transfer/collection stage.
- The earlier journey QA checks a bag is a native body on the belt; it does not verify its onward destination or end-of-belt handling.

Correction: Separate loaded, screening/in-transfer and safely-transferred states. Complete registration only after the bag crosses the guarded hatch/transfer endpoint into the real backstage system. Provide recovery for stalled or cancelled transfer before that point.

Acceptance:

- Follow one real suitcase from player hand through each belt and physical wall opening to supported backstage storage.
- No accepted bag remains pushing against a wall, falls off an unsupported end or becomes irretrievable mid-transfer.
- Ticket bag count and progress messages correspond to the actual completed transfer, not merely belt contact.

## J05 — P1: Lavatory occupied indicators do not provide an occupied-door lock

Status: verified_code_path; native_privacy_test_required.

- airport_runtime.act(slide) toggles door target regardless of occupancy. For fixed releases it calculates occupied only to choose red/green material.
- Closing using inside_release=True makes the indicator red; an outside_release target can immediately toggle the same door open because there is no persistent occupied/locked gate.
- The WC interactions have fixed_release/inside_release but no access24 or independent privacy state.

Correction: Maintain explicit occupied/locked state per cubicle. Inside close/lock sets occupied; outside normal release respects it; inside release always permits exit. Keep indicators synchronized with the real state, with an explicit emergency release only if intended.

Acceptance:

- Close/lock from inside: outside normal control cannot open the door and displays occupied.
- Inside release opens safely and restores vacant.
- Both indicators agree; close/open, interrupted animation and repeated clicks cannot create a misleading colour state.

## J06 — P2: A08 presents a boarding action even though it only supplies information

Status: verified.

- The A08 interaction has kind=boarding and title=Gate information, gate=A08.
- airport_clarity26 maps every boarding target to the Boarding hint. Clarity26/SourceAssets/hud26.py defines that hint as E Scan boarding pass.
- airport_runtime.act rejects gates other than A07 and merely says SA107 boards at Gate A07.

Correction: Represent the A08 station as a context-specific information action with the correct prompt and useful gate/flight status. Reserve boarding-pass scan prompts for an actual enabled boarding action.

Acceptance:

- At A08 the hint says information/status, not scan boarding pass.
- Using it explains the relevant status and route to A07 without denial/error feedback.
- A07 still validates the pass and opens its real bridge entry.

## J07 — P2: Coffee service is a success cue without a serving interaction or outcome

Status: verified.

- The current visible espresso station has a vending target titled Coffee service.
- airport_runtime.act(vending) plays GateOpen, prints Refreshments ready and emits Refreshment selected; it creates no drink, updates no machine/service state and offers no pickup.
- Modeled café cups/food remain static visual detail. This limitation is documented in the previous README, but the player-facing service action still promises an outcome.

Correction: Provide one honest, bounded service loop: dispense a cup to a supported pickup position and allow the player to hold/use or return it. Otherwise remove the functional service prompt and present the station as clear scenery. Avoid using the boarding-open cue for coffee.

Acceptance:

- A service request has a visible result at a reachable supported pickup position, with correct interaction and sound feedback.
- Repeated use cannot spawn intersecting/unbounded objects.
- A purely decorative station never reports a completed service action.

## J08 — P2: Queue service and the player call are driven by list timing rather than counter availability

Status: verified.

- Every3.2seconds, tick pops an NPC from remaining and starts its service/departure path.
- When the final NPC is popped, called=True and Player called to check-in desk30 desk=01 are emitted immediately, before that NPC reaches or leaves its service position.
- All authored NPC service paths include[-31.7,-14.6], corresponding to desk02; desk01 is at[-30.3,-10.6]. The marker claims both desks, while availability is not modeled per desk.

Correction: Use explicit counter assignment and service state. Advance one passenger into a genuinely free counter; call the player when an assigned counter is free and its approach is clear. Keep NPC and player guidance consistent with that counter.

Acceptance:

- At each call, the indicated workstation and public approach are free of another passenger.
- NPC service/exit motion cannot cross the player or other NPC without collision/avoidance.
- Both desk numbers, queue sign, call and actual service position agree. Self-service kiosks may remain a clearly marked optional route.

## J09 — P1: The current quality gate bypasses the systems now failing in the playable map

Status: verified.

- clarity37_review setup explicitly sets checked_in=True and bag_accepted=True, issues a ticket and teleports to[-42,-5.3,1.62] before its route checks.
- The93 checks mostly verify predetermined waypoint arrival, selected furniture, two partition traces, stairs and boarding. They do not exercise current queue/check-in, baggage endpoint transfer, access denial, lavatory privacy, perimeter escape, or temporal stability.
- The README discloses the after-check-in setup and references an older Terminal34 proof, so this is a coverage gap rather than fabricated evidence. New world geometry and inherited systems still require current end-to-end tests.

Correction: Add a current fresh-start journey and negative-path suite, plus per-finding visual/temporal checks. Keep focused route tests, but do not use their passing count as whole-map sign-off. Each repaired defect needs a reproduced-before and passing-after acceptance result.

Acceptance:

- Fresh launch through entrance, real queue or kiosk, physical bag transfer, security, repacking, gate, bridge and cabin seat completes without setup-state flags or route teleports.
- Negative cases cover denied entry/exit/boarding, occupied WC, boundary holes, outdoor phantom floors and stalled baggage.
- Stationary/moving frame captures and supporting object transforms distinguish z-fighting/AA shimmer from physical motion; all five fix reports are traced to evidence.

## Coverage

- **entrancefoyer/checkin**: Reviewed actual queue/call, optional kiosks, pickup/drop state and guide/HUD code; J04,J08,J09. Current check-in desks are not proven mutually overlapping; equipment reviewer found internal assembly/wall defects.
- **publicreturn/landsidecorridor**: Current floor-envelope/fallback and physical access policy reviewed; J01,J02; architecture reviewer verifies west envelope seam.
- **security/recovery**: Person traversal is real, but baggage scanner action is not connected to clearance and access policy is overridden; J01,J03,J04.
- **concourse/gate07foyer/gate08foyer**: Cross-reviewed sign and coplanar roof findings; contextual A08 action mismatch J06. Do not diagnose remaining A08 flicker as a room XY-footprint mismatch.
- **gate07/gate08**: Boarding conditions and gate-specific prompts reviewed; J06. Occupied bench filtering DOES exist in characters12_runtime and is not counted as an uncovered defect.
- **cafe/cafefoyer/gallery**: Real stairs/eye-height controls are present. Coffee service has no physical outcome, J07. Detail and roof defects are covered by equipment/layout/render reviews.
- **amenitylobby/amenities**: Cross-reviewed live exterior breach and floating/back-facing identifier; added explicit privacy-state defect J05.
- **arrivals/airside/jetbridge**: Cross-reviewed orphan service ramp, obsolete floor and global deck fallback J02; shifted aircraft must have schema-aware point/navigation/boarding updates per airside review.
- **operations**: Current staff-only lock is intentional policy; no staff credential is granted. This is not counted as a defect by itself. Staff sign/attachment and shelf readability issues belong to layout/equipment.

## Claims deliberately not made

- No basis to say all props physically jitter: baseline scanner/bag transforms are invariant; ceiling image instability has a verified coplanar cause.
- No missing occupied-seat guard: characters12_runtime filters and guards seated NPC locations.
- No invalid assigned03E seat: Revision18 contains Economy seat03E12.
- Staff-only access restriction can be intentional; do not unlock every room merely to make a review pass.
