param([int]$FromPass=10,[int]$ToPass=10,[switch]$SkipModels)
$airportRoot=$PSScriptRoot
if ($FromPass -ne 10 -or $ToPass -ne 10) { throw 'The current source is revision 11. Use pass 10 as the build stage. The ten historical maps and source backup remain separate.' }
$airportEngineRoot='C:\Users\zaran\Documents\Codex\UE\Engine\Binaries\Win64'
$airportProject=Join-Path (Split-Path $airportRoot -Parent) 'SkywardAir\UnrealProject\SkywardAir.uproject'
if (-not $SkipModels) {
 $airportStarted=Get-Date
 & 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background --factory-startup --python (Join-Path $airportRoot 'SourceAssets\airport_model.py') *> (Join-Path $airportRoot 'ArtBible\RebuildModels.log')
 $airportManifest=Get-Item -LiteralPath (Join-Path $airportRoot 'Exports\airport_assets.json')
 if ($airportManifest.LastWriteTime -lt $airportStarted) { throw 'Model export did not finish. Read ArtBible/RebuildModels.log.' }
}
$env:AIRPORT_BUILD_FROM=[string]$FromPass
$env:AIRPORT_BUILD_TO=[string]$ToPass
$airportScript=Join-Path $airportRoot 'SourceAssets\build_airport_unreal.py'
& (Join-Path $airportEngineRoot 'UnrealEditor-Cmd.exe') $airportProject -run=pythonscript "-script=$airportScript" -unattended -NullRHI -NoSound -NoSplash *> (Join-Path $airportRoot 'ArtBible\RebuildUnreal.log')
$airportReport=Get-Content -LiteralPath (Join-Path $airportRoot 'ArtBible\NativeBuild.json') -Raw | ConvertFrom-Json
if ($airportReport.status -ne 'SUCCESS') { throw 'Native build failed. Read ArtBible/NativeBuild.json and RebuildUnreal.log.' }
Write-Host 'Airport rebuild completed. Run Airport.cmd starts the game.'
