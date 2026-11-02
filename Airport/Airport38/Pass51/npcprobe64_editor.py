import unreal as u, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
R = []
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Airport38/L_Airport_Repair38')
for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
    l = a.get_actor_label()
    if l.endswith('Waiting passenger 6') or l.endswith('Waiting passenger 0'):
        p = a.get_actor_location(); par = a.get_attach_parent_actor()
        R.append([l, a.get_class().get_name(), a.get_name(), [round(p.x / 100, 2), round(-p.y / 100, 2), round(p.z / 100, 2)],
                  par.get_actor_label() if par else None, str(a.root_component.get_editor_property('mobility')), a.get_level().get_path_name() if a.get_level() else None])
(HERE / 'NpcProbe64.json').write_text(json.dumps(R, indent=1))
print('NPCPROBE64 done')
