param([switch]$Editor,[switch]$Security,[switch]$Validate,[switch]$Capture)
$airportLauncher = Join-Path (Split-Path $PSScriptRoot -Parent) 'Open-Airport.ps1'
if ($Editor) { & $airportLauncher }
elseif ($Validate) { & $airportLauncher -Validate }
elseif ($Capture) { & $airportLauncher -Capture }
elseif ($Security) { & $airportLauncher -Play -Security }
else { & $airportLauncher -Play }
