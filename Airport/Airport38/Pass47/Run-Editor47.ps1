# Pass47: run one standalone editor script (-run=pythonscript -NullRHI).
#
# Usage: Run-Editor47.ps1 -Script inspect47_editor.py [-Mutates]
# With -Mutates the level is backed up with a hash first; without it the
# script is expected to be read-only. Refuses to overlap another Unreal session.
param([Parameter(Mandatory = $true)][string]$Script, [switch]$Mutates)
$ErrorActionPreference = 'Stop'
$here = $PSScriptRoot
$outputs = Split-Path (Split-Path (Split-Path $here -Parent) -Parent) -Parent
$project = Join-Path $outputs 'SkywardAir\UnrealProject\SkywardAir.uproject'
$umap = Join-Path $outputs 'SkywardAir\UnrealProject\Content\Airport38\L_Airport_Repair38.umap'
$engine = 'C:\Users\zaran\Documents\Codex\UE\Engine\Binaries\Win64\UnrealEditor.exe'
if (Get-Process -Name 'UnrealEditor*' -ErrorAction SilentlyContinue) {
    throw 'An Unreal process is already running. Close it first; native sessions must not overlap.'
}
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
if ($Mutates) {
    $backup = Join-Path $here ('Backup\L_Airport_Repair38.' + $stamp + '.umap.bak')
    Copy-Item -LiteralPath $umap -Destination $backup -Force
    Write-Output ('level backed up to ' + $backup)
    Write-Output ('backup sha256 = ' + (Get-FileHash -LiteralPath $backup -Algorithm SHA256).Hash)
}
$log = Join-Path $here (([IO.Path]::GetFileNameWithoutExtension($Script)) + '-' + $stamp + '.log')
$args47 = @(('"' + $project + '"'), '-run=pythonscript', ('-script="' + (Join-Path $here $Script) + '"'),
            '-Unattended', '-NoSplash', '-NoSound', '-NullRHI', ('-abslog="' + $log + '"'))
$proc = Start-Process -FilePath $engine -ArgumentList $args47 -WindowStyle Hidden -PassThru
$proc.WaitForExit(1800000) | Out-Null
Write-Output ($Script + ' exit code = ' + $proc.ExitCode)
