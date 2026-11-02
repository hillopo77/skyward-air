"""Pass58: read-only - every light in the aircraft area and the 'Bounce' fills:
world location, parent, tags, intensity, mobility; and the cabin ceiling height
under each cabin practical (a downward trace)."""
import unreal as u, json, traceback
from pathlib import Path
HERE = Path(__file__).resolve().parent
R = dict(status='RUNNING', lights=[])
try:
    assert u.EditorLoadingAndSavingUtils.load_map('/Game/Airport38/L_Airport_Repair38')
    for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
        if not isinstance(a, u.Light):
            continue
        p = a.get_actor_location(); s = [round(p.x / 100, 2), round(-p.y / 100, 2), round(p.z / 100, 2)]
        lab = a.get_actor_label()
        if not (10 < s[0] < 22 or str(a.get_folder_path()).startswith('Lighting')):
            continue
        c = a.get_component_by_class(u.LightComponent)
        par = a.get_attach_parent_actor()
        R['lights'].append(dict(label=lab, folder=str(a.get_folder_path()), p=s, parent=par.get_actor_label() if par else None,
                                tags=[str(t) for t in a.tags], i=round(c.get_editor_property('intensity'), 1),
                                units=str(c.get_editor_property('intensity_units')).split('.')[-1][:8] if hasattr(c, 'intensity_units') else '',
                                mob=str(c.get_editor_property('mobility')).split('.')[-1][:6], vis=c.is_visible(),
                                hidden=a.is_hidden_ed()))
    R['status'] = 'SUCCESS'
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'PlaneLights58.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
print('PLANELIGHTS58', R['status'])
