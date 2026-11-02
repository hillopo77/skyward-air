# Flight39 cabin physics: current method and verification

The current adapter gives each registered cabin prop one consistent aircraft reference frame. Chaos simulates its relative movement, gravity, contacts and pickup force. The carrier pose transports the cabin and its small prop registry once. It does not also add aircraft cruise velocity to each native body while that body remains inside.

The carrier and transported props use `TeleportPhysics=True` for the reference-frame change. This preserves physical velocities and propagates the carrier change to attached children. It does not disable collisions, change a body's simulated status, place it at the hand, or bypass an obstruction. The ordinary pickup spring still applies a bounded native force. Its `carrier_velocity39` compensation is zero only while the held body uses aircraft-relative native velocity.

Dropping a prop leaves its real relative velocity intact. Throwing applies the existing native 9 m/s impulse. When the simulated body crosses the reference envelope, the adapter gives it the carrier's point velocity once and returns it to world physics. Entry/re-entry converts incoming velocity once. External airport props, ground vehicles and tow assemblies retain world physics.

Only the small `G.S.physics` registry is checked every 0.25 seconds; a held newcomer is checked immediately. The adapter does not scan or rewrite the whole scene every frame. Source geometry, interaction visibility and collision responses are unchanged by this fix.

## Velocity and timing interpretation

- `component.get_physics_linear_velocity()`: aircraft-relative native velocity while registered; world native velocity outside.
- `frame.relative_velocity(actor_or_component_or_name)`: relative velocity in either case.
- `frame.world_velocity(...)`: equivalent world velocity, adding carrier point velocity only to a registered relative body.
- `frame.motion_dt`: actual world/carrier clock. `frame.physics_dt`: configured capped Chaos clock. Native relative motion may advance less simulated time than a long render frame; observed rendered displacement should be measured from positions if that distinction matters.

The active PhysicsSettings cap is queried once. If Unreal exposes its property failure as a generic exception, the adapter reads the actual saved project configuration. This project's cap is 0.033333333 s. No guessed cap is used if both sources fail.

## Evidence and limits

The 27 bounded Python tests pass. They cover actual-position registration, drop/throw, one-time entry/exit conversion, external props, 16 ms to 1 s hitches, the generic Unreal property exception fallback, held aiming, opaque walls, nonrecursive interaction dispatch, all 44 modeled flight controls, aircraft transforms and the integrated procedure driver. These are not native collision proof.

The parent's actual native `ArtBible/BagPhysics39.json` now passes its explicit staged diagnostic: 12 seconds of held operation at a 20 FPS cap and a nominal 90 m/s aircraft start, then ordinary release for 3 seconds. Held distance was 1.2578 m. Released local drift was 0.0691 m; final local COM height was 0.3265 m and relative speed 0.1342 m/s. The body remained registered. This setup deliberately positions the aircraft, pawn and bag once and is not fresh passenger-route evidence. The full fresh journey must be rerun with this adapter after the remaining source imports.

This is a local gameplay reference-frame adapter, not a certified inertial aircraft/structural solver or a multiplayer replication implementation. A blocked suitcase remains subject to real cabin collisions; arbitrary paths through closed furniture are not promised.

## Envelope safety follow-up: implemented, native retest pending

The previous broad `point_inside` box corresponded to parked source x=[12,20], y=[-8.5,43.5], z=[-3.6,6.5]. The actual Revision18 metadata gives a 4.79688 m floor width centered at x=16, main cabin ending at y=35.1, cockpit front y=-5.4, maximum inner ceiling z=2.4, and lower-hold floor z=-2.05. That broad box was not a pressure-shell test.

The old box admitted [12.5,0.675,1], on the docking cab floor x=[10.5,13.916], and [16,40,1] behind the occupied cabin. The new `flight39_envelope.py` derives four real cabin/cockpit/hold/stair volumes. Main-cabin inner wall faces are x=[13.62,18.38]; cockpit inner wall faces are x=[14.04,17.96], from actual navigation collision boxes. The lower hold and sloping stairs use the actual navigation-floor rectangles and heights. Numerical floor/ceiling contact allowance is explicitly 0.03 m.

Implemented checks:

1. Prop registration, continued transport and pawn attachment use the metadata-derived volume union.
2. Departure exemptions use complete colliding native actor bounds, check coverage through the union (including structural deck gaps), and reject L1 threshold or bridge overlap. COM alone cannot exempt a straddling suitcase.
3. Stow occupancy includes loose and held known physics props against actual bridge deck polygons and their walkable height. Props below the apron do not occupy an elevated bridge. Fully aboard bodies are allowed.
4. A bounded parked exit check hands escaped bodies to world physics with zero carrier speed, preserving their velocity without position writes. It does not wait for a later aircraft pose change.

The combined flight/interaction/envelope suite passes 38 tests; the existing 8 airside acceptance tests and 43 policy assertions also pass. Exact manifest fields, cells, runtime hashes and cases are recorded in `EnvelopeSafety39_Checks.json`. The prior staged native held/drop PASS remains evidence for the local-physics architecture; the additional envelope/safety changes require the parent's native retest. The full fresh passenger/flight route remains pending with the combined final runtime.

Reference: [Epic Set Actor Location And Rotation](https://dev.epicgames.com/documentation/unreal-engine/BlueprintAPI/Transformation/SetActorLocationAndRotation).
