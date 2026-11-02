# Skyward Air Clarity37

Review Exit37.cmd opens the changed view after screening, with a local preview boarding pass. Run Clarity37.cmd and the normal Airport/Run Airport.cmd start at the airport entrance. WASD/mouse moves and looks, Shift runs, E interacts. The existing installed Unreal Editor is required.

## Visual changes

The problem was layered geometry and unrestricted views through internal glass. The revised northern terminal uses solid room partitions. Glazing is concentrated at the exterior, with broader panes and wider, matte mullion spacing. The café, gate lounges and circulation spaces now read as separate rooms.

Two visible generations of old fixture geometry were present. The saved source removes 380 obsolete north fixture parts, including old suspension wires and roses, plus 36 raised ceiling-trim parts. It replaces the north fixtures with 32 coordinated downward practicals, retaining the four café pendants and the existing warm ambient fill. Legacy north facade modules, roof cassettes and redundant columns are removed. Southern entrance/check-in fixtures are retained. New architecture uses restrained specular response; sharpening is reduced to0.1 in this revision.

The main exit view ends at a mounted A07 direction board. The gate entrance is an offset3m-wide opening. The gate foyer ceiling and floor match its current enlarged footprint, and the CCTV camera is mounted on the solid concourse side wall. The café detail, luggage bins, sofas, artwork, usable stairs, boarding and aircraft remain.

## Editable outputs

Airport_Clarity37.blend is the complete editable master, with Airport37_EditableClarityKit retaining the separate source parts. Exports/FBX and airport_assets.json contain14 revised architecture/detail families. The final native map is /Game/Airport37/L_Airport_Clarity37 in ../../SkywardAir/UnrealProject/SkywardAir.uproject. The final wall and foyer meshes are under Airport37/FinishMeshes37; other new meshes are under Airport37/Meshes. Existing materials, furniture, aircraft and journey code are shared dependencies.

The source recipes are model37.py followed by finish37.py. The latter fixes the enlarged foyer coverage, narrows the A07 opening and remounts the CCTV unit. The saved master is the source of truth. Detail36 source/map and SourceAssets/RecoveryBefore37 retain the previous state. No external assets or paid generation were used.

## Verification

ArtBible/QA37.json records93 passing checks and12 genuine raw1920×1080 screenshots. Testing starts after check-in with a local ticket and one explicit setup teleport, then walks through both screening lanes, the exit, café/gallery stairs, both lounges, the actual new sofa interaction, boarding and across the bridge into the aircraft. There are no walking teleports. Two real visibility traces also verify that the new solid partitions block the layered room sightlines. The unchanged check-in retains the earlier Terminal34 route proof; this focused test does not replay check-in.

ArtBible/Delivery37.json verifies agreement between saved source, FBX files, native map, runtime and screenshot hashes. Before/after images in Review.html are native photographs; the local HTML source and file links are checked without a browser-rendering claim. Import logs retain the engine's tangent/binormal warnings on some small/flat parts; final inspection is based on native screenshots.

## Remaining limits

Character art and some poses, distant scenery, general crowd navigation, interaction for every modeled prop, sustained frame-rate certification, multiplayer and standalone packaging remain separate work. This is an editable local prototype.
