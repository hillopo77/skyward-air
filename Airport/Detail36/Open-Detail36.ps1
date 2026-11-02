param([switch]$Play,[switch]$Validate,[switch]$Capture,[switch]$Aboard,[switch]$Checkin,[switch]$Security)
& (Join-Path $PSScriptRoot '..\Open-Airport.ps1') @PSBoundParameters
