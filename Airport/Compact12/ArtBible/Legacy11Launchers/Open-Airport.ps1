param([switch]$Play,[switch]$Validate,[switch]$Capture)
$airportRoot = $PSScriptRoot
$airportProject = Join-Path (Split-Path $airportRoot -Parent) 'SkywardAir\UnrealProject\SkywardAir.uproject'
$airportEngine = 'C:\Users\zaran\Documents\Codex\UE\Engine\Binaries\Win64\UnrealEditor.exe'
if (-not (Test-Path -LiteralPath $airportEngine)) { throw 'Set $airportEngine to your installed UnrealEditor.exe.' }
$airportArgs = @('"'+$airportProject+'"','/Game/Airport10/L_Airport_Revision11','-NoSplash')
if ($Play -or $Validate -or $Capture) { $airportArgs += @('-game','-windowed','-ResX=1600','-ResY=1000','-Airport','-AirportPass=10') }
$airportArgs += ('-abslog="'+(Join-Path $airportRoot 'ArtBible\AirportPlay11.log')+'"')
if ($Validate) { $airportArgs += @('-AirportQA','-RenderOffscreen','-NoSound') }
if ($Capture) { $airportArgs += @('-AirportCapture','-RenderOffscreen','-NoSound') }
Start-Process -FilePath $airportEngine -ArgumentList $airportArgs -WindowStyle $(if ($Validate -or $Capture) {'Hidden'} else {'Normal'})
