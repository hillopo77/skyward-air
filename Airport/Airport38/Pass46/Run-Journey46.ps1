# Pass46: run the fresh-route flight journey and compare it to the baseline.
#
# This is the regression that matters for P46-015: the journey walks the pawn
# through security and check-in for real, with collision, and waits for the
# scanned bag to reach scanned_bags. A jammed bag or a blocked lane shows up
# here as a failed check, not as a warning.
#
# The baseline to beat is 166 of 167 passing with the single known failure
# being the P46-011 bag interlock, which is non-deterministic across runs.
param([string]$Label = 'run')
$ErrorActionPreference = 'Stop'
$pass46 = $PSScriptRoot
$airportRoot = Split-Path $pass46 -Parent
$outputs = Split-Path (Split-Path $airportRoot -Parent) -Parent
$project = Join-Path $outputs 'SkywardAir\UnrealProject\SkywardAir.uproject'
$engine = 'C:\Users\zaran\Documents\Codex\UE\Engine\Binaries\Win64\UnrealEditor.exe'
$report = Join-Path $airportRoot 'ArtBible\FlightJourney39.json'

if (!(Test-Path -LiteralPath $engine)) { throw 'Unreal Editor not found.' }
if (Get-Process -Name 'UnrealEditor*' -ErrorAction SilentlyContinue) {
    throw 'An Unreal process is already running. Close it first; native sessions must not overlap.'
}

$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
if (Test-Path -LiteralPath $report) { Remove-Item -LiteralPath $report -Force }

$log = Join-Path $pass46 ('Journey46-' + $Label + '-' + $stamp + '.log')
$gameArgs = @(('"' + $project + '"'), '/Game/Airport38/L_Airport_Repair38', '-NoSplash',
              '-game', '-windowed', '-ResX=1280', '-ResY=720',
              '-Airport', '-AirportCompact12', '-AirportPass=10', '-Characters21',
              '-AirportJourney22', '-AirportClarity26', '-AirportRepair38',
              '-Repair39Flight', '-RenderOffscreen', '-NoSound',
              ('-abslog="' + $log + '"'))

$proc = Start-Process -FilePath $engine -ArgumentList $gameArgs -WindowStyle Hidden -PassThru
Write-Output ('journey "' + $Label + '" started pid=' + $proc.Id)

# The journey writes its report continuously and finishes on its own; the game
# process stays up afterwards, so wait for a settled report rather than exit.
$deadline = (Get-Date).AddMinutes(20)
$done = $false
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 10
    if (Test-Path -LiteralPath $report) {
        try {
            $d = Get-Content -LiteralPath $report -Raw | ConvertFrom-Json
            # The journey truncates and rewrites its report on every check; an
            # empty read parses to $null, and $null -ne 'RUNNING' is true. That
            # once killed a healthy run mid-flight. Require a real end state.
            if ($d -and $d.status -and $d.status -ne 'RUNNING') { $done = $true; break }
        } catch { }
    }
    if ($proc.HasExited) { break }
}
if (!$proc.HasExited) { Stop-Process -Id $proc.Id -Force }
Start-Sleep -Seconds 2

if (!$done) { throw 'The journey wrote no finished report inside 20 minutes.' }
$d = Get-Content -LiteralPath $report -Raw | ConvertFrom-Json
$kept = Join-Path $pass46 ('Backup\FlightJourney39_' + $Label + '_' + $stamp + '.json')
Copy-Item -LiteralPath $report -Destination $kept -Force

$passed = ($d.checks | Where-Object { $_.passed }).Count
$total = $d.checks.Count
Write-Output ('status=' + $d.status + '  checks=' + $passed + '/' + $total +
              '  elapsed=' + [math]::Round($d.elapsed_s, 1) + 's')
Write-Output ('journey flags: checked_in=' + $d.journey.checked_in +
              ' bag_accepted=' + $d.journey.bag_accepted +
              ' security=' + $d.journey.security +
              ' boarding=' + $d.journey.boarding +
              ' aboard=' + $d.journey.aboard)
if ($d.error) { Write-Output ('error: ' + $d.error) }
foreach ($q in ($d.checks | Where-Object { -not $_.passed })) {
    Write-Output ('  FAILED  ' + $q.name)
    if ($q.obstacles) {
        foreach ($o in $q.obstacles) {
            if ($o.blocked) { Write-Output ('            blocked at z=' + $o.height + ' by ' + $o.actor + ' / ' + $o.component) }
        }
    }
}
Write-Output ('report kept at ' + $kept)
exit 0
