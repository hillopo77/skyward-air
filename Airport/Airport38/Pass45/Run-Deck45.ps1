# Pass45 entrance exposure probe. Offscreen, read-only, one game process only.
# Mirrors Open-Airport38.ps1's mode flags exactly so the probe runs under the
# same runtime configuration as ordinary play, with one extra flag added.
$ErrorActionPreference = 'Stop'
$pass45 = $PSScriptRoot
$airportRoot = Split-Path $pass45 -Parent
$outputs = Split-Path (Split-Path $airportRoot -Parent) -Parent
$project = Join-Path $outputs 'SkywardAir\UnrealProject\SkywardAir.uproject'
$engine = 'C:\Users\zaran\Documents\Codex\UE\Engine\Binaries\Win64\UnrealEditor.exe'

if (!(Test-Path -LiteralPath $engine)) { throw 'Unreal Editor not found.' }
if (!(Test-Path -LiteralPath $project)) { throw 'SkywardAir project not found.' }
if (Get-Process -Name 'UnrealEditor*' -ErrorAction SilentlyContinue) {
    throw 'An Unreal process is already running. Close it first; native sessions must not overlap.'
}

$probeArgs = @(
    ('"' + $project + '"'), '/Game/Airport38/L_Airport_Repair38', '-NoSplash',
    '-game', '-windowed', '-ResX=1920', '-ResY=1080',
    '-Airport', '-AirportCompact12', '-AirportPass=10', '-Characters21',
    '-AirportJourney22', '-AirportClarity26', '-AirportRepair38',
    '-Deck45',
    '-RenderOffscreen', '-NoSound', '-Unattended', '-NoCrashDialog',
    ('-abslog="' + (Join-Path $pass45 'Deck45Run.log') + '"')
)

$report = Join-Path $pass45 'DeckRaster45.json'
if (Test-Path -LiteralPath $report) { Remove-Item -LiteralPath $report -Force }

$started = Get-Date
$proc = Start-Process -FilePath $engine -ArgumentList $probeArgs -WindowStyle Hidden -PassThru
Write-Output ("probe started pid=" + $proc.Id)

while (((Get-Date) - $started).TotalSeconds -lt 900) {
    if (Test-Path -LiteralPath $report) {
        try { $d = Get-Content -LiteralPath $report -Raw | ConvertFrom-Json } catch { Start-Sleep -Milliseconds 300; continue }
        if ($d.status -ne 'RUNNING') {
            Write-Output ("status=" + $d.status + " containment escapes=" + $d.deck.Count)
            if ($d.error) { Write-Output $d.error }
            $proc.WaitForExit(60000) | Out-Null
            Write-Output ("process exit code = " + $proc.ExitCode)
            exit $(if ($d.status -eq 'SUCCESS' -and $proc.ExitCode -eq 0) { 0 } else { 1 })
        }
    }
    if ($proc.HasExited) { throw ('Engine exited before its final report, code ' + $proc.ExitCode) }
    Start-Sleep -Seconds 2
}
$proc.Kill()
throw 'Exposure probe exceeded its time limit.'
