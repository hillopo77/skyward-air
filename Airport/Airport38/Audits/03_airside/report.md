# Airside critical review — baseline Clarity37

This is not a finished aircraft stand. The route can be walked in a scripted proof, but its physical construction and future movement logic do not agree. A pass counter does not establish a sealed dock, a coherent service entrance, or a safe aircraft departure envelope.

The review used the root's complete native component/instance inventory, saved layout, source recipes/runtime and genuine captures26–32. No native editor or Blender process was launched by this reviewer, and no project assets were changed.

## Highest-priority defects

1. **The bridge docking throat is incomplete.** The side walls/roof end atx=-3.2, while the last floor reachesx=-2.083. Roughly.695m lies outside the fuselage without a continuous cab enclosure. Rails and a roof/light cross-member protrude into open space. The bellows detail is placed inside the fuselage rather than sealing this gap. Screenshot29 makes the defect unambiguous. The floor having a valid navigation height does not repair its construction.
2. **The service ramp is an orphan from the old gate layout.** Its automatic doors remain atx=-17,y18. Current A07 ends aty10 and A08 is west ofx=-24. Screenshot31 shows the resulting exposed grass-side threshold and leftover fittings. The old suitcase placement05 is still there. The ramp must either be removed or connected to a real controlled staff room; a standalone portal on grass is unacceptable.
3. **Departure has no clearance contract.** The aircraft's complete width is45.336m, and the current safe claim only concerns A08's parked western wall. Forward is-Y. The broad aft wings eventually move toward A07 and the static bridge. No airport-mode retract/stow/departure interlock exists. This is a confirmed missing implementation, not a claim that the current static map has already flown through a wall.
4. **The A07 desk is set into the wall.** Native desk bounds reachy=-3.055; the inside face of the south wall is approximatelyy=-2.91. That is about.145m of overlap. Inventory shows one A07 desk, so this is a placement defect, not evidence of two duplicate desk actors.
5. **Navigation support does not match exterior construction.** The old Compact terminal rectangle extends through areas no longer enclosed by the building. The apron controller declares a flat-3.7m height where the actual ground slopes from0 to-3.7m. The generic Cabin deck fallback also applies at arbitraryx/y near zero feet height. These mismatches need correcting, not hiding with more floor slabs.

## Other verified problems

- The scaled end bridge carpet overlaps its preceding carpet by approximately2.8mm at the same elevation. That is a genuine coplanar overlap. The exact seam's visible flicker was not isolated by this reviewer; it is a rendering hazard that should be removed.
- Tug and dollies have no parking-brake/stowed state. The authored contact material has friction.08 while the service grade has tan(slope)=.1057. Dynamic bodies have no deliberate grade-holding provision. Baseline sampled luggage was stationary, so the report does not falsely claim to have reproduced every reported runaway or jitter instance.

## Coherent correction

The safest layout option is to translate the **whole aircraft and its absolute gameplay data +16m sourceX**, rather than selectively moving wings or narrowing a lounge again. The complete aircraft minimumX would become-6.668m, over7m outside the terminal's current east face. That still does not solve the bridge: author a bent/articulated path and a complete docking cab, with a defined stowed envelope or validated outward pushback before forward taxi. A cab-only withdrawal does not prove that the fixed bridge legs are clear of the swept wing.

Keep the aircraft's unit/axis conversion function unchanged. Translate schema-defined absolute points before configuration, plus native aircraft roots once. Never translate motion deltas, roller shade deltas, local rod endpoints, sizes or facing vectors. Repair the hardcoded aircraft-nearest boundary, StartAboard point and L1 crossing test, and bound the Cabin deck fallback. The current plane18 shade code callsP.vector on both closed position and delta, so a global conversion offset would break it.

The full findings.json contains exact bounds, object IDs, source references, correction requirements and acceptance tests. A native movement sweep, close-up dock inspection, exterior boundary walk and60s parked-vehicle test are required. A route-only screenshot pass is insufficient.
