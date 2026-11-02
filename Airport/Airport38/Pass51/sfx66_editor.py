"""Pass66: import Gameplay66's synthesised sound effects (Pass51/Sfx66/*.wav) as SoundWaves (-run=pythonscript).
MUTATES AND SAVES assets in /Game/Airport38/Gameplay66/Audio only. Re-runnable (replaces)."""
import unreal as u, json, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEST = '/Game/Airport38/Gameplay66/Audio'
R = dict(status='RUNNING', sounds=[])


def main():
    tasks = []
    for wav in sorted((HERE / 'Sfx66').glob('*.wav')):
        t = u.AssetImportTask()
        for k, v in dict(filename=str(wav), destination_path=DEST, destination_name=wav.stem, automated=True, save=True,
                         replace_existing=True).items():
            t.set_editor_property(k, v)
        tasks.append(t)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    for t in tasks:
        name = Path(t.get_editor_property('filename')).stem
        s = u.load_asset(DEST + '/' + name)
        assert s is not None, 'import failed: ' + name
        R['sounds'].append([name, round(s.get_editor_property('duration'), 3)])
    R['status'] = 'SUCCESS'


try:
    main()
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'Sfx66.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
print('SFX66', R['status'])
