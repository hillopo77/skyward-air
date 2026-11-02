param([switch]$Aboard)
$ErrorActionPreference = 'Stop'
$clarityAirport = Split-Path $PSScriptRoot -Parent
$clarityProject = Join-Path (Split-Path $clarityAirport -Parent) 'SkywardAir\UnrealProject\SkywardAir.uproject'
$clarityEngine = 'C:\Users\zaran\Documents\Codex\UE\Engine\Binaries\Win64\UnrealEditor.exe'
$clarityArgs = @('"'+$clarityProject+'"','/Game/Airport26/L_Airport_Clarity26','-NoSplash','-game','-windowed','-ResX=1920','-ResY=1080','-Airport','-AirportCompact12','-AirportPass=10','-Characters21','-AirportJourney22','-AirportVisual23','-AirportRooms24','-AirportFoyer25','-AirportClarity26')
if ($Aboard) { $clarityArgs += '-AirportStartAboard' }
$clarityArgs += ('-abslog="'+(Join-Path $PSScriptRoot 'ArtBible\AirportPlay26.log')+'"')
Start-Process -FilePath $clarityEngine -ArgumentList $clarityArgs
