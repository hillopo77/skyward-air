# Pass55: build the level's lighting with Lightmass (ResavePackages -BuildLighting).
# Usage: Bake55.ps1 [-Quality Preview|Medium|High|Production]
param([string]$Quality = 'Preview')
$ErrorActionPreference = 'Stop'
$outputs = Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
$project = Join-Path $outputs 'SkywardAir\UnrealProject\SkywardAir.uproject'
$umap = Join-Path $outputs 'SkywardAir\UnrealProject\Content\Airport38\L_Airport_Repair38.umap'
$engine = 'C:\Users\zaran\Documents\Codex\UE\Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
if (Get-Process -Name 'UnrealEditor*' -ErrorAction SilentlyContinue) { throw 'An Unreal process is already running.' }
$stamp = (Get-Date).ToString('yyyyMMdd-HHmmss')
Copy-Item -LiteralPath $umap -Destination (Join-Path $PSScriptRoot "Backup\L_Airport_Repair38.$stamp.prebake.umap") -Force
$log = Join-Path $PSScriptRoot "Logs\Bake55-$Quality-$stamp.log"
$t0 = Get-Date
$a = @(('"' + $project + '"'), '-run=ResavePackages', '-BuildLighting', "-Quality=$Quality", '-AllowCommandletRendering',
       '-Map=L_Airport_Repair38', '-IgnoreChangelist', '-Unattended', '-NoSplash', '-NoSound', ('-abslog="' + $log + '"'))
$p = Start-Process -FilePath $engine -ArgumentList $a -WindowStyle Hidden -PassThru
$p.WaitForExit(5400000) | Out-Null
if (-not $p.HasExited) { $p.Kill(); 'TIMEOUT after 90 min' }
'exit {0}  {1:n1} min' -f $p.ExitCode, ((Get-Date) - $t0).TotalMinutes
Select-String -LiteralPath $log -Pattern 'Lighting|Lightmass|Swarm|BuildLighting|Error' | Select-Object -Last 25 | ForEach-Object { $_.Line.Substring(0, [Math]::Min(220, $_.Line.Length)) }
