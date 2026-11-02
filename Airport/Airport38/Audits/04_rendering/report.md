# Rendering and lighting audit 4

The most serious flicker is a construction failure. A08's ceiling and a retained roof cap occupy the same visible plane. The material actually selected changes between frames while the camera and scanner transforms stay still. Increasing detail or changing AA will not cure that. The same collision exists over the café approach.

The scanner is a separate problem. Its strips leave 6 mm bright slits, and the final renderer is much less temporally stable than the project settings suggest. The active session uses native 1080p, TAA8, frame weight0.35 and filter0.8, even though the configuration file advertises TAA16/0.1/filter1 at125%. The bundled Epic implementation explicitly documents the jitter/ghosting tradeoff. The initialization chain keeps changing this profile. One final authority is needed.

The supplied evidence does **not** show a physically shaking scanner. Both scanners had zero transform range and zero velocity in60 samples. Curtain temporal difference averaged0.328/255; the ceiling averaged10.816/255. At ceiling pixel900,300 the sequence switches from RGB48,51,59 to17,21,29 and back. Treating both symptoms as loose-prop physics would be the wrong repair.

Lighting is also governed by historical patches. Some otherwise identical practicals cast shadows merely because their loop index is divisible by5, while earlier generations used3 or4. That is a poor basis for consistent visual grounding. It does not prove that every odd shadow is caused by this setting, but it needs an explicit practical/key/fill design. The northern ceiling fields also read much darker than the welcoming walls, despite the ceiling material itself being middle grey. Preserve warm ambient readability while making those surfaces legible; do not repeat the earlier dark-room failure in pursuit of physical purity.

The validation was too narrow. Zero duplicate actor placements and zero duplicate faces inside individual parts do not catch a roof face coincident with another asset's ceiling. Likewise,93 navigation/interaction assertions cannot establish stable rendering. Add world-space structural plane checks and repeatable stationary/moving image sequences before visual signoff.

The complete findings and acceptance tests are in [findings.json](findings.json): R01 roof conflicts, R02 runtime AA authority, R03 curtain silhouette, R04 shadow roles, R05 ceiling fill, R06 structural/temporal acceptance coverage, R07 stale status reporting. H01 dynamic-light cost and H02 SSR metal-edge instability are explicitly unproven and require controlled measurement rather than assertions.

This was read-only. No model, runtime, native asset or engine session was changed by this reviewer. The review covers the full baseline photographs and current code/inventories; the pickup/belt/throw states were not physically reproduced by the provided static holds.
