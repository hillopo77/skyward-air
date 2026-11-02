param([switch]$Aboard)
$ErrorActionPreference = 'Stop'
$foyerAirport = Split-Path $PSScriptRoot -Parent
$foyerProject = Join-Path (Split-Path $foyerAirport -Parent) 'SkywardAir\UnrealProject\SkywardAir.uproject'
$foyerEngine = 'C:\Users\zaran\Documents\Codex\UE\Engine\Binaries\Win64\UnrealEditor.exe'
$foyerArgs = @('"'+$foyerProject+'"','/Game/Airport25/L_Airport_Foyer25','-NoSplash','-game','-windowed','-ResX=1600','-ResY=1000','-Airport','-AirportCompact12','-AirportPass=10','-Characters21','-AirportJourney22','-AirportVisual23','-AirportRooms24','-AirportFoyer25')
if ($Aboard) { $foyerArgs += '-AirportStartAboard' }
$foyerArgs += ('-abslog="'+(Join-Path $PSScriptRoot 'ArtBible\AirportPlay25.log')+'"')
Start-Process -FilePath $foyerEngine -ArgumentList $foyerArgs
