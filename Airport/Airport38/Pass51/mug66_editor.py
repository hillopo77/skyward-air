"""Pass66: the plain mug imported without collision; rebuild it from the teal mug (which has it) in cream (-run=pythonscript).
MUTATES AND SAVES: new mesh SM_AP_P66MugCream, and the level's 'Airport66 mug NN' actors now use it."""
import unreal as u, json, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAP = '/Game/Airport38/L_Airport_Repair38'
DIR = '/Game/Airport38/Pass48Meshes'
R = dict(status='RUNNING', swapped=0)


def main():
    src, dst = DIR + '/SM_AP_P66MugTeal', DIR + '/SM_AP_P66MugCream'
    if u.EditorAssetLibrary.does_asset_exist(dst):
        u.EditorAssetLibrary.delete_asset(dst)
    mesh = u.EditorAssetLibrary.duplicate_asset(src, dst)
    assert mesh, 'duplicate failed'
    cream = u.load_asset('/Game/Airport38/Finish43/MI_AP_P34Cream') or next(
        (u.load_asset(p) for p in u.EditorAssetLibrary.list_assets('/Game', recursive=True, include_folder=False)
         if p.split('/')[-1].split('.')[0] == 'MI_AP_P34Cream'), None)
    assert cream, 'no cream material'
    for i, sm in enumerate(mesh.static_materials):
        if 'Teal' in str(sm.material_slot_name) or 'Teal' in (sm.material_interface.get_name() if sm.material_interface else ''):
            mesh.set_material(i, cream)
    u.EditorAssetLibrary.save_loaded_asset(mesh)
    assert u.EditorLoadingAndSavingUtils.load_map(MAP)
    EA = u.get_editor_subsystem(u.EditorActorSubsystem)
    for a in EA.get_all_level_actors():
        lab = a.get_actor_label()
        if lab.startswith('Airport66 mug ') and not lab.startswith('Airport66 mug teal'):
            a.static_mesh_component.set_static_mesh(mesh); R['swapped'] += 1
    assert u.EditorLoadingAndSavingUtils.save_current_level()
    R['status'] = 'SUCCESS'


try:
    main()
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'Mug66.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
print('MUG66', R['status'])
