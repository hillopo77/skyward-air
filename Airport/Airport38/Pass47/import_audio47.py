"""Pass47: import the ambience loops as looping SoundWaves.

Same import path native_flight39.import_audio uses. Creates assets under
/Game/Airport38/Pass47/Audio only; the level is not touched.
Run standalone under -run=pythonscript.
"""
import unreal as u, json, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEST = '/Game/Airport38/Pass47/Audio'
R = dict(status='RUNNING', imported=[])


def main():
    tasks = []
    for src in sorted((HERE / 'Audio').glob('*47.wav')):
        t = u.AssetImportTask()
        t.filename = str(src); t.destination_path = DEST; t.destination_name = src.stem
        t.automated = True; t.replace_existing = True; t.save = True
        tasks.append(t)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    for t in tasks:
        for path in t.imported_object_paths:
            a = u.load_asset(path)
            if a is None:
                continue
            a.set_editor_property('looping', True)
            u.EditorAssetLibrary.save_loaded_asset(a)
            R['imported'].append(dict(asset=path, looping=bool(a.get_editor_property('looping')),
                                      seconds=round(float(a.get_editor_property('duration')), 2)))
    R['status'] = 'SUCCESS' if len(R['imported']) == 5 else 'INCOMPLETE'


try:
    main()
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'ImportAudio47.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
print('IMPORTAUDIO47', R['status'])
