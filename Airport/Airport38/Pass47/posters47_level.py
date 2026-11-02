"""Pass47: lit travel-poster lightboxes for the two bare corridors and the
repack room.

The public-return (23 m) and landside corridors are bare wall end to end. This
hangs five advertising lightboxes: the flight-board frame the terminal already
uses (SM_AP_ScreenBoard), at 0.6 scale so it clears the 3.2 m ceiling, showing
three Skyward Air travel posters drawn in the house style
(posters47_blender.py) through the screen material, like a lit advert.

Spots were picked clear of every tall thing standing at those walls
(planters, the departures board, the screening doors); the boxes hang from
1.28 to 2.62 m, above benches and trolleys. At yaw 0 this frame's face points
south, so north-wall boxes use yaw 0 and south-wall ones yaw 180 (the Pass46
lesson). Backs sit on the measured wall faces.

These are not flight displays, so they are deliberately not given a screen
role; their material is set on the actor. MUTATES AND SAVES the level.
"""
import unreal as u, json, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAP = '/Game/Airport38/L_Airport_Repair38'
DEST = '/Game/Airport38/Pass47/Posters'
SCREENS = '/Game/Airport38/EquipmentScreens'
SCALE = 0.6
Z = 1.95
HALF_DEPTH = 0.093 * SCALE / 2 * 2        # board half-depth at this scale (0.093 m at 1.0)
SPOTS = [  # label, x, wall face y, side, poster
    ('Public return poster47 0', -44.0, -18.09, 'north', 'AzureBay'),
    ('Public return poster47 1', -34.0, -18.09, 'north', 'Highlands'),
    ('Public return poster47 2', -40.0, -21.91, 'south', 'CoralCoast'),
    ('Landside poster47 0', -46.0, -7.91, 'south', 'AzureBay'),
    ('Landside poster47 1', -33.5, -4.09, 'north', 'CoralCoast'),
    # Round 2: the repack room behind security (x -36..-32, y 0..10) was bare
    # wall on every side. South wall face y 0.09; east wall face x -32.09,
    # its board above the charging counter (top ~1.0 m). For east/west walls
    # the second number is the wall face x and the first the board's y.
    ('Recovery poster47 0', -34.0, 0.09, 'south', 'Highlands'),
    ('Recovery poster47 1', 2.45, -32.09, 'east', 'AzureBay'),
]
R = dict(status='RUNNING', posters=[], materials={})


def main():
    AT = u.AssetToolsHelpers.get_asset_tools()
    ML = u.MaterialEditingLibrary
    dep_tex = u.load_asset(SCREENS + '/T_AP_UI38_Departures')
    mats = {}
    for name in ('AzureBay', 'Highlands', 'CoralCoast'):
        t = u.AssetImportTask()
        t.filename = str(HERE / 'DisplayArt' / ('T_AP_Poster47_%s.png' % name))
        t.destination_path = DEST; t.destination_name = 'T_AP_Poster47_' + name
        t.automated = True; t.replace_existing = True; t.save = True
        AT.import_asset_tasks([t])
        tex = u.load_asset(DEST + '/T_AP_Poster47_' + name)
        for prop in ('compression_settings', 'srgb', 'mip_gen_settings', 'lod_group', 'filter'):
            try:
                tex.set_editor_property(prop, dep_tex.get_editor_property(prop))
            except Exception:
                pass
        u.EditorAssetLibrary.save_loaded_asset(tex)
        mi_path = DEST + '/MI_AP_Poster47_' + name
        if not u.EditorAssetLibrary.does_asset_exist(mi_path):
            u.EditorAssetLibrary.duplicate_asset(SCREENS + '/MI_AP_UI38_Departures', mi_path)
        mi = u.load_asset(mi_path)
        ML.set_material_instance_texture_parameter_value(mi, 'ScreenImage', tex)
        # A lit advert, a little softer than the flight screens (70).
        ML.set_material_instance_scalar_parameter_value(mi, 'ScreenLuminance', 50.0)
        u.EditorAssetLibrary.save_loaded_asset(mi)
        mats[name] = mi
        R['materials'][name] = mi.get_path_name()

    assert u.EditorLoadingAndSavingUtils.load_map(MAP)
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    EA = u.get_editor_subsystem(u.EditorActorSubsystem)
    acts = {a.get_actor_label(): a for a in EA.get_all_level_actors()}
    tmpl = acts['Concourse departures board46'].static_mesh_component
    for label, x, face_y, side, poster in SPOTS:
        if label in acts:
            EA.destroy_actor(acts[label])
        if side in ('north', 'south'):
            y = face_y - HALF_DEPTH if side == 'north' else face_y + HALF_DEPTH
            yaw = 0.0 if side == 'north' else 180.0
        else:                                   # x holds y, face_y holds the wall face x
            x, y = (face_y - HALF_DEPTH if side == 'east' else face_y + HALF_DEPTH), x
            yaw = 90.0 if side == 'east' else -90.0   # face west / east into the room
        a = EA.spawn_actor_from_class(u.StaticMeshActor, u.Vector(x * 100, -y * 100, Z * 100), u.Rotator(0, 0, yaw))
        a.set_actor_label(label)
        a.set_folder_path('Airport38/Pass47/Posters')
        a.set_actor_scale3d(u.Vector(SCALE, SCALE, SCALE))
        c = a.static_mesh_component
        c.set_static_mesh(tmpl.static_mesh)
        screen_slots = []
        for i in range(tmpl.get_num_materials()):
            slot = str(c.static_mesh.static_materials[i].material_slot_name)
            if slot.startswith('MI_AP_Screen'):
                c.set_material(i, mats[poster]); screen_slots.append(slot)
            else:
                c.set_material(i, tmpl.get_material(i))
        c.set_mobility(u.ComponentMobility.STATIC)
        c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
        o, e = a.get_actor_bounds(False)
        R['posters'].append(dict(actor=label, poster=poster, wall=side, yaw=yaw, screen_slots=screen_slots,
                                 x=[round((o.x - e.x) / 100, 2), round((o.x + e.x) / 100, 2)],
                                 y=[round(-(o.y + e.y) / 100, 3), round(-(o.y - e.y) / 100, 3)],
                                 z=[round((o.z - e.z) / 100, 2), round((o.z + e.z) / 100, 2)]))
    assert u.EditorLoadingAndSavingUtils.save_map(world, MAP), 'save_map failed'
    R['status'] = 'SUCCESS'


try:
    main()
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'Posters47.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
print('POSTERS47', R['status'])
