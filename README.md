# Skyward Air

A first-person airport-and-airliner sandbox in Unreal Engine 5.8: walk the terminal, check in, go through
security, board, sit in the cockpit and fly, and mess with everything on the way (grab, throw and equip
props on a springy tether; people react). The level, its lighting and most of its art are built by scripts
in this repo (Blender for meshes, Unreal Python for the level), and the game logic runs on the editor's Python.

## Play exactly this build

1. Install **Unreal Engine 5.8** (Epic Games Launcher).
2. Clone this repo.
3. From the [latest Release](../../releases/latest), download every `SkywardAir-Content-part*.zip` and extract
   them all into `SkywardAir/UnrealProject/`, so you end up with `SkywardAir/UnrealProject/Content/...` beside
   `SkywardAir.uproject`.
4. Run `Airport/Run Airport.cmd` (Windows). If Unreal is not in the standard place, set the `UNREAL_EDITOR`
   environment variable to its `UnrealEditor.exe` first. The first start compiles shaders and takes a while.

It must run through the editor (`UnrealEditor.exe ... -game`): the gameplay is Python, which a packaged
build does not include.

## Where things are

| Path | What |
| --- | --- |
| `SkywardAir/UnrealProject/Content/Python/` | the game at runtime: `airport_runtime.py` (main loop), `gameplay66.py` (movement, tether, equip, HUD), `cabin68.py` (cabin light and the panic line), `airport_flight39.py` (flight), `skyward_runtime.py` (interactive controls) |
| `Airport/Airport38/` | the current level's build pipeline; `Open-Airport38.ps1` launches it |
| `Airport/Airport38/Pass51/` | recent passes: Blender kits (`*_blender.py`), level edits (`*_editor.py`), the step queue (`Queue66.ps1`), and the change log `MAKEOVER51.md` |
| `Airport/Airport38/Pass48/` | in-game probes (`*_probe.py`) that measure the level, the mesh helpers (`mesh48.py`) and the importer |
| `Airport/Airport38/Pass50/` | `Check50.ps1` (run an editor script, or capture camera views to PNG) and `Views50.json` |
| `Airport/Airport38/Pass51/Slider71/` | before/after photos of the latest pass |

## Working on it with Claude

Read `Airport/Airport38/Pass51/MAKEOVER51.md` first: it records every pass, what was measured in the game,
and the traps found on the way (for example: never swap material slots on interactive controls, and editor
scripts must `modify()` actors and `save_map()`). Changes follow one loop: build in Blender headless, apply
with an editor script (`Check50.ps1 -Editor ... -Mutates`, which backs the level up first), then photograph
in the game (`Check50.ps1 -Views ...`) and run the journey test (`Queue66.ps1 -Steps journey`).
