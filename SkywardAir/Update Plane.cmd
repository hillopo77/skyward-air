@echo off
"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background "%~dp0Plane.blend" --python-exit-code 1 --python "%~dp0SourceAssets\Blender\export_current.py"
if errorlevel 1 (
  pause
  exit /b 1
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Rebuild-Unreal.ps1"
if errorlevel 1 pause
