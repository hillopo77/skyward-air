"""Pass51: glowing finishes for the hall fit-out (-run=pythonscript). MUTATES AND SAVES
three new material instances (re-runnable; nothing existing changes).

At the level's fixed EV 6.5 the existing LED/opal instances (emission 2-14)
read as flat grey. These are children of the same M_AP_Satin23 master:
  MI_AP_P51SignGlow  sign lettering, warm ivory, lit from behind
  MI_AP_P51Soffit    the opal light panels under the check-in canopy
  MI_AP_P51Runway    the flush 'runway' lights in the floor route
"""
import unreal as u, json, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIR = '/Game/Airport38/Pass48/Materials'
MASTER = '/Game/Airport38/Materials/M_AP_Satin23'
MATS = {'MI_AP_P51SignGlow': ((1.0, .88, .66), 12.0, .6), 'MI_AP_P51Soffit': ((1.0, .84, .62), 5.0, .7),
        'MI_AP_P51Runway': ((1.0, .80, .52), 120.0, .4), 'MI_AP_P58CabinPanel': ((1.0, .96, .9), 25.0, .6), 'MI_AP_P66CabinStrip': ((1.0, .87, .68), 4.5, .6)}
R = dict(status='RUNNING', made=[])
ML = u.MaterialEditingLibrary
try:
    master = u.load_asset(MASTER)
    if master is None:                         # find the master wherever it lives
        reg = u.AssetRegistryHelpers.get_asset_registry()
        ad = next(a for a in reg.get_assets_by_class(u.TopLevelAssetPath('/Script/Engine', 'Material'), True) if str(a.asset_name) == 'M_AP_Satin23')
        master = ad.get_asset()
    tools = u.AssetToolsHelpers.get_asset_tools()
    for name, (rgb, emission, rough) in MATS.items():
        path = DIR + '/' + name
        mi = u.load_asset(path) if u.EditorAssetLibrary.does_asset_exist(path) else \
            tools.create_asset(name, DIR, u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
        ML.set_material_instance_parent(mi, master)
        ML.set_material_instance_vector_parameter_value(mi, 'BaseColor', u.LinearColor(*rgb, 1))
        ML.set_material_instance_scalar_parameter_value(mi, 'Emission', emission)
        ML.set_material_instance_scalar_parameter_value(mi, 'Roughness', rough)
        ML.update_material_instance(mi)
        assert u.EditorAssetLibrary.save_loaded_asset(mi)
        R['made'].append([name, master.get_path_name(), emission])
    R['status'] = 'SUCCESS'
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'Glow51.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
print('GLOW51', R['status'])

