# Pass46 / P46-011: move the security greeter out of the walk lane.
#
# MUTATES the saved level: backs the .umap up with a hash first and refuses to
# start while any Unreal process is alive. There is no git in this project.
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


$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$backup = Join-Path $pass46 ('Backup\L_Airport_Repair38.' + $stamp + '.umap.bak')
Copy-Item -LiteralPath $umap -Destination $backup -Force
Write-Output ('level backed up to ' + $backup)
Write-Output ('backup sha256 = ' + (Get-FileHash -LiteralPath $backup -Algorithm SHA256).Hash)


$report = Join-Path $pass46 'Npc46.json'
if (Test-Path -LiteralPath $report) {
    Move-Item -LiteralPath $report -Destination (Join-Path $pass46 ('Npc46.' + $stamp + '.json')) -Force
}

$script = Join-Path $pass46 'npc46_probe.py'
$log = Join-Path $pass46 ('Npc46-' + $stamp + '.log')
$fixArgs = @(('"' + $project + '"'), '-run=pythonscript', ('-script="' + $script + '"'),
             '-Unattended', '-NoSplash', '-NoSound', '-NullRHI',
             ('-abslog="' + $log + '"'))

$proc = Start-Process -FilePath $engine -ArgumentList $fixArgs -WindowStyle Hidden -PassThru
Write-Output ('npc move started pid=' + $proc.Id)
$proc.WaitForExit(1800000) | Out-Null
Write-Output ('process exit code = ' + $proc.ExitCode)

if (Test-Path -LiteralPath $report) {
    $d = Get-Content -LiteralPath $report -Raw | ConvertFrom-Json
    Write-Output ('status=' + $d.status)
    foreach ($q in $d.moved) { Write-Output ('  ' + $q.actor + '  ' + ($q.before.location -join ',') + ' yaw ' + $q.before.yaw + '  ->  ' + ($q.after.location -join ',') + ' yaw ' + $q.after.yaw) }
    if ($d.error) { Write-Output $d.error }
    exit $(if ($d.status -eq 'SUCCESS' -and $proc.ExitCode -eq 0) { 0 } else { 1 })
}
throw 'No report written.'
