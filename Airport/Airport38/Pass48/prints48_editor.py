"""Pass48: printed-art materials (-run=pythonscript). Imports T_AP_Mural48 and
makes MI_AP_P48Mural from the project's textured master M_AP_PH24 (matt
print, not a glowing screen). MUTATES AND SAVES assets only."""
import unreal as u, json, traceback
from pathlib import Path
HERE = Path(__file__).resolve().parent
DEST = '/Game/Airport38/Pass48'
R = dict(status='RUNNING')
try:
    t = u.AssetImportTask()
    for k, v in dict(filename=str(HERE / 'Textures' / 'T_AP_Mural48.png'), destination_path=DEST + '/Textures',
                     destination_name='T_AP_Mural48', automated=True, save=True, replace_existing=True).items():
        t.set_editor_property(k, v)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    tex = u.load_asset(DEST + '/Textures/T_AP_Mural48')
    tex.set_editor_property('srgb', True)
    tex.set_editor_property('address_x', u.TextureAddress.TA_CLAMP); tex.set_editor_property('address_y', u.TextureAddress.TA_CLAMP)
    u.EditorAssetLibrary.save_loaded_asset(tex)
    path = DEST + '/Materials/MI_AP_P48Mural'
    mi = u.load_asset(path) or u.AssetToolsHelpers.get_asset_tools().create_asset(
        'MI_AP_P48Mural', DEST + '/Materials', u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
    ML = u.MaterialEditingLibrary
    ML.set_material_instance_parent(mi, u.load_asset('/Game/Airport24/Materials/M_AP_PH24'))
    ML.set_material_instance_texture_parameter_value(mi, 'BaseTexture', tex)
    ML.set_material_instance_scalar_parameter_value(mi, 'Roughness', .75)
    ML.set_material_instance_scalar_parameter_value(mi, 'Specular', .3)
    ML.set_material_instance_scalar_parameter_value(mi, 'Metallic', 0.0)
    u.EditorAssetLibrary.save_loaded_asset(mi)
    R.update(status='SUCCESS', material=mi.get_path_name())
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'Prints48.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
