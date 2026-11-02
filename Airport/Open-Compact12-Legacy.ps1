param([switch]$Play,[switch]$Validate,[switch]$Capture,[switch]$Aboard)
$airportRoot=$PSScriptRoot
$airportCompact=Join-Path $airportRoot 'Compact12'
$airportProject=Join-Path (Split-Path $airportRoot -Parent) 'SkywardAir\UnrealProject\SkywardAir.uproject'
$airportEngine='C:\Users\zaran\Documents\Codex\UE\Engine\Binaries\Win64\UnrealEditor.exe'
if (-not (Test-Path -LiteralPath $airportEngine)) { throw 'UnrealEditor.exe is required for this editable preview.' }
$airportArgs=@('"'+$airportProject+'"','/Game/Airport12/L_Airport_Compact12','-NoSplash')
if ($Play -or $Validate -or $Capture -or $Aboard) { $airportArgs+=@('-game','-windowed','-ResX=1600','-ResY=1000','-Airport','-AirportCompact12','-AirportPass=10') }
$airportArgs+=('-abslog="'+(Join-Path $airportCompact 'ArtBible\AirportPlay12.log')+'"')
if ($Aboard) { $airportArgs+='-AirportStartAboard' }
if ($Validate) { $airportArgs+=@('-AirportQA','-RenderOffscreen','-NoSound') }
if ($Capture) { $airportArgs+=@('-AirportCapture','-RenderOffscreen','-NoSound',('-AirportShotSet='+(Join-Path $airportCompact 'SourceAssets\CaptureViews12.json'))) }
Start-Process -FilePath $airportEngine -ArgumentList $airportArgs -WindowStyle Hidden
