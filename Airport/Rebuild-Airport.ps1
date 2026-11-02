param([switch]$SkipModels)
$airportPython='C:\Users\zaran\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$airportScript=Join-Path $PSScriptRoot 'Compact12\SourceAssets\RebuildCompact12.py'
$airportOptions=@()
if ($SkipModels) {$airportOptions+='--skip-models'}
& $airportPython $airportScript @airportOptions
if ($LASTEXITCODE -ne 0) {throw 'Rebuild failed. Read Compact12/ArtBible/Rebuild logs.'}
