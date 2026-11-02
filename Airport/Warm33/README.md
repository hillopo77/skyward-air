# Warm lighting correction33

Run Warm33.cmd opens the check-in entrance. WASD move, mouse look, E interact. The existing check-in flow and layout remain unchanged.

The user rejected the dark horror-like lighting and clarified that supportive ambient light is welcome. The target is a bright, warm and welcoming airport, with fixtures leading the light rather than a strict source-only simulation. The skylight is restored to36, its lower hemisphere contributes again, exposure is fixed atEV5.9, and ambient occlusion is reduced. Screen-space GI is disabled to avoid the noisy dark ceiling. Ceiling surfaces are warmer and lighter; plaster normal detail is restrained.

Both large suspended fixtures are remodeled with visible glowing underside diffusers. Their rect-light sources sit beneath the lenses and point downward. Their broad fill softens the room, while the smaller ceiling and desk fixtures retain shadows and warm accents. There are no upward-pointing large panels or burned-white ceiling halos.

Editable source: Airport_Warm33.blend. Native map: /Game/Airport33/L_Airport_Warm33. source33.py changes just the room-family mesh and editable lights; native33.py imports that one family and balances lighting/material instances in a separate map. Previous versions and affected runtime/launcher files are preserved. verify33.py captures five actual native views and checks source directions, ambient setup, room mesh and viewport dimensions. review33.py validates captures/source hashes and generates Review.html.

The Blender light-energy conversion is for preview; native lumens and the saved Unreal map are the playback reference. This is an artistic lighting balance, not calibrated architectural lighting. No full airport journey replay or sustained-performance test is needed for this visual correction.
