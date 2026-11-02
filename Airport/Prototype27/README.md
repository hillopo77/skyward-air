# Entrance room: prototype level 5

The former Clarity26 entrance is retained as prototype1. This revision keeps the check-in-first route and the room's6×10m footprint, while improving modeled construction, graphic readability, PBR finishes and practical lighting. Other airport rooms and character meshes are retained.

Run `Run Prototype5.cmd` or the main airport launcher. WASD moves, mouse looks, E uses the aimed object, Shift runs, B shows the boarding pass. Follow gold to check-in; when checked in, follow blue through screening to GateA07. Boarding reaches the actual parked aircraft.

`Airport_Prototype27.blend` is the editable placed master. Its component library contains eleven families, with continuous lofts, curves and modifiers retained. Original graphics and four original PBR surface sets live in Textures; the Blender images are packed. No purchased or generated third-party assets were added.

Native map: `/Game/Airport27/L_Airport_Prototype5`. Prior intermediate maps2–4 are saved separately for review, with genuine historical progress screenshots under Screenshots/P2, P3 and P4. Final captures are P5. Essential graphics keep their full print textures resident; native1920×1080, short-history TAA,16× anisotropic filtering and distance-faded normal detail are used. Bigger important lettering is the main readability improvement. Tiny decorative text cannot remain legible at unlimited distances.

Build with the installed Blender and Unreal Editor:

1. Run SourceAssets/final_graphics27.py with Python.
2. Run Blender in background with `--python SourceAssets/model27.py` using its absolute path.
3. Run SourceAssets/build_native.py with argument5 using Python.
4. Run SourceAssets/run27.py with `photos 5`, `distance 5`, then `qa 5`, sequentially.
5. Run SourceAssets/review27.py after all evidence passes.

These helpers use the existing local Unreal installation and require the project dependency maps. This is an editable development preview, not a packaged standalone executable. Historical progress screenshots are point-in-time evidence; shared mesh and texture resources can be revised by rebuilding the final assets. The verification covers the route, interactions and distance-render state; it is not a sustained FPS certification or a claim that whole-airport art is finished.

Recovery copies of the prior runtime and launcher are in SourceAssets/RecoveryBefore27. Prior maps and Blender masters remain separate. Do not run multiple heavy engine helpers at once.
