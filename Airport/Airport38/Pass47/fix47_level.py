"""Pass47 level fixes (-run=pythonscript). MUTATES AND SAVES the level.

1. Forecourt duplicates. Pass46's inventory listed actors, not the instances
   inside `Airport instanced architecture and fittings`, so it concluded the
   forecourt was bare and placed 35 objects. The authored landscape was there
   as instances all along: 23 kerbs, 4 trees, 4 benches, 4 streetlights,
   3 taxis, 1 shuttle bus. 31 of the Pass46 actors double an instance -
   coincident kerbs, taxis and bus (the bus at a different yaw reads as two
   buses crossed), a bench, two lights, two trees crowding instanced trees.
   Those 31 are destroyed.

2. Two instanced trees (8 m) and two streetlights stand inside or on the edge
   of the 3.85 m forecourt canopy and grow through its roof. Their instances
   are removed and they are replanted as actors across the road on the far
   verge, so the road reads as an avenue instead of the canopy being speared.

3. Concourse: Pass46's plant in the mouth of the south alcove splits it down
   the middle. Removed; the alcove keeps its planter by the east wall.

4. Arrivals board artwork: imports T_AP_UI38_Arrivals.png beside the other
   screen textures with the same settings as Departures, and makes
   MI_AP_UI38_Arrivals from MI_AP_UI38_Departures with the image swapped.
   The routing itself is a code and data change made alongside this script.
"""
import unreal as u, json, time, math, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAP = '/Game/Airport38/L_Airport_Repair38'
SCREENS = '/Game/Airport38/EquipmentScreens'
CANOPY = (-61.3, -52.95, -21.0, -3.5)

DESTROY = (['Forecourt kerb46 %02d' % i for i in range(1, 22)] +
           ['Forecourt taxi46 0', 'Forecourt taxi46 1', 'Forecourt taxi46 2',
            'Forecourt shuttle bus46', 'Forecourt garden bench46 0',
            'Forecourt garden bench46 2', 'Forecourt streetlight46 1',
            'Forecourt streetlight46 2', 'Forecourt tree46 0', 'Forecourt tree46 1',
            'Concourse plant46 0'])
# Replanted across the road (asphalt x -68..-62), on the far verge.
REPLANT = dict(SM_AP_Tree=[(-71.2, -16.5, 23.0, 1.32), (-71.8, -4.0, -41.0, 1.18)],
               SM_AP_Streetlight=[(-68.9, -18.0, 180.0, 1.0), (-68.9, -8.0, 180.0, 1.0)])

R = dict(status='RUNNING', destroyed=[], missing=[], instances_removed=[], replanted=[],
         arrivals=None)


def flush(status=None):
    if status:
        R['status'] = status
    (HERE / 'Fix47.json').write_text(json.dumps(R, indent=1), encoding='utf-8')


def v(p):
    return u.Vector(p[0] * 100, -p[1] * 100, p[2] * 100)


def main():
    assert u.EditorLoadingAndSavingUtils.load_map(MAP)
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    EA = u.get_editor_subsystem(u.EditorActorSubsystem)
    actors = {}
    for a in EA.get_all_level_actors():
        try:
            actors[a.get_actor_label()] = a
        except Exception:
            continue

    # 1 + 3. Destroy the duplicates and the alcove plant.
    for n in DESTROY:
        a = actors.get(n)
        if a is None:
            R['missing'].append(n)
            continue
        EA.destroy_actor(a)
        R['destroyed'].append(n)
    flush()

    # 2. Remove the instances under the canopy, remembering their look.
    host = actors['Airport instanced architecture and fittings']
    looks = {}
    for c in host.get_components_by_class(u.InstancedStaticMeshComponent):
        m = c.get_editor_property('static_mesh')
        if m is None or m.get_name() not in REPLANT:
            continue
        looks[m.get_name()] = (m, [c.get_material(i) for i in range(c.get_num_materials())])
        doomed = []
        for i in range(c.get_instance_count()):
            t = c.get_instance_transform(i, True)
            x, y = t.translation.x / 100, -t.translation.y / 100
            if CANOPY[0] <= x <= CANOPY[1] and CANOPY[2] <= y <= CANOPY[3]:
                doomed.append((i, round(x, 2), round(y, 2)))
        for i, x, y in sorted(doomed, reverse=True):
            c.remove_instance(i)
            R['instances_removed'].append(dict(mesh=m.get_name(), at=[x, y]))
    flush()

    # Replant across the road.
    for mesh_name, spots in REPLANT.items():
        mesh, mats = looks[mesh_name]
        for k, (x, y, yaw, s) in enumerate(spots):
            a = EA.spawn_actor_from_class(u.StaticMeshActor, v((x, y, 0.0)), u.Rotator(0, 0, -yaw))
            label = 'Verge %s47 %d' % ('tree' if 'Tree' in mesh_name else 'streetlight', k)
            a.set_actor_label(label)
            a.set_folder_path('Airport38/Pass47/Forecourt')
            a.set_actor_scale3d(u.Vector(s, s, s))
            c = a.static_mesh_component
            c.set_static_mesh(mesh)
            for i, m in enumerate(mats):
                if m:
                    c.set_material(i, m)
            c.set_mobility(u.ComponentMobility.STATIC)
            c.set_collision_enabled(u.CollisionEnabled.QUERY_AND_PHYSICS)
            c.set_collision_profile_name('BlockAll')
            o, e = a.get_actor_bounds(False)
            R['replanted'].append(dict(actor=label, mesh=mesh_name, at=[x, y], yaw=yaw, scale=s,
                                       top_m=round((o.z + e.z) / 100, 2)))
    flush()

    # 4. Arrivals screen texture and material.
    dep_tex = u.load_asset(SCREENS + '/T_AP_UI38_Departures')
    t = u.AssetImportTask()
    t.filename = str(HERE / 'DisplayArt' / 'T_AP_UI38_Arrivals.png')
    t.destination_path = SCREENS; t.destination_name = 'T_AP_UI38_Arrivals'
    t.automated = True; t.replace_existing = True; t.save = True
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    tex = u.load_asset(SCREENS + '/T_AP_UI38_Arrivals')
    copied = {}
    for prop in ('compression_settings', 'srgb', 'mip_gen_settings', 'lod_group', 'filter'):
        try:
            val = dep_tex.get_editor_property(prop)
            tex.set_editor_property(prop, val)
            copied[prop] = str(val)
        except Exception:
            pass
    u.EditorAssetLibrary.save_loaded_asset(tex)
    mi_path = SCREENS + '/MI_AP_UI38_Arrivals'
    if not u.EditorAssetLibrary.does_asset_exist(mi_path):
        u.EditorAssetLibrary.duplicate_asset(SCREENS + '/MI_AP_UI38_Departures', mi_path)
    mi = u.load_asset(mi_path)
    u.MaterialEditingLibrary.set_material_instance_texture_parameter_value(mi, 'ScreenImage', tex)
    u.EditorAssetLibrary.save_loaded_asset(mi)
    R['arrivals'] = dict(texture=tex.get_path_name(), material=mi.get_path_name(),
                         settings_from_departures=copied,
                         image=u.MaterialEditingLibrary.get_material_instance_texture_parameter_value(mi, 'ScreenImage').get_name())
    flush()

    assert u.EditorLoadingAndSavingUtils.save_map(world, MAP), 'save_map failed'
    flush('SUCCESS')
    print('FIX47 SUCCESS destroyed=%d removed=%d replanted=%d' % (
        len(R['destroyed']), len(R['instances_removed']), len(R['replanted'])), flush=True)


try:
    main()
except Exception:
    R['error'] = traceback.format_exc()
    flush('ERROR')
    raise
