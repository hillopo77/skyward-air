param([switch]$Aboard)
$ErrorActionPreference = 'Stop'
$roomsAirport = Split-Path $PSScriptRoot -Parent
$roomsProject = Join-Path (Split-Path $roomsAirport -Parent) 'SkywardAir\UnrealProject\SkywardAir.uproject'
$roomsEngine = 'C:\Users\zaran\Documents\Codex\UE\Engine\Binaries\Win64\UnrealEditor.exe'
$roomsArgs = @('"'+$roomsProject+'"','/Game/Airport24/L_Airport_Rooms24','-NoSplash','-game','-windowed','-ResX=1600','-ResY=1000','-Airport','-AirportCompact12','-AirportPass=10','-Characters21','-AirportJourney22','-AirportVisual23','-AirportRooms24')
if ($Aboard) { $roomsArgs += '-AirportStartAboard' }
$roomsArgs += ('-abslog="'+(Join-Path $PSScriptRoot 'ArtBible\AirportPlay24.log')+'"')
Start-Process -FilePath $roomsEngine -ArgumentList $roomsArgs
