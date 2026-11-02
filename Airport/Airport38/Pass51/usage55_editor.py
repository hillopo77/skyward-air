"""Pass55: every base material gets the 'used with static lighting' usage flag
(-run=pythonscript). MUTATES AND SAVES materials.

The project's materials were all created without it, which never mattered
while every light was movable. With baked lighting the engine replaced every
surface with the default checkerboard ('missing usage flag StaticLighting').
Only the flag changes; the previous value is recorded in Usage55.json.
"""
import unreal as u, json, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = dict(status='RUNNING', changed=[], failed=[])
try:
    reg = u.AssetRegistryHelpers.get_asset_registry()
    for ad in reg.get_assets_by_class(u.TopLevelAssetPath('/Script/Engine', 'Material'), True):
        pkg = str(ad.package_name)
        if not pkg.startswith('/Game/'):
            continue
        m = ad.get_asset()
        try:
            if not m.get_editor_property('used_with_static_lighting'):
                m.set_editor_property('used_with_static_lighting', True)
                u.MaterialEditingLibrary.recompile_material(m)
                u.EditorAssetLibrary.save_loaded_asset(m)
                R['changed'].append(pkg)
        except Exception as e:
            R['failed'].append([pkg, str(e)[:120]])
    R['status'] = 'SUCCESS'
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'Usage55.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
print('USAGE55', R['status'], len(R['changed']))
