"""Pass50: put back every post-process volume's GI, reflection and SSAO settings
as they were before lumen50_editor.py (-run=pythonscript). MUTATES AND SAVES the level.

Lumen could not run here (DirectX 11 has no Lumen in this engine; DirectX 12
hangs this GPU driver), so the lighting goes back to the Pass49 set-up. The
level backed up just before the Lumen step is copied in as a temporary map,
read, and its volume settings copied onto the live level's volumes by label;
the temporary map is deleted again. Nothing else in the level changes.
"""
import unreal as u, json, shutil, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAP = '/Game/Airport38/L_Airport_Repair38'
TMP = '/Game/Airport38/Pass50Tmp/L_Before50'
CONTENT = HERE.parents[2] / 'SkywardAir' / 'UnrealProject' / 'Content'
BACKUP = HERE / 'Backup' / 'L_Airport_Repair38.20261031-221956.umap.bak'
KEYS = ['dynamic_global_illumination_method', 'reflection_method', 'ambient_occlusion_intensity']
R = dict(status='RUNNING', restored=[], missing=[])


def read_volumes():
    out = {}
    for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
        if isinstance(a, u.PostProcessVolume):
            s = a.get_editor_property('settings')
            out[a.get_actor_label()] = {k: (bool(s.get_editor_property('override_' + k)), s.get_editor_property(k)) for k in KEYS}
    return out


def main():
    dst = CONTENT / 'Airport38' / 'Pass50Tmp' / 'L_Before50.umap'
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(BACKUP, dst)
    u.AssetRegistryHelpers.get_asset_registry().scan_paths_synchronous(['/Game/Airport38/Pass50Tmp'], True)
    assert u.EditorLoadingAndSavingUtils.load_map(TMP), 'cannot open the backup copy'
    before = read_volumes()
    assert u.EditorLoadingAndSavingUtils.load_map(MAP)
    for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
        if not isinstance(a, u.PostProcessVolume):
            continue
        lab = a.get_actor_label()
        if lab not in before:
            R['missing'].append(lab); continue
        s = a.get_editor_property('settings')
        for k, (on, val) in before[lab].items():
            s.set_editor_property('override_' + k, on)
            s.set_editor_property(k, val)
        a.set_editor_property('settings', s)
        R['restored'].append([lab] + [str(before[lab][k][1]) if before[lab][k][0] else '-' for k in KEYS])
    assert u.EditorLoadingAndSavingUtils.save_current_level()
    u.EditorAssetLibrary.delete_directory('/Game/Airport38/Pass50Tmp')
    R['status'] = 'SUCCESS'


try:
    main()
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'RestoreGI50.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
print('RESTOREGI50', R['status'])
