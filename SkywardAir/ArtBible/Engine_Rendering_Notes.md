# Runtime rendering checks

The first SM5/DX12 run produced five actual Unreal captures, but its ceiling was too dark and the sunlight too harsh. This failed the visual comparison gate.

The next DX12/SM6 trial was supported by the reported adapter capabilities, but exited with a GPU crash before capture. The log identifies an NVIDIA GeForce RTX 3060 Laptop GPU and driver 522.06, and warns that this driver is old. This is evidence of a local runtime failure, not a proven diagnosis of the driver as the sole cause.

The deliverable therefore uses DX11/SM5 with screen-space reflections and ambient occlusion, softer/reduced sun, calibrated emissive fixtures, practical lights, five shadowless rectangular bounce approximations directed towards the ceiling and five modest indirect point fills. Screen-space GI was removed after it produced visible noise and uneven ceiling shading. The project can be retested with Lumen/SM6 on a different or updated graphics setup later. No driver or system update was performed.

A later capture-tool crash came from a re-entrant map-save callback, not from the compatible renderer. The capture routine now guards against recursive ticks and leaves the map unchanged. Navigation also exposed sky-dome collision; the dome now has actor collision disabled and the NoCollision profile, checked after reloading the saved map.

Blender renders remain source-art previews. Actual runtime captures are prefixed `UE_`; `EngineValidation.json` records the latest capture and navigation test status. No frame-rate or final art-approval claim is made.

Revision 03 also corrects material binding by the imported source section identifier, includes exported corner normals in change signatures, and fixes the horizontal sign in the Blender camera direction conversion. Earlier oblique engine views are archived checks; UE 22–27 are the current camera-matched review views. Broad practical fills no longer cast hard point-like shadows, and instrument glass has separately reduced specular reflection. The engine is still brighter and flatter than the Cycles previews; this remains a visual refinement gap.
