$project = Join-Path $PSScriptRoot 'UnrealProject\SkywardAir.uproject'
$script = Join-Path $PSScriptRoot 'UnrealProject\Content\Python\build_unreal.py'
$engine = 'C:\Users\zaran\Documents\Codex\UE\Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
& $engine $project '-run=pythonscript' ('-script='+$script) '-unattended' '-nop4' '-NullRHI' '-nosplash' '-nosound'
if ($LASTEXITCODE -ne 0) { throw 'Unreal build failed. See ArtBible/UnrealBuildReport.json and UnrealProject/Saved/Logs.' }
