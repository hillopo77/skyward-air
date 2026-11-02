@echo off
"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background "%~dp0Plane.blend" --python-exit-code 1 --python "%~dp0SourceAssets\Blender\export_current.py"
if errorlevel 1 pause
