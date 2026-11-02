"""Pass71: what the level holds for each extinguisher station (read-only, -run=pythonscript).
Writes Pass51/Inspect71.json: label, mesh, location, rotation, bounds, materials, hidden."""
import unreal as u, json, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = dict(status='RUNNING', actors=[])
try:
    assert u.EditorLoadingAndSavingUtils.load_map('/Game/Airport38/L_Airport_Repair38')
    for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
        lab = a.get_actor_label()
        if not lab.startswith(('Safety station', 'Usable extinguisher', 'P70 ', 'P71 ')) and 'xtinguisher' not in lab:
            continue
        rec = dict(label=lab, cls=a.get_class().get_name())
        if isinstance(a, u.StaticMeshActor):
            c = a.static_mesh_component; m = c.static_mesh
            rec.update(mesh=m.get_path_name() if m else None, mats=[(c.get_material(i).get_name() if c.get_material(i) else None) for i in range(c.get_num_materials())])
        p, r = a.get_actor_location(), a.get_actor_rotation(); o, e = a.get_actor_bounds(False)
        rec.update(loc=[round(p.x / 100, 3), round(-p.y / 100, 3), round(p.z / 100, 3)], yaw=round(r.yaw, 1),
                   bounds=[round((o.x - e.x) / 100, 2), round((o.x + e.x) / 100, 2), round((-o.y - e.y) / 100, 2), round((-o.y + e.y) / 100, 2),
                           round((o.z - e.z) / 100, 2), round((o.z + e.z) / 100, 2)], hidden=a.is_hidden_ed())
        R['actors'].append(rec)
    R['status'] = 'SUCCESS'
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'Inspect71.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
print('INSPECT71', R['status'])
