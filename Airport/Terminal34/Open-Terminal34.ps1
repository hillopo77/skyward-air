param([switch]$Editor,[switch]$Checkin,[switch]$Capture,[switch]$Validate)
$airportLauncher = Join-Path (Split-Path $PSScriptRoot -Parent) 'Open-Airport.ps1'
if ($Editor) { & $airportLauncher }
elseif ($Validate) { & $airportLauncher -Validate }
elseif ($Capture) { & $airportLauncher -Capture }
elseif ($Checkin) { & $airportLauncher -Play -Checkin }
else { & $airportLauncher -Play }
