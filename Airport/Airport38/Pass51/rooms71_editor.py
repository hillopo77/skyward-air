"""Pass71: security, the washrooms and the WC passage, in the level (-run=pythonscript). MUTATES AND SAVES.
Run BEFORE the Rooms70 kits are re-imported: it makes the materials the new kits bind to.

Player brief: security had no effort in its textures and materials and it is hard to see in there; the
washroom was lazy; the seats outside face the wrong way.

  materials   MI_AP_P71Sec*: deep sea-green stone cladding, cool opal light, signal green, a white machine shell,
              slate tunnel, smoked curtain, slate lane floor; MI_AP_P71Mirror, a real mirror (parent M_AP_Satin23)
  machines    portals, scanners, curtains, tray and receiving stations and the operator console take the
              new shell / tunnel / curtain / green materials (only on those actors)
  light       'P71 security *': a soft linear light under each ceiling light line (shadowed), a washer on
              every wall, the feature wall's own spill, a light inside each scanner tunnel; and
              the room grade volume that covers security alone: neutral white balance, brighter exposure
  washrooms   the Pass34 vanity, toilets and recycling unit are hidden (the new kit has its own); the cubicle doors go walnut
              with brass hardware
  passage     'WC passage bench46' (an SM_AP_Bench27 mesh, whose seat faces -Y at yaw 0) faced the wall at
              yaw -90: turned to 90, its back 3 cm off the measured wall face
"""
import unreal as u, json, math, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAP = '/Game/Airport38/L_Airport_Repair38'
DIR = '/Game/Airport38/Pass48/Materials'
MASTER = '/Game/Airport23/Materials/M_AP_Satin23'
FACES = json.loads((HERE / 'Rooms71Faces.json').read_text(encoding='utf-8'))
MATS = {'MI_AP_P71SecStone': ((.2, .31, .29), 0.0, .6), 'MI_AP_P71SecOpal': ((.92, .96, 1.0), 40.0, .3),
        'MI_AP_P71Mirror': ((.86, .9, .94), 0.0, .04, 1.0),
        'MI_AP_P71Porcelain': ((.93, .93, .92), 0.0, .12, 0.0),
        'MI_AP_P71SecGreen': ((.25, 1.0, .4), 160.0, .3), 'MI_AP_P71SecShell': ((.86, .88, .9), 0.0, .28),
        'MI_AP_P71SecTunnel': ((.1, .12, .15), 0.0, .6), 'MI_AP_P71SecCurtain': ((.14, .18, .22), 0.0, .45),
        'MI_AP_P71SecLaneFloor': ((.18, .26, .34), 0.0, .7)}
SWAPS = [(('Security portal', 'X-ray scanner', 'Lane 0', 'Security operator'), 'MI_AP_P38EIvory', 'MI_AP_P71SecShell'),
         (('Security portal',), 'MI_AP_Pearl', 'MI_AP_P71SecShell'),
         (('Security portal',), 'MI_AP_GreenLED', 'MI_AP_P71SecGreen'),
         (('Security operator',), 'MI_AP_P34Cream', 'MI_AP_P71SecShell'),
         (('X-ray scanner',), 'MI_AP_P38EDark', 'MI_AP_P71SecTunnel'),
         (('Scanner 0',), 'MI_AP_P38ERubber', 'MI_AP_P71SecCurtain'),
         (('Terminal WC',), 'MI_AP_Ivory', 'MI_AP_P27Walnut'), (('Terminal WC',), 'MI_AP_Pearl', 'MI_AP_P27Walnut'),
         (('Terminal WC',), 'MI_AP_Steel', 'MI_AP_P38AGold')]
SEC = (-49, -36, -4, 10)
R = dict(status='RUNNING', materials=[], swaps=[], lights=[], grade={}, grades_here=[], wc={}, bench={})
ML = u.MaterialEditingLibrary


def ue(x, y, z):
    return u.Vector(x * 100, -y * 100, z * 100)


def face(room, key):
    return FACES.get('%s %s' % (room, key), [.09])[0]


def find_asset(name, cls='MaterialInstanceConstant'):
    reg = u.AssetRegistryHelpers.get_asset_registry()
    return next((a.get_asset() for a in reg.get_assets_by_class(u.TopLevelAssetPath('/Script/Engine', cls), True)
                 if str(a.asset_name) == name), None)


def materials():
    master = u.load_asset(MASTER) or find_asset('M_AP_Satin23', 'Material')
    tools = u.AssetToolsHelpers.get_asset_tools()
    for name, (rgb, emission, rough, *metal) in MATS.items():
        path = DIR + '/' + name
        mi = u.load_asset(path) if u.EditorAssetLibrary.does_asset_exist(path) else \
            tools.create_asset(name, DIR, u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
        ML.set_material_instance_parent(mi, master)
        ML.set_material_instance_vector_parameter_value(mi, 'BaseColor', u.LinearColor(*rgb, 1))
        ML.set_material_instance_scalar_parameter_value(mi, 'Emission', emission)
        ML.set_material_instance_scalar_parameter_value(mi, 'Roughness', rough)
        ML.set_material_instance_scalar_parameter_value(mi, 'Metallic', metal[0] if metal else 0.0)
        ML.update_material_instance(mi)
        assert u.EditorAssetLibrary.save_loaded_asset(mi)
        R['materials'].append(name)


def tag(a, label):
    a.set_actor_label(label)
    a.tags = [u.Name('Skyward:' + label)]
    a.set_folder_path('Lighting/Pass71')


def rect(EA, label, at, rot, w, h, lm, temp, att, shadows):
    a = EA.spawn_actor_from_class(u.RectLight, at, rot); tag(a, label)
    c = a.get_component_by_class(u.RectLightComponent)
    c.set_mobility(u.ComponentMobility.MOVABLE)
    c.set_editor_property('intensity_units', u.LightUnits.LUMENS)
    c.set_editor_property('intensity', float(lm))
    c.set_editor_property('use_temperature', True); c.set_editor_property('temperature', float(temp))
    c.set_editor_property('attenuation_radius', float(att))
    c.set_editor_property('source_width', float(w)); c.set_editor_property('source_height', float(h))
    c.set_editor_property('cast_shadows', bool(shadows)); c.set_editor_property('specular_scale', .5)
    R['lights'].append([label, lm])


def lights(EA):
    x0, x1, y0, y1 = SEC
    for x in (-45.75, -39.25):                                          # under the two ceiling light lines
        rect(EA, 'P71 security line %.2f' % x, ue(x, 3.0, 2.74), u.Rotator(0, -90, 0), 1300, 30, 5000, 4800, 1000, True)
    fw, fe, fs, fn = (face('security', k) for k in 'WESN')
    for key, at, yaw, length in (('W', (x0 + fw + .6, 3.0, 2.7), 180, 1340), ('E', (x1 - fe - .6, 3.0, 2.7), 0, 1340),
                                 ('S', (-42.5, y0 + fs + .6, 2.7), 90, 1240), ('N', (-42.5, y1 - fn - .6, 2.7), -90, 1240)):
        rect(EA, 'P71 security washer ' + key, ue(*at), u.Rotator(0, -35, yaw), length, 10, 1500, 4500, 450, False)
    rect(EA, 'P71 security feature spill', ue(x0 + fw + .35, 2.95, 2.1), u.Rotator(0, 0, 0), 600, 160, 900, 6500, 500, False)
    for bx in (-43.15, -38.05):                                          # inside each scanner tunnel
        a = EA.spawn_actor_from_class(u.PointLight, ue(bx, 3.0, 1.35), u.Rotator(0, 0, 0)); tag(a, 'P71 security tunnel %.2f' % bx)
        c = a.get_component_by_class(u.PointLightComponent)
        c.set_mobility(u.ComponentMobility.MOVABLE)
        c.set_editor_property('intensity_units', u.LightUnits.CANDELAS); c.set_editor_property('intensity', 30.0)
        c.set_editor_property('light_color', u.Color(r=191, g=235, b=255, a=255))
        c.set_editor_property('attenuation_radius', 150.0); c.set_editor_property('source_radius', 5.0)
        c.set_editor_property('cast_shadows', True)
        R['lights'].append([a.get_actor_label(), 30])


def contains(a, x, y):
    o, e = a.get_actor_bounds(False)
    return o.x - e.x <= x * 100 <= o.x + e.x and o.y - e.y <= -y * 100 <= o.y + e.y


def grade(EA, actors):
    """The room grade volume that covers security, and only security, gets a neutral white balance and a
    brighter exposure (duplicate_actor crashes in a commandlet, so no new volume is made). Its old values
    are kept in the report."""
    vols = [a for a in actors if isinstance(a, u.PostProcessVolume)]
    here = []
    for v in vols:
        if v.get_editor_property('unbound') or not contains(v, -42.5, 3.0):
            continue
        o, e = v.get_actor_bounds(False)
        box = [round((o.x - e.x) / 100, 2), round((o.x + e.x) / 100, 2), round((-o.y - e.y) / 100, 2), round((-o.y + e.y) / 100, 2)]
        s = v.get_editor_property('settings')
        rec = dict(label=v.get_actor_label(), priority=v.get_editor_property('priority'), box=box,
                   white_temp=[s.get_editor_property('override_white_temp'), s.get_editor_property('white_temp')],
                   exposure=[s.get_editor_property('override_auto_exposure_min_brightness'), s.get_editor_property('auto_exposure_min_brightness'),
                             s.get_editor_property('auto_exposure_max_brightness')])
        R['grades_here'].append(rec)
        only_here = box[0] >= SEC[0] - 1.5 and box[1] <= SEC[1] + 1.5 and box[2] >= SEC[2] - 1.5 and box[3] <= SEC[3] + 1.5
        here.append((v.get_editor_property('priority'), only_here, v))
    mine = [t for t in here if t[1]]
    if not mine:
        R['grade'] = dict(skipped='no grade volume covers security alone'); return
    v = max(mine, key=lambda t: t[0])[2]
    s = v.get_editor_property('settings')
    for k, val in (('white_temp', 5600.0), ('auto_exposure_min_brightness', 6.0), ('auto_exposure_max_brightness', 6.0)):
        s.set_editor_property('override_' + k, True); s.set_editor_property(k, val)
    v.set_editor_property('settings', s)
    R['grade'] = dict(changed=v.get_actor_label(), white_temp=5600.0, exposure=6.0)


def main():
    materials()
    assert u.EditorLoadingAndSavingUtils.load_map(MAP)
    EA = u.get_editor_subsystem(u.EditorActorSubsystem)
    actors = EA.get_all_level_actors()
    for a in actors:
        if a.get_actor_label().startswith('P71 security'):
            EA.destroy_actor(a)
    actors = EA.get_all_level_actors()
    mats = {n: u.load_asset(DIR + '/' + n) for n in MATS}
    mats['MI_AP_P27Walnut'] = find_asset('MI_AP_P27Walnut'); mats['MI_AP_P38AGold'] = find_asset('MI_AP_P38AGold')
    for a in actors:
        if not isinstance(a, u.StaticMeshActor):
            continue
        lab = a.get_actor_label(); c = a.static_mesh_component
        for prefixes, old, new in SWAPS:
            if not lab.startswith(prefixes):
                continue
            for i in range(c.get_num_materials()):
                m = c.get_material(i)
                if m and m.get_name() == old:
                    c.set_material(i, mats[new]); R['swaps'].append([lab, i, old, new])
        if lab in ('Vanity24_1808', 'Toilet24_1798', 'Toilet24_1803', 'Recycling24_1810'):   # replaced by the new kit
            a.set_actor_hidden_in_game(True); a.set_actor_enable_collision(False)
            a.set_is_temporarily_hidden_in_editor(True)
            R['wc'][lab] = 'hidden'
        if lab == 'WC passage bench46':
            o0, e0 = a.get_actor_bounds(False)
            a.set_actor_rotation(u.Rotator(0, 0, 90.0), False)
            o1, e1 = a.get_actor_bounds(False)
            wall_x = (-26 + face('wc_passage', 'W')) * 100
            loc = a.get_actor_location()
            a.set_actor_location(u.Vector(loc.x + (wall_x + 3 + e1.x) - o1.x, loc.y + (o0.y - o1.y), loc.z), False, False)
            o2, e2 = a.get_actor_bounds(False)
            R['bench'] = dict(before=[round(o0.x / 100, 3), round(-o0.y / 100, 3)], after=[round(o2.x / 100, 3), round(-o2.y / 100, 3)],
                              back=round((o2.x - e2.x) / 100, 3), wall=round(wall_x / 100, 3), yaw=90)
    lights(EA)
    grade(EA, EA.get_all_level_actors())
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    assert u.EditorLoadingAndSavingUtils.save_map(world, MAP), 'save failed'
    R['status'] = 'SUCCESS'


try:
    main()
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'RoomsEdit71.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
print('ROOMS71', R['status'])
