# Aircraft revision07 — confirmed cabin changes and exterior start

The user explicitly confirmed the main galley between business and economy, business chairs only beside the windows with a clear centre, and a 10% larger structural shell/clearance envelope with fittings kept at their individual size. The unclear spoken door-count fragment was not interpreted as a request for eleven or twelve doors.

The current aircraft has four grey business seats (rows 01–02, A/K), 24 economy seats (rows 03–08, A/D/E/K), two dedicated pilot seats, both lavatory suites, forward crew/galley areas and a central galley at source Y=6.435m. The curtain divider is at Y=7.55m. Economy pitch is 1.22m. Business has an open centre approximately 2.70m wide.

Carpet is a continuous five-zone fitted surface with global UVs, low-contrast wool texture and flush service-zone transitions. Old transverse floor-bay strips have been removed. The economy aisle guides share one uninterrupted alignment. Seats/fixtures are positioned as coherent assemblies rather than individually stretched.

Each economy seatback has a modeled display/bezel, static original screen artwork, headphone/USB-C panel and stowed tray with a retained hinge/latch. Four bulkhead displays serve the first economy row. Each business chair has its own console-mounted articulated display. The entertainment interface is visual artwork only; media or touch operation is not implemented.

Passenger/service doors 1L/1R/2L/2R have through viewports, seals, operating hardware, arming housings, girt bar fittings and slide pack bustles. Their dimensions were informed by Boeing D6-58328 Rev K §2.7. The doors are art interpretations and do not simulate the 767's lift/stow path. The cockpit door starts closed and uses E to animate about its actual hinge. Source-instance label parenting keeps its native labels attached to the moving leaf.

The uncooked game startup provides E to sit in either pilot seat or any business chair, and E again to stand. Sitting saves the standing position, pauses translation, temporarily disables pawn collision/plane constraint and sets the seated eye position. Standing restores these settings. The script is deliberately described as an editor-hosted prototype rather than packaged gameplay.

The clarity profile is 1600×900, 125% internal resolution, 16-sample temporal AA, film grain/chromatic aberration/motion blur disabled and reduced fine normal strength. Actual screenshots use the regular standalone viewport capture after temporal AA settles; they are not high-resolution capture resets.

Exterior work replaces the uneven prior skin with continuous flush window-bearing panels, a fitted canopy and nose, a tapered tail cone and clipped blue/gold paint boundaries. New airfoil wings, flap seams/canoe fairings and tip lamps are modeled. Hollow larger engines have rolled inlet lips, acoustic/intake geometry, 60 curved solid fan blades, conical spinners, service joints/latches, exhaust lips and formed pylons. Exterior silhouette, transitions, gear bays, control-surface construction and finer surfacing still need substantial further work. The current playable compact airframe is not an exact 767.

Reference: https://www.boeing.com/content/dam/boeing/v2/airports/acaps/767_REV_K.pdf
Slide pack / arming hardware reference: https://downloads.regulations.gov/FAA-2011-0719-0005/attachment_1.pdf

Validation evidence is in Layout07Checks.json (19 layout/source checks), InteriorGeometryChecks.json (26 retained physical construction checks), EngineValidation.json (actual standalone captures and actions/movement), and UnrealBuildReport.json (native import and map reload). The static E-action tests call the same use_nearest() function as live key polling; they do not claim a manually injected keyboard event. No final visual approval or measured frame-rate claim is made.
