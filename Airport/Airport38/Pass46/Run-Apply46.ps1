# Pass46: apply the validated improvement spec to the level.
#
# Runs the script standalone under -run=pythonscript, which is the mode Pass45's
# import step used and the only one that gives a real EditorActorSubsystem. The
# game dispatch cannot do this: in -game mode the subsystem is None.
#
# This MUTATES the saved level, so it backs the .umap up first and refuses to
# start while any Unreal process is alive. There is no git anywhere in this
# project; the backup in Pass46\Backup is the only way back.
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

# Refuse to run against a spec that has not passed the offline validator.
Push-Location $pass46
try {
    & python -I validate_spec46.py
    if ($LASTEXITCODE -ne 0) { throw 'Spec46 failed offline validation; not applying it.' }
} finally { Pop-Location }

$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$backup = Join-Path $pass46 ('Backup\L_Airport_Repair38.' + $stamp + '.umap.bak')
Copy-Item -LiteralPath $umap -Destination $backup -Force
Write-Output ("level backed up to " + $backup)
Write-Output ("backup sha256 = " + (Get-FileHash -LiteralPath $backup -Algorithm SHA256).Hash)

$report = Join-Path $pass46 'Apply46.json'
if (Test-Path -LiteralPath $report) { Remove-Item -LiteralPath $report -Force }

$script = Join-Path $pass46 'apply46_probe.py'
$fixArgs = @(('"' + $project + '"'), '-run=pythonscript', ('-script="' + $script + '"'),
             '-Unattended', '-NoSplash', '-NoSound', '-NullRHI',
             ('-abslog="' + (Join-Path $pass46 'Apply46.log') + '"'))

$started = Get-Date
$proc = Start-Process -FilePath $engine -ArgumentList $fixArgs -WindowStyle Hidden -PassThru
Write-Output ("apply started pid=" + $proc.Id)
$proc.WaitForExit(1800000) | Out-Null
Write-Output ("process exit code = " + $proc.ExitCode)

if (Test-Path -LiteralPath $report) {
    $d = Get-Content -LiteralPath $report -Raw | ConvertFrom-Json
    Write-Output ("status=" + $d.status +
                  " placed=" + $d.placed.Count +
                  " moved=" + $d.moved.Count +
                  " varied=" + $d.varied.Count +
                  " collided=" + $d.collided.Count +
                  " rejected=" + $d.rejected.Count)
    if ($d.error) { Write-Output $d.error }
    exit $(if ($d.status -eq 'SUCCESS' -and $proc.ExitCode -eq 0) { 0 } else { 1 })
}
throw 'No report written.'
