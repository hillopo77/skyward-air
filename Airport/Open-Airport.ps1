param([switch]$Play,[switch]$Editor,[switch]$Validate,[switch]$Capture,[switch]$Performance,[switch]$Aboard,[switch]$Checkin,[switch]$Security,[switch]$Exit)
$ErrorActionPreference = 'Stop'
if ($Checkin -or $Security -or $Exit) {
    & (Join-Path $PSScriptRoot 'Open-Airport37.ps1') -Play:$Play -Validate:$Validate -Capture:$Capture -Aboard:$Aboard -Checkin:$Checkin -Security:$Security -Exit:$Exit
} else {
    & (Join-Path $PSScriptRoot 'Airport38\Open-Airport38.ps1') -Play:$Play -Editor:$Editor -Validate:$Validate -Capture:$Capture -Performance:$Performance -Aboard:$Aboard
}
