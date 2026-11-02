# Pass45 lighting repair. Backs the level up, then runs the native fix.
$ErrorActionPreference = 'Stop'
$pass45 = $PSScriptRoot
$airportRoot = Split-Path $pass45 -Parent
$outputs = Split-Path (Split-Path $airportRoot -Parent) -Parent
$project = Join-Path $outputs 'SkywardAir\UnrealProject\SkywardAir.uproject'
$engine = 'C:\Users\zaran\Documents\Codex\UE\Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$umap = Join-Path $outputs 'SkywardAir\UnrealProject\Content\Airport38\L_Airport_Repair38.umap'

if (!(Test-Path -LiteralPath $engine)) { throw 'UnrealEditor-Cmd not found.' }
if (!(Test-Path -LiteralPath $umap)) { throw "Level not found: $umap" }
if (Get-Process -Name 'UnrealEditor*' -ErrorAction SilentlyContinue) {
    throw 'An Unreal process is running. Native sessions must not overlap.'
}

# Backup the level before any mutation. There is no git in this project.
$backupDir = Join-Path $pass45 'Backup'
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$backup = Join-Path $backupDir ("L_Airport_Repair38.$stamp.umap.bak")
Copy-Item -LiteralPath $umap -Destination $backup -Force
Write-Output ("level backed up to " + $backup)
Write-Output ("backup sha256 = " + (Get-FileHash -LiteralPath $backup -Algorithm SHA256).Hash)

$report = Join-Path $pass45 'ImportClosure45.json'
if (Test-Path -LiteralPath $report) { Remove-Item -LiteralPath $report -Force }

$script = Join-Path $pass45 'import_closure45.py'
$fixArgs = @(('"' + $project + '"'), '-run=pythonscript', ('-script="' + $script + '"'),
             '-Unattended', '-NoSplash', '-NoSound', '-NullRHI',
             ('-abslog="' + (Join-Path $pass45 'ImportClosure45.log') + '"'))

$started = Get-Date
$proc = Start-Process -FilePath $engine -ArgumentList $fixArgs -WindowStyle Hidden -PassThru
Write-Output ("fix started pid=" + $proc.Id)
$proc.WaitForExit(1800000) | Out-Null
Write-Output ("process exit code = " + $proc.ExitCode)

if (Test-Path -LiteralPath $report) {
    $d = Get-Content -LiteralPath $report -Raw | ConvertFrom-Json
    Write-Output ("status=" + $d.status + " volumes_found=" + $d.volumes_found + " changed=" + $d.changed.Count)
    if ($d.error) { Write-Output $d.error }
    exit $(if ($d.status -eq 'SUCCESS' -and $proc.ExitCode -eq 0) { 0 } else { 1 })
}
throw 'No report written.'
