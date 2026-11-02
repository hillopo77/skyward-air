# Skyward Air Detail36

The normal Airport/Run Airport.cmd now opens Detail36 from the forecourt. Run Detail36.cmd does the same. Review Security36.cmd starts at security with a local preview boarding pass so the changed rooms are immediately reviewable. WASD/mouse moves and looks, Shift runs, E interacts. The installed project Unreal Editor is required for this local editable preview.

## What changed

The operator console is against the staff wall, not behind the right detector lane. The exit leads through an aligned 3.2 m opening; the bench, charging table, suitcase and sightline-blocking plant are off the main gold route. Repacking has a separate side alcove. Screening directions, floor inlays and the junction directory make the decision points readable.

The repeated generic hanging boards at the room entrances are removed. A07 has a timber identification tower, A08 a rounded sage entrance and circular marker, Cloud Nine a timber entrance and fitted beam fascia, and the toilets have wall identification. Existing in-room flight information remains.

Cloud Nine now has fitted cabinets with backs/shelves/hinges/handles, an espresso machine with group heads/portafilters/wands/selectors/gauge/grate, grinder and cups, a glazed bakery display with price-ticket mounts and modeled food, a supported register/card reader/napkin dispenser, and tea urns with taps/lids/sight glasses/drip trays. Three open sorting-bin stations serve the café and gallery; a fourth serves A08. Extra tables, chairs and place settings furnish the room. The confusing large wooden baffles are removed; a 4.4 m dining soffit and four down-facing terracotta pendants give the dining side a more settled scale. The upper gallery remains accessible.

Both lounges have seating clusters, cushioned sofas, oval tables, travel artwork, magazines and luggage storage while retaining their circulation paths. The existing aircraft, check-in and entrance remain in the scene.

## Editable and runnable outputs

Airport_Detail36.blend is the complete editable master, including the linked detail-kit scene. Exports/airport_layout.json records placements, room openings, targets and cameras. Exports/FBX and airport_assets.json hold 18 new/adapted families. The native map is /Game/Airport36/L_Airport_Detail36 in ../../SkywardAir/UnrealProject/SkywardAir.uproject. Corrected close-up meshes are imported under /Game/Airport36/FinalMeshes36 and /Game/Airport36/FinalPolish36; the fresh import avoids retained FBX section/material ordering. Flow35 source/map and RecoveryBefore36 retain the prior state.

SourceAssets/model36.py and refine36.py retain the authoring recipes and the focused scrutiny work. The saved master is the editable source of truth. This project builds on the existing native maps, materials and runtime rather than providing a separate packaged game.

## Verification and photographs

ArtBible/WalkEvidence36/QA36.json records 91 passing checks: both screening lanes, the aligned exit, café access, upper gallery and descent, both lounges, actually sitting/standing at the new A07 sofa, boarding-pass use and continuous walking across the bridge into the aircraft. It begins after check-in with one explicitly recorded setup teleport, then uses no walking teleports. It does not claim to replay check-in. The unchanged earlier check-in has the Terminal34 route proof.

The route screenshots are archived beside that report. After the walking check, material bindings, bin interior normals and pastry contact were corrected without changing the room layout or walking paths. ArtBible/Photos36.json records the final 16 raw 1920 × 1080 native photographs in Screenshots/. Review.html presents them. ArtBible/Delivery36.json verifies source hash agreement, FBX hashes, runtime hashes, the native map and photo hashes. The local HTML source, links and image existence were checked; no browser-rendering claim is made.

The engine FBX import logs include tangent/binormal warnings on some small or flat parts. Native screenshots were scrutinized for visible shading problems. No clean-room material rebuild or unsupported performance certification is claimed.

## Remaining work

Inherited character art and some seated/standing poses still need dedicated work. Broad distant scenery, crowd navigation, interaction for every new café prop, sustained performance measurement, multiplayer and standalone packaging remain separate. The new café equipment and food are modeled visual assets; the existing airport journey and seating interactions remain playable.
