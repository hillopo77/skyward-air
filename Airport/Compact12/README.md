# Compact airport 12 and character library

Run **Run Airport.cmd** in the parent Airport folder. It starts at the compact terminal entrance. **Run Plane.cmd** in SkywardAir starts aboard the same updated aircraft. The installed Unreal Engine is required; this is an editable single-player preview.

WASD and mouse move/look. Shift runs. Aim the crosshair and press E or click to interact. Tab toggles fast spectator movement; Space/Ctrl move vertically. V toggles the player avatar while walking. F7 changes the player pilot colour. E drops a held bag; click throws it. An extinguisher uses hold-click to discharge, E to drop and R near its bracket to stow/refill. Aircraft shades operate at their fixed rocker switches.

The passenger journey is check-in, a physical bag drop, the security portal, Gate A07, the jetbridge and the open aircraft entry. A08 is an alternate waiting gate. The café, travel shop, arrivals carousel, enclosed washrooms, mezzanine and apron service ramp complete the terminal. The airfield includes a marked runway, taxiway, tower, hangar and ground equipment. The tug pulls two articulated dollies.

The new terminal is 35 × 40 metres. The earlier 7,224-square-metre layout is preserved separately. Ten cumulative native airport maps are saved under /Game/Airport12; the final map is L_Airport_Compact12. The animated cast is populated in that final map.

Editable sources are Compact12/Airport.blend, Characters/Characters12.blend and SkywardAir/Revision18/Plane_Refined18.blend. The airport master links the character pose collections and aircraft library. The character workshop contains ten skinned variants, a shared 20-bone rig, eyelid/eye-look morphs and seven native animation clips. Five colourful pilot variants are selectable player appearances; five human passenger variants form the NPC cast. NPC walking paths and greetings are authored. Review specimens are hidden during normal play.

The aircraft retains its existing detailed interior and gameplay. Revision18 fits the business wall liner outward by 12 cm, preserves the furnishings, adds 48 five-section captive window shades and uses softly tinted clear glazing. The cockpit apertures have modeled pearl edge reveals. Existing aircraft/airport texture artwork is retained; the changes concentrate on geometry, character materials, glazing and fixture lighting.

Use Rebuild Airport.cmd after source changes. Rebuild-Airport.ps1 -SkipModels reimports existing FBX exports and repopulates the native maps. Test Airport.cmd performs focused native acceptance. Capture Airport.cmd recreates the saved review views. Rebuilds do not automatically certify the gallery; retain and refresh acceptance and screenshot evidence after changes.

Remaining scope: general passenger AI, multiplayer, production packaging, hand/prop-specific interaction animation and calibrated physical simulation remain future work. The stylized models are original work guided by the supplied Dear Passengers screenshots. Exact visual parity is not claimed. The legacy crash maps and the original Plane.blend remain separate.
