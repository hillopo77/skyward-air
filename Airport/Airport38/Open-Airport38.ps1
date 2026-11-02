param([switch]$Play,[switch]$Editor,[switch]$Aboard,[switch]$Validate,[switch]$Capture,[switch]$Performance)
$ErrorActionPreference = 'Stop'
$airportRoot = $PSScriptRoot
$airportProject = Join-Path (Split-Path (Split-Path $airportRoot -Parent) -Parent) 'SkywardAir\UnrealProject\SkywardAir.uproject'
# The editor: $env:UNREAL_EDITOR if set, else this machine's build, else a standard Epic Games UE 5.8 install
$airportEngine = @($env:UNREAL_EDITOR, 'C:\Users\zaran\Documents\Codex\UE\Engine\Binaries\Win64\UnrealEditor.exe',
                   'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe') |
    Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
if (!$airportEngine) { throw 'Unreal Editor 5.8 is required: install it, or set UNREAL_EDITOR to its UnrealEditor.exe.' }
if (!(Test-Path -LiteralPath $airportProject)) { throw 'SkywardAir project is missing beside the Airport output folder.' }
$airportArgs = @(('"'+$airportProject+'"'), '/Game/Airport38/L_Airport_Repair38', '-NoSplash')
if (!$Editor) {
 $airportArgs += @('-game','-windowed','-ResX=1920','-ResY=1080','-Airport','-AirportCompact12','-AirportPass=10','-Characters21','-AirportJourney22','-AirportClarity26','-AirportRepair38')
}
if ($Aboard) { $airportArgs += '-AirportStartAboard' }
if ($Validate) { $airportArgs += '-Repair39Flight' }
if ($Capture) { $airportArgs += '-Repair38Photos' }
if ($Performance) { $airportArgs += '-Repair39Performance' }
$airportArgs += ('-abslog="'+(Join-Path $airportRoot 'ArtBible\AirportPlay39.log')+'"')
if ($Validate -or $Capture -or $Performance) {
 $airportArgs += @('-RenderOffscreen','-NoSound')
 Start-Process -FilePath $airportEngine -ArgumentList $airportArgs -WindowStyle Hidden
} else {
 Start-Process -FilePath $airportEngine -ArgumentList $airportArgs
}
