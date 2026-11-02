param([switch]$Aboard)
$ErrorActionPreference = 'Stop'
$visualAirport = Split-Path $PSScriptRoot -Parent
$visualProject = Join-Path (Split-Path $visualAirport -Parent) 'SkywardAir\UnrealProject\SkywardAir.uproject'
$visualEngine = 'C:\Users\zaran\Documents\Codex\UE\Engine\Binaries\Win64\UnrealEditor.exe'
$visualArgs = @('"'+$visualProject+'"','/Game/Airport23/L_Airport_Visual23','-NoSplash','-game','-windowed','-ResX=1600','-ResY=1000','-Airport','-AirportCompact12','-AirportPass=10','-Characters21','-AirportJourney22','-AirportVisual23')
if ($Aboard) { $visualArgs += '-AirportStartAboard' }
$visualArgs += ('-abslog="'+(Join-Path $PSScriptRoot 'ArtBible\AirportPlay23.log')+'"')
Start-Process -FilePath $visualEngine -ArgumentList $visualArgs
