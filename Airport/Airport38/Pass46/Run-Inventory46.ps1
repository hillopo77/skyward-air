# Pass46 whole-game inventory audit. Offscreen, read-only, one game process.
# Mirrors Open-Airport38.ps1's mode flags so the audit sees the same runtime
# configuration as ordinary play, with one extra flag added.
#
# Unlike the Pass45 launchers this copies the probe into Content/Python itself,
# so the file the engine imports is always the one in this folder.
$ErrorActionPreference = 'Stop'
$pass46 = $PSScriptRoot
$airportRoot = Split-Path $pass46 -Parent
$outputs = Split-Path (Split-Path $airportRoot -Parent) -Parent
$project = Join-Path $outputs 'SkywardAir\UnrealProject\SkywardAir.uproject'
$pythonDir = Join-Path $outputs 'SkywardAir\UnrealProject\Content\Python'
$engine = 'C:\Users\zaran\Documents\Codex\UE\Engine\Binaries\Win64\UnrealEditor.exe'

if (!(Test-Path -LiteralPath $engine)) { throw 'Unreal Editor not found.' }
if (!(Test-Path -LiteralPath $project)) { throw 'SkywardAir project not found.' }
if (Get-Process -Name 'UnrealEditor*' -ErrorAction SilentlyContinue) {
    throw 'An Unreal process is already running. Close it first; native sessions must not overlap.'
}

Copy-Item -LiteralPath (Join-Path $pass46 'inventory46_probe.py') -Destination $pythonDir -Force
Copy-Item -LiteralPath (Join-Path $airportRoot 'SourceAssets\airport_repair38.py') -Destination $pythonDir -Force
Write-Output 'installed inventory46_probe.py and the dispatch'

$probeArgs = @(
    ('"' + $project + '"'), '/Game/Airport38/L_Airport_Repair38', '-NoSplash',
    '-game', '-windowed', '-ResX=1920', '-ResY=1080',
    '-Airport', '-AirportCompact12', '-AirportPass=10', '-Characters21',
    '-AirportJourney22', '-AirportClarity26', '-AirportRepair38',
    '-Inventory46',
    '-RenderOffscreen', '-NoSound', '-Unattended', '-NoCrashDialog',
    ('-abslog="' + (Join-Path $pass46 'Inventory46Run.log') + '"')
)

$report = Join-Path $pass46 'Inventory46.json'
if (Test-Path -LiteralPath $report) { Remove-Item -LiteralPath $report -Force }

$started = Get-Date
$proc = Start-Process -FilePath $engine -ArgumentList $probeArgs -WindowStyle Hidden -PassThru
Write-Output ("audit started pid=" + $proc.Id)

while (((Get-Date) - $started).TotalSeconds -lt 1800) {
    if (Test-Path -LiteralPath $report) {
        try { $d = Get-Content -LiteralPath $report -Raw | ConvertFrom-Json } catch { Start-Sleep -Milliseconds 400; continue }
        if ($d.status -ne 'RUNNING') {
            Write-Output ("status=" + $d.status + " actors=" + $d.counted + "/" + $d.total +
                          " traced=" + $d.traced + " unsupported=" + $d.unsupported.Count)
            if ($d.error) { Write-Output $d.error }
            $proc.WaitForExit(90000) | Out-Null
            Write-Output ("process exit code = " + $proc.ExitCode)
            exit $(if ($d.status -eq 'SUCCESS' -and $proc.ExitCode -eq 0) { 0 } else { 1 })
        }
    }
    if ($proc.HasExited) { throw ('Engine exited before its final report, code ' + $proc.ExitCode) }
    Start-Sleep -Seconds 3
}
$proc.Kill()
throw 'Inventory audit exceeded its time limit.'
