# Pass46 / P46-015: measure which items actually block, in -game.
#
# Read-only. It runs in -game rather than -run=pythonscript because no physics
# query answers in that mode - a control trace onto the check-in hall floor,
# which is certainly solid, comes back empty there. Traces only answer in the
# running game, which is also the mode the journey traces in.
#
# Run this BEFORE changing any collision. P46-014 changed ten plants on the
# belief that their collision was off; they were already QUERY_AND_PHYSICS and
# the change was a no-op. The premise had never been measured.
$ErrorActionPreference = 'Stop'
$pass46 = $PSScriptRoot
$airportRoot = Split-Path $pass46 -Parent
$outputs = Split-Path (Split-Path $airportRoot -Parent) -Parent
$project = Join-Path $outputs 'SkywardAir\UnrealProject\SkywardAir.uproject'
$pythonDir = Join-Path $outputs 'SkywardAir\UnrealProject\Content\Python'
$engine = 'C:\Users\zaran\Documents\Codex\UE\Engine\Binaries\Win64\UnrealEditor.exe'

if (!(Test-Path -LiteralPath $engine)) { throw 'Unreal Editor not found.' }
if (!(Test-Path -LiteralPath $project)) { throw 'SkywardAir project not found.' }
if (!(Test-Path -LiteralPath $pythonDir)) { throw 'Project Python folder not found.' }
if (Get-Process -Name 'UnrealEditor*' -ErrorAction SilentlyContinue) {
    throw 'An Unreal process is already running. Close it first; native sessions must not overlap.'
}

# The probe and the dispatch that reaches it must both be installed, or the
# flag is accepted and silently does nothing.
Copy-Item -LiteralPath (Join-Path $pass46 'verify46_probe.py') -Destination $pythonDir -Force
Copy-Item -LiteralPath (Join-Path $airportRoot 'SourceAssets\airport_repair38.py') -Destination $pythonDir -Force
Write-Output 'installed verify46_probe.py and the dispatch'

$report = Join-Path $pass46 'Verify46.json'
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
if (Test-Path -LiteralPath $report) {
    Move-Item -LiteralPath $report -Destination (Join-Path $pass46 ('Verify46.' + $stamp + '.json')) -Force
}

$log = Join-Path $pass46 ('Collide46Verify-' + $stamp + '.log')
$gameArgs = @(('"' + $project + '"'), '/Game/Airport38/L_Airport_Repair38', '-NoSplash',
              '-game', '-windowed', '-ResX=1280', '-ResY=720',
              '-Airport', '-AirportCompact12', '-AirportPass=10', '-Characters21',
              '-AirportJourney22', '-AirportClarity26', '-AirportRepair38',
              '-Collide46Verify', '-RenderOffscreen', '-NoSound',
              ('-abslog="' + $log + '"'))

$proc = Start-Process -FilePath $engine -ArgumentList $gameArgs -WindowStyle Hidden -PassThru
Write-Output ('verify started pid=' + $proc.Id)

# The probe writes its report and then stops ticking; the game keeps running,
# so wait for a finished report rather than for the process to exit.
$deadline = (Get-Date).AddMinutes(8)
$done = $false
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 5
    if (Test-Path -LiteralPath $report) {
        try {
            $d = Get-Content -LiteralPath $report -Raw | ConvertFrom-Json
            # An empty read mid-rewrite parses to $null; require a real end state.
            if ($d -and $d.status -and $d.status -ne 'RUNNING') { $done = $true; break }
        } catch { }
    }
    if ($proc.HasExited) { break }
}
if (!$proc.HasExited) { Stop-Process -Id $proc.Id -Force }
Start-Sleep -Seconds 2

if (!$done) { throw 'Verify46 wrote no finished report.' }
$d = Get-Content -LiteralPath $report -Raw | ConvertFrom-Json
Write-Output ('status=' + $d.status)
Write-Output ('control: floor=' + $d.control.floor_below_checkin +
              ' wall=' + $d.control.wall_to_the_west +
              ' passed=' + $d.control.passed)
if ($d.status -ne 'SUCCESS') { if ($d.error) { Write-Output $d.error }; exit 1 }

Write-Output ''
Write-Output ('{0,-26} {1,-16} {2,-18} {3,-6} {4,-6} {5}' -f 'actor', 'kind', 'collision', 'solid', 'concl', 'reached from / blocked by')
foreach ($q in $d.solidity) {
    $detail = if ($q.reached_from.Count) { ($q.reached_from -join ', ') } else { $q.note }
    Write-Output ('{0,-26} {1,-16} {2,-18} {3,-6} {4,-6} {5}' -f $q.actor, $q.kind,
                  ($q.collision_enabled -replace '.*CollisionEnabled\.', '' -replace ':.*', ''),
                  $q.solid, $q.conclusive, $detail)
}
Write-Output ''
foreach ($q in $d.tunnels) {
    Write-Output ('tunnel ' + $q.actor + ': open=' + $q.open + ' hit=' + $q.hit_along_bag_path + ' -- ' + $q.means)
}
if ($d.missing.Count) { Write-Output ('not in the level: ' + ($d.missing -join ', ')) }
$solid = ($d.solidity | Where-Object { $_.solid }).Count
Write-Output ''
Write-Output ("actually solid: $solid of " + $d.solidity.Count)
exit 0
