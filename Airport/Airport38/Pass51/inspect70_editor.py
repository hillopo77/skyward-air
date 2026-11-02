"""Pass70: read-only inventory for the player's Pass69 feedback (-run=pythonscript, no save).

Writes Pass51/Inspect70.json:
  furniture  every stool / desk / table / bar / counter / ledge / bench actor in the terminal: label, mesh, location,
             size, collision enabled + profile, the mesh's simple-collision counts and trace flag (walk-through hunt)
  extinguishers  every actor whose label or mesh says extinguisher, and anything that looks like its holder
  a08        every actor within 1.2 m of the A08 sign wall and the terrace, with bounds (z-fighting hunt)
  rooms      security, WC passage and WC: every actor inside, label / mesh / location / size / materials
  kids       the A08 play corner
"""
import unreal as u, json, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOMS = {'security': (-49, -36, -4, 10), 'wc_passage': (-26, -23, -12, -1), 'wc': (-23, -14, -12, -3)}
FURN = ('stool', 'desk', 'table', 'bar', 'counter', 'ledge', 'bench', 'work bar', 'worktop')
R = dict(status='RUNNING', furniture=[], extinguishers=[], a08=[], rooms={k: [] for k in ROOMS}, kids=[], cabin=[], agents=[])


def src(v):
    return [round(v.x / 100, 3), round(-v.y / 100, 3), round(v.z / 100, 3)]


def geom(mesh):
    try:
        b = mesh.get_editor_property('body_setup')
        g = b.get_editor_property('agg_geom')
        return dict(box=len(g.get_editor_property('box_elems')), sphere=len(g.get_editor_property('sphere_elems')),
                    sphyl=len(g.get_editor_property('sphyl_elems')), convex=len(g.get_editor_property('convex_elems')),
                    flag=str(b.get_editor_property('collision_trace_flag')).split('.')[-1][:24])
    except Exception as e:
        return dict(error=str(e)[:80])


def row(a, mats=False):
    o, e = a.get_actor_bounds(False)
    c = a.static_mesh_component if isinstance(a, u.StaticMeshActor) else None
    m = c.static_mesh if c else None
    r = a.get_actor_rotation()
    d = dict(label=a.get_actor_label(), cls=a.get_class().get_name(), mesh=m.get_name() if m else None, centre=src(o),
             size=[round(e.x / 50, 2), round(e.y / 50, 2), round(e.z / 50, 2)], yaw=round(r.yaw, 1), pitch=round(r.pitch, 1),
             roll=round(r.roll, 1), hidden=a.is_hidden_ed(), tags=[str(t) for t in a.tags][:4])
    if c:
        d.update(coll=str(c.get_collision_enabled()).split('.')[-1][:20], profile=str(c.get_collision_profile_name()),
                 mob=str(c.mobility).split('.')[-1][:8], hig=c.get_editor_property('hidden_in_game'))
        if mats:
            d['mats'] = [(c.get_material(i).get_name() if c.get_material(i) else None) for i in range(c.get_num_materials())]
    return d


try:
    assert u.EditorLoadingAndSavingUtils.load_map('/Game/Airport38/L_Airport_Repair38')
    actors = u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
    for a in actors:
        try:
            lab = a.get_actor_label(); low = lab.lower()
            if not isinstance(a, (u.StaticMeshActor, u.SkeletalMeshActor)):
                continue
            o, e = a.get_actor_bounds(False); p = src(o)
            if 12.5 < p[0] < 19.5 and -6 < p[1] < 31 and any(k in lab for k in ('bin', 'Bin', 'Rack', 'PSU', 'Passenger service',
                                                                                  'Cabin broad', 'stair', 'Stair', 'hold', 'Hold', 'hatch', 'Hatch')):
                R['cabin'].append(row(a)); continue
            if isinstance(a, u.SkeletalMeshActor) and -20 < p[0] < -15 and -3 < p[1] < 2:
                R['agents'].append(row(a)); continue
            if not (-60 < p[0] < 12):                                  # the terminal only, not the aircraft
                continue
            m = a.static_mesh_component.static_mesh if isinstance(a, u.StaticMeshActor) and a.static_mesh_component else None
            mn = (m.get_name() if m else '').lower()
            if any(k in low or k in mn for k in FURN) and max(e.x, e.y) < 900:
                d = row(a); d['geom'] = geom(m) if m else None; R['furniture'].append(d)
            if 'xting' in low or 'xting' in mn or 'fire' in low and ('cab' in low or 'brack' in low or 'hold' in low):
                R['extinguishers'].append(row(a, True))
            if -32 <= p[0] <= -24 and 14 <= p[1] <= 34.5 and (p[1] > 29 or 'A08' in lab or 'terrace' in low or 'P64' in lab or 'Gate' in lab):
                R['a08'].append(row(a, True))
            if -30 <= p[0] <= -23 and 30 <= p[1] <= 34.5:
                R['kids'].append(row(a, True))
            for k, (x0, x1, y0, y1) in ROOMS.items():
                if x0 <= p[0] <= x1 and y0 <= p[1] <= y1 and p[2] < 6:
                    R['rooms'][k].append(row(a, True))
        except Exception as ex:
            R.setdefault('notes', []).append(str(ex)[:120])
    R['status'] = 'SUCCESS'
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'Inspect70.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
print('INSPECT70', R['status'])
