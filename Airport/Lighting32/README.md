# Fixture lighting revision32

Run Lighting32.cmd opens the same check-in entrance with revised lighting. Main Run Airport uses the revised map but still starts at the original airport entrance. The room layout and interactions are retained from Arrival31.

The inherited skylight was set to65 and flooded the room from all directions. Its intensity is now8, with a black lower hemisphere. Eleven room sources align with modeled diffusers: five ceiling fixtures, two upward fixtures, two aimed wall washers and two kiosk task lights. Sources sit just outside their own lenses rather than within the mesh, use explicit lumens and cast shadows. Adjacent lights respect room partitions. Wall washers point toward the timber service alcoves instead of into the room. Uplights illuminate the ceiling above their housings.

The local exposure is fixed at EV5.0. Screen-space global illumination adds approximate reflected light on the existing DX11 renderer. The strong original ambient wash is reduced while the fixture lighting supplies most of the interior illumination. Posters and desk signs receive room light. Information screens and the backed queue display retain emissive display materials. The earlier clear-resolution profile remains active.

Airport_Lighting32.blend preserves editable geometry and light positions. Its light metadata retains native lumens; the Blender watt conversion provides a preview rather than an exact renderer match. Native map: /Game/Airport32/L_Airport_Lighting32. SourceAssets/native32.py changes lights, local post processing and sign materials only; no geometry is reimported and no full airport rebuild is performed. SourceAssets/source32.py maintains the Blender source. Previous map/source and affected launch/runtime files remain available.

verify32.py checks fixture positions, shadows, authored ambient level, screen-space bounce and actual1920×1080 viewport size; captures four room views and a matched lamps-off diagnostic. review32.py verifies hashes and measures the images' linear relative-luminance response. These are source/lighting checks, not calibrated lux measurements or a full airport journey replay. Screen-space bounce is view-dependent and can show some noise; other airport sections may need their own fixture balance after the global-fill correction.

Reference: [Epic global illumination methods](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/DynamicGlobalIlluminationMethod?application_version=5.7).
