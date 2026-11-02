# Pass46 / P46-015: enable collision on the security and queue furniture.
#
# Takes a group: A is the six queue posts and four stanchions, B is the two
# X-ray scanners. They are kept apart so that each gets its own journey run and
# a failure points at one change rather than twelve.
#
# Runs standalone under -run=pythonscript, the only mode with a real
# EditorActorSubsystem. This MUTATES the saved level, so it backs the .umap up
# first and refuses to start while any Unreal process is alive. There is no git
# anywhere in this project; the backup in Pass46\Backup is the only way back.
param([Parameter(Mandatory = $true)][ValidateSet('A', 'B', 'C')][string]$Group)
$ErrorActionPreference = 'Stop'
$pass46 = $PSScriptRoot
$airportRoot = Split-Path $pass46 -Parent
$outputs = Split-Path (Split-Path $airportRoot -Parent) -Parent
$project = Join-Path $outputs 'SkywardAir\UnrealProject\SkywardAir.uproject'
$umap = Join-Path $outputs 'SkywardAir\UnrealProject\Content\Airport38\L_Airport_Repair38.umap'
$engine = 'C:\Users\zaran\Documents\Codex\UE\Engine\Binaries\Win64\UnrealEditor.exe'

if (!(Test-Path -LiteralPath $engine)) { throw 'Unreal Editor not found.' }
if (!(Test-Path -LiteralPath $project)) { throw 'SkywardAir project not found.' }
if (!(Test-Path -LiteralPath $umap)) { throw 'Level not found.' }
if (Get-Process -Name 'UnrealEditor*' -ErrorAction SilentlyContinue) {
    throw 'An Unreal process is already running. Close it first; native sessions must not overlap.'
}

# Refuse to run unless the offline clearance analysis still passes, so a change
# to the route or to the furniture cannot slip through unchecked.
Push-Location $pass46
try {
    & python -I clearance46.py | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw 'clearance46.py reports an in-scope item that would block the pawn; not changing collision.'
    }
} finally { Pop-Location }

$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$backup = Join-Path $pass46 ('Backup\L_Airport_Repair38.' + $stamp + '.umap.bak')
Copy-Item -LiteralPath $umap -Destination $backup -Force
Write-Output ('level backed up to ' + $backup)
Write-Output ('backup sha256 = ' + (Get-FileHash -LiteralPath $backup -Algorithm SHA256).Hash)

# ascii, not utf8: Windows PowerShell's utf8 writes a BOM the probe would read
# as part of the group name.
Set-Content -LiteralPath (Join-Path $pass46 'Collide46Group.txt') -Value $Group -Encoding ascii

$report = Join-Path $pass46 'Collide46.json'
if (Test-Path -LiteralPath $report) {
    Move-Item -LiteralPath $report -Destination (Join-Path $pass46 ('Collide46.' + $stamp + '.json')) -Force
}

$script = Join-Path $pass46 'collide46_probe.py'
$log = Join-Path $pass46 ('Collide46-' + $Group + '.log')
$fixArgs = @(('"' + $project + '"'), '-run=pythonscript', ('-script="' + $script + '"'),
             '-Unattended', '-NoSplash', '-NoSound', '-NullRHI',
             ('-abslog="' + $log + '"'))

$proc = Start-Process -FilePath $engine -ArgumentList $fixArgs -WindowStyle Hidden -PassThru
Write-Output ('collide group ' + $Group + ' started pid=' + $proc.Id)
$proc.WaitForExit(1800000) | Out-Null
Write-Output ('process exit code = ' + $proc.ExitCode)

if (Test-Path -LiteralPath $report) {
    $d = Get-Content -LiteralPath $report -Raw | ConvertFrom-Json
    Write-Output ('status=' + $d.status +
                  ' changed=' + $d.changed.Count +
                  ' unchanged=' + $d.unchanged.Count +
                  ' rejected=' + $d.rejected.Count)
    foreach ($q in $d.changed) {
        Write-Output ('  changed   ' + $q.actor + '  ' + $q.mesh +
                      '  ' + ($q.was.enabled -replace '.*CollisionEnabled\.', '' -replace ':.*', '') +
                      ' -> ' + ($q.now.enabled -replace '.*CollisionEnabled\.', '' -replace ':.*', '') +
                      ' / ' + $q.now.profile + '  actor collision ' + $q.was.actor_collision + ' -> ' + $q.now.actor_collision + '  top=' + $q.top_m + ' m')
    }
    foreach ($q in $d.unchanged) { Write-Output ('  unchanged ' + $q.actor + '  ' + $q.reason) }
    foreach ($q in $d.rejected) { Write-Output ('  rejected  ' + $q.actor + '  ' + $q.reason) }
    Write-Output '  not verified here: no physics query answers in this mode. Run Run-Verify46.ps1.'
    if ($d.error) { Write-Output $d.error }
    exit $(if ($d.status -eq 'SUCCESS' -and $proc.ExitCode -eq 0) { 0 } else { 1 })
}
throw 'No report written.'
