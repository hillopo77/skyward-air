param([ValidateSet('Plane','Exterior','Spacious','Compare','Airport','Cabin','Night','Cockpit')][string]$Scene='Plane',[switch]$Play,[switch]$Exterior)
$project = Join-Path $PSScriptRoot 'UnrealProject\SkywardAir.uproject'
$engine = 'C:\Users\zaran\Documents\Codex\UE\Engine\Binaries\Win64\UnrealEditor.exe'
$maps = @{Plane='L_Plane_Reference';Exterior='L_Plane_Exterior15';Spacious='L_Cabin_Spacious121';Compare='L_Cabin_Compare';Airport='L_Airport_Gate07';Cabin='L_Cabin_Day';Night='L_Cabin_Night';Cockpit='L_Cockpit'}
if (-not (Test-Path -LiteralPath $engine)) { throw 'Set $engine in this launcher to your Unreal 5.8 installation.' }
$arguments = @('"'+$project+'"','/Game/Maps/'+$maps[$Scene],'-NoSplash','-NoSound')
if ($Play) { $arguments += @('-game','-windowed','-ResX=1600','-ResY=900') }
if ($Exterior) { $arguments += '-SkywardStartExterior' }
Start-Process -FilePath $engine -ArgumentList $arguments -WindowStyle Normal
