# Pass50: one-shot change-and-look. Runs editor scripts, then photographs the
# chosen views in the running game, then makes a contact sheet, in one go.
#
# Usage:
#   Check50.ps1 -Editor Pass50\lumen50_editor.py -Mutates -Views Z03_checkin_in,X1_forecourt_arrival -Out Pass50\Look\A
#   Check50.ps1 -Views all -Out Pass50\Sweep        (no editor step)
# Editor scripts run one after another (-run=pythonscript -NullRHI); with
# -Mutates the level is backed up once first. Views come from
# Pass48\AllViews51.json ('all' for every one) plus any in Pass50\Views50.json.
# Never overlaps another Unreal session.
param([string[]]$Editor = @(), [switch]$Mutates, [string[]]$Views = @(), [string]$Out = '', [int]$Minutes = 12)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent                        # Airport38
$outputs = Split-Path (Split-Path $root -Parent) -Parent
$project = Join-Path $outputs 'SkywardAir\UnrealProject\SkywardAir.uproject'
$umap = Join-Path $outputs 'SkywardAir\UnrealProject\Content\Airport38\L_Airport_Repair38.umap'
$engine = 'C:\Users\zaran\Documents\Codex\UE\Engine\Binaries\Win64\UnrealEditor.exe'
$blender = 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'
$t0 = Get-Date
if (Get-Process -Name 'UnrealEditor*' -ErrorAction SilentlyContinue) { throw 'An Unreal process is already running.' }
$stamp = $t0.ToString('yyyyMMdd-HHmmss')
if ($Editor.Count -and $Mutates) {
    $backup = Join-Path $PSScriptRoot ('Backup\L_Airport_Repair38.' + $stamp + '.umap.bak')
    New-Item -ItemType Directory -Force (Split-Path $backup) | Out-Null
    Copy-Item -LiteralPath $umap -Destination $backup -Force
    'level backed up to ' + $backup
}
foreach ($s in $Editor) {
    $script = (Resolve-Path (Join-Path $root $s)).Path
    $log = Join-Path $PSScriptRoot ('Logs\' + [IO.Path]::GetFileNameWithoutExtension($script) + '-' + $stamp + '.log')
    New-Item -ItemType Directory -Force (Split-Path $log) | Out-Null
    $a = @(('"' + $project + '"'), '-run=pythonscript', ('-script="' + $script + '"'), '-Unattended', '-NoSplash',
           '-NoSound', '-NullRHI', ('-abslog="' + $log + '"'))
    $p = Start-Process -FilePath $engine -ArgumentList $a -WindowStyle Hidden -PassThru
    $p.WaitForExit(1800000) | Out-Null
    $tail = Select-String -LiteralPath $log -Pattern 'LogPython: [A-Z0-9]+ (SUCCESS|ERROR|FAIL)|LogPython: Error' | Select-Object -Last 3
    '{0}: exit {1}  {2}' -f (Split-Path $script -Leaf), $p.ExitCode, (($tail | ForEach-Object { $_.Line.Trim() }) -join ' | ')
}
if ($Views.Count) {
    $outAbs = Join-Path $root $Out
    New-Item -ItemType Directory -Force $outAbs | Out-Null
    Get-ChildItem $outAbs -Filter *.png -ErrorAction SilentlyContinue | Remove-Item
    python (Join-Path $PSScriptRoot 'views50.py') $outAbs ($Views -join ',')
    & (Join-Path $root 'Pass48\Run-GameProbe48.ps1') -Flag Look48 -Probe look48_probe.py -Report Look48.json -Minutes $Minutes | Select-Object -Last 1
    & $blender -b --factory-startup -P (Join-Path $root 'Pass48\contact48_blender.py') -- $outAbs (Join-Path $outAbs 'sheet') | Out-Null
    'stills: ' + (Get-ChildItem $outAbs -Filter *.png | Where-Object { $_.Name -notlike 'sheet*' }).Count + '  sheets: ' +
        ((Get-ChildItem $outAbs -Filter 'sheet*.png' | ForEach-Object { $_.Name }) -join ',')
}
'elapsed {0:n0} s' -f ((Get-Date) - $t0).TotalSeconds
