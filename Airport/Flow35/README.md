# Skyward Air Flow35

Run the main Airport/Run Airport.cmd or this folder's Run Flow35.cmd. Default play starts at the forecourt; -Checkin still opens the check-in preview. WASD/mouse moves and looks, Shift runs, E interacts. Follow check-in, preparation, screening, repacking and Gate A07. Cloud Nine is the timber entrance on the left of the concourse; A08 North Lounge is straight ahead.

The affected areas were replanned: screening is3m farther inside, staff signage is moved off the main route, the repacking bench faces the public aisle, entrance widths/profiles differ, the cafe has306m² of floor area, and the gallery has72m². A2.4m-wide two-flight straight stair replaces the switchback. Dining chairs face their tables. A07 has fewer seat banks and an accessible boarding path. A08 moves north into a separate128m² lounge, with the wall over1m clear of the unchanged aircraft's complete bounding envelope.

Airport_Flow35.blend is the editable master. Exports/FBX holds15 new architectural/detail families; inherited detailed furniture and equipment remain in the project. The native map is /Game/Airport35/L_Airport_Flow35 in ../../SkywardAir/UnrealProject/SkywardAir.uproject. SourceAssets/RecoveryBefore35 preserves changed runtime/launcher files. The34 map and source are unchanged.

ArtBible/QA35.json records65 passing checks. It starts after check-in with a real local ticket and one explicit setup teleport, then walks continuously through screening, repacking, cafe, upper gallery and back down, both lounges and A07 boarding into the actual aircraft. It does not claim to replay check-in; the unchanged check-in has the earlier Terminal34 RouteProof. Stair tests verify eye height4.77m upstairs and1.62m after descent. Final photos are15 genuine raw1920×1080 captures from the same run.

The first test exposed missed stair-floor samples at long frame times. The final floor selector preserves connected stair surfaces, with normal swept vertical movement, and restores the ground landing. It is scoped to the new airport stairs and does not affect the aircraft hold. Final scrutiny also added missing gallery table pedestals and baffle hangers, turned shelves inward, attached lounge timber backing and cleared the screening exit.

Screening traversal now permits movement appropriate to the frame time and the native pawn speed, instead of rejecting every step over1m. The distance remains bounded so the after-check-in setup teleport does not count as a detector traversal.

Review Security35.cmd opens the changed section with a local preview ticket. The normal launcher begins at the entrance.

Remaining limits: inherited character art and some poses, broad distant scenery, general crowd navigation, all-prop interactivity, sustained performance certification, multiplayer and standalone packaging. This is an editable local prototype. The gallery's HTML source/links were verified, without a browser-rendering claim.
