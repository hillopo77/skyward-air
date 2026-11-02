param([switch]$Play,[switch]$Validate,[switch]$Capture,[switch]$Aboard,[switch]$Checkin,[switch]$Security,[switch]$Exit)
$ErrorActionPreference = 'Stop'
$airportRoot = $PSScriptRoot
$journeyRoot = Join-Path $airportRoot 'Clarity37'
$airportProject = Join-Path (Split-Path $airportRoot -Parent) 'SkywardAir\UnrealProject\SkywardAir.uproject'
$airportEngine = 'C:\Users\zaran\Documents\Codex\UE\Engine\Binaries\Win64\UnrealEditor.exe'
if (!(Test-Path -LiteralPath $airportEngine)) { throw 'The installed Unreal Editor is required for this editable preview.' }
$airportArgs = @('"'+$airportProject+'"', '/Game/Airport37/L_Airport_Clarity37', '-NoSplash')
$airportWidth = '1920'
$airportHeight = '1080'
if ($Play -or $Validate -or $Capture -or $Aboard -or $Checkin -or $Security -or $Exit) { $airportArgs += @('-game','-windowed',('-ResX='+$airportWidth),('-ResY='+$airportHeight),'-Airport','-AirportCompact12','-AirportPass=10','-Characters21','-AirportJourney22','-AirportVisual23','-AirportRooms24','-AirportFoyer25','-AirportClarity26','-AirportPrototype27','-AirportCheckin30','-AirportArrival31','-AirportWarm33','-AirportFlow35','-AirportDetail36','-AirportClarity37') }
$airportArgs += ('-abslog="'+(Join-Path $journeyRoot 'ArtBible\AirportPlay37.log')+'"')
if ($Checkin) { $airportArgs += '-CheckinPreview31' }
if ($Security) { $airportArgs += '-SecurityPreview35' }
if ($Exit) { $airportArgs += '-Clarity37ExitPreview' }
if ($Aboard) { $airportArgs += '-AirportStartAboard' }
if ($Validate -or $Capture) {
 $airportArgs += @('-RenderOffscreen','-NoSound')
 if ($Validate) { $airportArgs += '-Clarity37QA' }
 if ($Capture) { $airportArgs += '-Clarity37Photos' }
 Start-Process -FilePath $airportEngine -ArgumentList $airportArgs -WindowStyle Hidden
} else {
 Start-Process -FilePath $airportEngine -ArgumentList $airportArgs
}

