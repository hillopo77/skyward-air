# Pass46: run one read-only -game probe and wait for its report.
#
# Usage: Run-GameProbe46.ps1 -Flag Deck46 -Probe deck46_probe.py -Report Deck46.json
# Installs the probe and the dispatch (both, or the flag silently does
# nothing), launches the game with the flag, waits for the report to leave
# RUNNING, then closes the game. Refuses to overlap another Unreal session.
param([Parameter(Mandatory = $true)][string]$Flag,
      [Parameter(Mandatory = $true)][string]$Probe,
      [Parameter(Mandatory = $true)][string]$Report,
      [int]$Minutes = 8)
$ErrorActionPreference = 'Stop'
$pass46 = $PSScriptRoot
$airportRoot = Split-Path $pass46 -Parent
$outputs = Split-Path (Split-Path $airportRoot -Parent) -Parent
$project = Join-Path $outputs 'SkywardAir\UnrealProject\SkywardAir.uproject'
$pythonDir = Join-Path $outputs 'SkywardAir\UnrealProject\Content\Python'
$engine = 'C:\Users\zaran\Documents\Codex\UE\Engine\Binaries\Win64\UnrealEditor.exe'
if (Get-Process -Name 'UnrealEditor*' -ErrorAction SilentlyContinue) {
    throw 'An Unreal process is already running. Close it first; native sessions must not overlap.'
}
Copy-Item -LiteralPath (Join-Path $pass46 $Probe) -Destination $pythonDir -Force
Copy-Item -LiteralPath (Join-Path $airportRoot 'SourceAssets\airport_repair38.py') -Destination $pythonDir -Force
$out = Join-Path $pass46 $Report
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
if (Test-Path -LiteralPath $out) {
    Move-Item -LiteralPath $out -Destination ($out -replace '\.json$', ('.' + $stamp + '.json')) -Force
}
$log = Join-Path $pass46 ($Flag + '-' + $stamp + '.log')
$gameArgs = @(('"' + $project + '"'), '/Game/Airport38/L_Airport_Repair38', '-NoSplash',
              '-game', '-windowed', '-ResX=1280', '-ResY=720',
              '-Airport', '-AirportCompact12', '-AirportPass=10', '-Characters21',
              '-AirportJourney22', '-AirportClarity26', '-AirportRepair38',
              ('-' + $Flag), '-RenderOffscreen', '-NoSound', ('-abslog="' + $log + '"'))
$proc = Start-Process -FilePath $engine -ArgumentList $gameArgs -WindowStyle Hidden -PassThru
Write-Output ($Flag + ' started pid=' + $proc.Id)
$deadline = (Get-Date).AddMinutes($Minutes); $done = $false
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 5
    if (Test-Path -LiteralPath $out) {
        # An empty read mid-rewrite parses to $null; require a real end state.
        try { $st = (Get-Content -LiteralPath $out -Raw | ConvertFrom-Json).status; if ($st -and $st -ne 'RUNNING') { $done = $true; break } } catch { }
    }
    if ($proc.HasExited) { break }
}
if (!$proc.HasExited) { Stop-Process -Id $proc.Id -Force }
Start-Sleep -Seconds 2
if (!$done) { throw ($Flag + ' wrote no finished report.') }
Write-Output ('status=' + (Get-Content -LiteralPath $out -Raw | ConvertFrom-Json).status + '  report=' + $out)
