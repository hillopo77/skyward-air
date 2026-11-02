# Pass66: run Unreal steps one after another, each only after 20 s with no Unreal process, retrying when
# another tool starts a session first. Usage: Queue66.ps1 -Steps 'props','probe','cabin','views','journey'
param([string[]]$Steps)
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root
function Quiet { $q = 0; while ($q -lt 20) { if (Get-Process UnrealEditor* -ErrorAction SilentlyContinue) { $q = 0 } else { $q += 5 }; Start-Sleep 5 } }
function Run($name, [scriptblock]$body) {
    for ($try = 1; $try -le 6; $try++) {
        Quiet
        $out = try { & $body 2>&1 | Out-String } catch { $_.ToString() }
        if ($out -match 'already running') { Write-Output "$name : collided with another session, retrying"; continue }
        Write-Output ("$name : " + ($out.Trim() -split "`n" | Select-Object -Last 3) -join ' | ')
        return
    }
    Write-Output "$name : gave up after 6 collisions"
}
foreach ($s in $Steps) {
    switch ($s) {
        'collide' { Run 'collide' { & .\Pass50\Check50.ps1 -Editor Pass51\collide66_editor.py } }
        'mug'     { Run 'mug' { & .\Pass50\Check50.ps1 -Editor Pass51\mug66_editor.py -Mutates } }
        'ceil'    { Run 'ceil' { & .\Pass48\Run-GameProbe48.ps1 -Flag P48_ceil66_probe -Probe ceil66_probe.py -Report Ceil66.json -Minutes 5 } }
        'plane'   { Run 'plane' { & .\Pass50\Check50.ps1 -Editor Pass51\glow51_editor.py,Pass51\plane66_editor.py -Mutates } }
        'props'   { Run 'props' { & .\Pass50\Check50.ps1 -Editor Pass51\loose66_editor.py -Mutates } }
        'probe'   { Run 'probe' { & .\Pass48\Run-GameProbe48.ps1 -Flag P48_game66_probe -Probe game66_probe.py -Report Game66.json -Minutes 6 } }
        'cabin'   { Run 'cabin' { & .\Pass50\Check50.ps1 -Views C1_cabin_aisle,C_aisle_fwd,C_aisle_low,C_business -Out Pass51\Look\C66 -Minutes 20 } }
        'views'   { Run 'views' { & .\Pass50\Check50.ps1 -Views R66_cafe_bar,R66_terrace_props,R66_reno_corner,R66_cafe_lounge,R66_kids_corner,P_a08_terrace,Z21_cafe_in -Out Pass51\Look\R66 -Minutes 20 } }
        'diag'    { Run 'diag' { & .\Pass50\Check50.ps1 -Views LX68_E_all,LX68_E_nosky,LX68_E_nogi,LX68_E_noamb,LX68_E_norect,LX68_E_nodir,LX68_E_norefl,LX68_E_onlylamps,LX68_E_reset,LX68_B_all,LX68_B_nosky,LX68_B_nogi,LX68_B_noamb,LX68_B_norect,LX68_B_nodir,LX68_B_norefl,LX68_B_onlylamps,LX68_B_reset -Out Pass51\Look\LX68 -Minutes 20 } }
        'floorline' { Run 'floorline' { & .\Pass48\Run-GameProbe48.ps1 -Flag P48_floorline68_probe -Probe floorline68_probe.py -Report FloorLine68.json -Minutes 5 } }
        'inspect69' { Run 'inspect69' { & .\Pass50\Check50.ps1 -Editor Pass51\cabin69_inspect_editor.py } }
        'cabin69' { Run 'cabin69' { & .\Pass50\Check50.ps1 -Editor Pass51\glow51_editor.py,Pass51\cabin69_editor.py,Pass51\plane66_editor.py -Mutates } }
        'cabinlook' { Run 'cabinlook' { & .\Pass50\Check50.ps1 -Views C1_cabin_aisle,C_aisle_fwd,C_aisle_low,C_business,C69_eco_window_seat,C69_eco_ceiling,C69_eco_aft,C69_eco_floor,C69_bus_suite,C69_bus_ceiling -Out Pass51\Look\C69 -Minutes 20 } }
        'inspect70' { Run 'inspect70' { & .\Pass50\Check50.ps1 -Editor Pass51\inspect70_editor.py } }
        'build70' { Run 'build70' { & .\Pass50\Check50.ps1 -Editor Pass51\glow51_editor.py,Pass51\cabin69_editor.py,Pass51\plane66_editor.py,Pass51\hud70_editor.py -Mutates } }
        'cabinlook70' { Run 'cabinlook70' { & .\Pass50\Check50.ps1 -Views C1_cabin_aisle,C_aisle_fwd,C_business,C69_eco_ceiling,C69_eco_floor,C69_eco_window_seat,C69_bus_suite,C70_into_cockpit,C70_eco_seated,C2_flight_deck -Out Pass51\Look\C70 -Minutes 20 } }
        'kit70' { Run 'kit70' { & .\Pass50\Check50.ps1 -Editor Pass48\import70_editor.py -Mutates } }
        'ext70' { Run 'ext70' { & .\Pass48\Run-GameProbe48.ps1 -Flag P48_ext70_probe -Probe ext70_probe.py -Report Ext70.json -Minutes 5 } }
        'look70' { Run 'look70' { & .\Pass50\Check50.ps1 -Views V70_a08_sign,V70_a08_sign_side,V70_a08_terrace,V70_a08_kids,V70_a07_desk_w,V70_a07_desk_e,V70_sec_1,V70_sec_2,V70_sec_3,V70_wcp_1,V70_wcp_2,V70_wc_1,V70_wc_2,V70_hold_stair -Out Pass51\Look\V70 -Minutes 20 } }
        'props70' { Run 'props70' { & .\Pass50\Check50.ps1 -Editor Pass51\props70_editor.py -Mutates } }
        'verify70' { Run 'verify70' { & .\Pass50\Check50.ps1 -Views V70_a08_sign,V70_a08_sign_side,V70_a08_terrace,V70_a08_kids,V70_a07_desk_w,V70_sec_1,V70_sec_2,V70_sec_3,V70_wcp_1,V70_wcp_2,V70_wc_1,V70_wc_2,X70_ext0,X70_ext1,X70_ext2,X70_ext3,X70_ext4,X70_sec_feature,X70_sec_recompose,X70_wc_vanity,C_aisle_fwd,C1_cabin_aisle,C_business,C70_into_cockpit -Out Pass51\Look\W70 -Minutes 25 } }
        'recheck70' { Run 'recheck70' { & .\Pass50\Check50.ps1 -Views X70_sec_feature,X70_sec_recompose,C_business,C1_cabin_aisle,C_aisle_fwd,V70_a08_terrace -Out Pass51\Look\R70 -Minutes 20 } }
        'hudtext70' { Run 'hudtext70' { & .\Pass50\Check50.ps1 -Editor Pass51\hud70_editor.py -Mutates } }
        'rooms71probe' { Run 'rooms71probe' { & .\Pass48\Run-GameProbe48.ps1 -Flag P48_rooms71_probe -Probe rooms71_probe.py -Report Rooms71.json -Minutes 5 } }
        'walls71' { Run 'walls71' { & .\Pass48\Run-GameProbe48.ps1 -Flag P48_walls71_probe -Probe walls71_probe.py -Report Walls71.json -Minutes 5 } }
        'build71' { $b = & 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' -b --factory-startup -P (Join-Path $root 'Pass51\rooms70_blender.py') 2>&1 | Select-String 'ROOMS70|Error|Traceback'; Write-Output ("build71 : " + ($b -join ' | ')); Write-Output ("views71 : " + (python (Join-Path $root 'Pass51\views71.py') 2>&1 | Out-String).Trim()) }
        'rooms71' { Run 'rooms71' { & .\Pass50\Check50.ps1 -Editor Pass51\rooms71_editor.py -Mutates } }
        'kit71' { Run 'kit71' { & .\Pass50\Check50.ps1 -Editor Pass48\import70_editor.py -Mutates } }
        'props71' { Run 'props71' { & .\Pass50\Check50.ps1 -Editor Pass51\props71_editor.py -Mutates } }
        'cabin72' { Run 'cabin72' { & .\Pass50\Check50.ps1 -Editor Pass51\cabin72_editor.py -Mutates } }
        'look71' { $g = Get-Content (Join-Path $root 'Pass51\Views71.json') -Raw | ConvertFrom-Json; $v = @($g.S71) + @($g.E71); Run 'look71' { & .\Pass50\Check50.ps1 -Views $v -Out Pass51\Look\S71 -Minutes 30 } }
        'look72' { $g = Get-Content (Join-Path $root 'Pass51\Views71.json') -Raw | ConvertFrom-Json; $v = @($g.P72); Run 'look72' { & .\Pass50\Check50.ps1 -Views $v -Out Pass51\Look\P72 -Minutes 25 } }
        'journey' { Run 'journey' { & .\Pass46\Run-Journey46.ps1 -Label pass66j1 } }
    }
}
