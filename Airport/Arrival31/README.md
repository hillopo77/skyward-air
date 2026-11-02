# Check-in arrival31

Run Arrival31.cmd opens the revised check-in entrance. Main Run Airport starts at the original airport entrance. Walk in, turn right to the waiting seats or continue to the queue ahead. Press E at the join marker, wait for both passengers to advance, then visit Desk01. Self-service remains available. WASD move, mouse look, E interact.

The entrance pocket has roughly four metres before the queue, with a clear right-hand approach. The shorter rug and fewer posts keep the process farther inside. One passenger moves to self-service. The entrance objective introduces the room; queue interaction is limited to 2.2 metres. Furniture sizes, two counters, room boundaries and onward corridor are retained.

Signs use simpler graphics and muted bezels. Per-map material instances reduce metal highlights and wood/stone normal detail. Local ceiling fill and bloom are reduced. Calm31 renders native resolution with eight TAA samples, no sharpen, DOF or motion blur. This is a targeted improvement in viewing comfort, not a claim that every viewing issue is resolved.

Airport_Arrival31.blend is the editable source. Native map: /Game/Airport31/L_Airport_Arrival31. SourceAssets/prepare31.py writes layout and graphics; model31.py exports only the two changed geometry families; native31.py imports the changed kit into a separate map. verify31.py performs one focused native walk and captures four raw screenshots. review31.py validates the evidence and generates Review.html. Previous source and map remain available. RecoveryBefore31 preserves changed launcher/runtime files.

ArrivalQA31: 50 passing checks, continuous walking, zero player teleports, 1920×1080 viewport; entrance/right-side access, queue guard, actual passenger advances, check-in, physical baggage acceptance and onward corridor verified. Full airport boarding and sustained frame rate were not retested. Existing character art and local scripted queue are retained. No external generation or paid assets used.
