# Airport passenger journey22

Run ../Run Airport.cmd for the complete process, beginning at the entrance. Run SkywardAir/Run Plane.cmd to use the existing direct-to-cabin shortcut. The installed Unreal Engine is required; this is an editable local game preview.

WASD and mouse move/look. E or click operates the control under the crosshair. You can check in while holding a suitcase. At a bag-drop control, the held suitcase is placed using native forces and registered once it rests on the moving belt. Checked baggage is optional. Walk fully through a security portal, then validate your pass at A07. Walk along the jetbridge through the actual open aircraft door. Economy03E is the ticket seat; use the right aisle through the galley. E sits; Space stands. B opens/closes the journey boarding pass. V toggles avatar view and F7 changes pilot colour.

Source map: /Game/Airport12/L_Airport_Journey22, based on the saved character21 map. Runtime: SkywardAir/UnrealProject/Content/Python/airport_journey22.py. The airport geometry remains editable in Compact12/Airport.blend; the aircraft and character sources are separate. SourceAssets/build_journey22_unreal.py reproduces the journey map from the preserved character21 baseline. Test Airport.cmd repeats the rendered process and saves JourneyQA22.json plus nine photographs.

The test moves the actual pawn from the entrance to the aircraft seat without teleporting along the main route. Separate invalid-state fixtures test denied boarding. The screenshot hashes, runtime dependencies, ticket receipt and bag conveyor displacement are recorded in ArtBible/JourneyQA22.json.

Narrative/Cast22.json binds two named fictional individuals to existing cabin passenger actors and records their requested Jewish background separately from their story role. No religious stereotypes or religion-based behavior are added. Later story events and individual motives remain to be authored.

Limits: boarding ends inside the parked aircraft. Takeoff/flight remains the separate existing flight mode. Baggage is physically accepted and conveyed; a full airport baggage-sorting/loading AI is not implemented. Broader character art, existing seated NPC foot-scale issues and performance optimization remain separate work. Original aircraft/crash sources and previous maps are preserved.
