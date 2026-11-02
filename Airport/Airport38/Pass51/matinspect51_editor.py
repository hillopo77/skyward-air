"""Pass51: read-only look at candidate materials (parent, scalar/vector/texture params)."""
import unreal as u, json, traceback
from pathlib import Path
HERE = Path(__file__).resolve().parent
NAMES = ['MI_AP_WarmLED', 'MI_AP_P34LED', 'MI_AP_P38BLED', 'MI_AP_F25LED', 'MI_AP_P33WarmOpal', 'MI_AP_P38AOpal', 'MI_AP_P30Opal',
         'MI_AP_P37Opal', 'MI_AP_P38AGold', 'MI_AP_P43TFloor', 'MI_AP_P30Carpet', 'MI_AP_P43TOak', 'MI_AP_P38ANavy', 'MI_AP_P43TText',
         'MI_AP_P38AText', 'MI_AP_WhiteLED', 'MI_AP_P27Walnut', 'MI_AP_P34Stone', 'MI_AP_P38AStone', 'MI_AP_P27Limestone', 'MI_AP_P43TBronze']
R = dict(status='RUNNING', mats={})
ML = u.MaterialEditingLibrary
try:
    reg = u.AssetRegistryHelpers.get_asset_registry()
    for ad in reg.get_assets_by_class(u.TopLevelAssetPath('/Script/Engine', 'MaterialInstanceConstant'), True):
        n = str(ad.asset_name)
        if n not in NAMES:
            continue
        mi = ad.get_asset()
        row = dict(path=str(ad.package_name), parent=mi.get_editor_property('parent').get_path_name() if mi.get_editor_property('parent') else None, s={}, v={}, t={})
        for p in ML.get_scalar_parameter_names(mi):
            row['s'][str(p)] = ML.get_material_instance_scalar_parameter_value(mi, p)
        for p in ML.get_vector_parameter_names(mi):
            c = ML.get_material_instance_vector_parameter_value(mi, p); row['v'][str(p)] = [round(c.r, 3), round(c.g, 3), round(c.b, 3)]
        for p in ML.get_texture_parameter_names(mi):
            t = ML.get_material_instance_texture_parameter_value(mi, p); row['t'][str(p)] = t.get_name() if t else None
        R['mats'].setdefault(n, []).append(row)
    R['status'] = 'SUCCESS'
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'MatInspect51.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
print('MATINSPECT51', R['status'])
