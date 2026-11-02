"""Pass45: import the jetbridge closure panels and place them on the bridge.

Imports the 11 panel FBXs, assigns the project's existing MI_AP_P38B*
materials rather than FBX-embedded copies, places each at its authored world
transform, and attaches it to the bridge part it closes using KEEP_WORLD so no
transform is applied twice and the panel follows the deployed pose.

Collision is set to UseComplexAsSimple, matching the rest of the bridge
assets, so the panel blocks shape sweeps and traces alike.

Idempotent: a re-run destroys the previously spawned Pass45 closure actors
before placing fresh ones.
"""
import unreal as u, json, time, math, traceback
from pathlib import Path

R = Path(__file__).resolve().parents[1]
B = '/Game/Airport38'
MAP = B + '/L_Airport_Repair38'
MESH_DIR = B + '/Pass45Meshes'
MAT_DIR = B + '/Materials'
ACTOR_PREFIX = 'P45 bridge closure '

PARENT_FOR = {
    'Bridge38 cab mitre': 'Bridge38 cab mitre',
    'Bridge38 pivot': 'Bridge38 pivot chamber',
    'Bridge38 elbow': 'Bridge38 elbow chamber',
    'Bridge38 docking cab': 'Bridge38 docking cab',
    'Bridge38 terminal neck': 'Bridge38 terminal neck',
}
SLEEVE_PREFIX = {'Bridge38 bank A': 'Bridge38 bank A sleeve ',
                 'Bridge38 bank B': 'Bridge38 bank B sleeve '}

report = dict(status='RUNNING', started=time.time(), imported=[], placed=[], notes=[])


def flush():
    out = R / 'Pass45'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'ImportClosure45.json').write_text(json.dumps(report, indent=2), encoding='utf-8')


def prop(o, **kw):
    for k, v in kw.items():
        o.set_editor_property(k, v)


def v(p):
    return u.Vector(p[0] * 100.0, -p[1] * 100.0, p[2] * 100.0)


try:
    build = json.loads((R / 'Pass45' / 'Closure45Build.json').read_text(encoding='utf-8'))
    panels = build['panels']

    assert u.EditorLoadingAndSavingUtils.load_map(MAP), 'could not load ' + MAP
    EA = u.get_editor_subsystem(u.EditorActorSubsystem)
    AT = u.AssetToolsHelpers.get_asset_tools()

    mats = {}
    for key in ('Shell', 'Teal', 'Glass', 'Trim', 'Steel'):
        path = MAT_DIR + '/MI_AP_P38B' + key
        m = u.load_asset(path)
        if m is None:
            report['notes'].append('missing material ' + path)
        mats['MI_AP_P38B' + key] = m

    # remove any previous Pass45 closure actors, so this can be re-run
    removed = []
    for a in list(EA.get_all_level_actors()):
        if a.get_actor_label().startswith(ACTOR_PREFIX):
            removed.append(a.get_actor_label())
            EA.destroy_actor(a)
    report['removed_previous'] = removed

    actors = {a.get_actor_label(): a for a in EA.get_all_level_actors()}

    # Batch import, with native38.py's exact flags. Blender writes Z-up metres
    # with no axis conversion, so the scene is not converted and only units are.
    tasks = []
    for p in panels:
        t = u.AssetImportTask()
        # The build script recorded paths relative to Pass45; the engine's cwd
        # is elsewhere, so resolve them here.
        fbx = Path(p['fbx'])
        if not fbx.is_absolute():
            fbx = (R / 'Pass45' / fbx).resolve()
        p['fbx'] = str(fbx)
        prop(t, filename=str(fbx), destination_path=MESH_DIR,
             destination_name=p['asset'], automated=True, save=True,
             replace_existing=True)
        o = u.FbxImportUI()
        prop(o, import_mesh=True, import_as_skeletal=False, import_materials=False,
             import_textures=False, automated_import_should_detect_type=False,
             mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH)
        prop(o.static_mesh_import_data, combine_meshes=True,
             auto_generate_collision=False, reorder_material_to_fbx_order=True,
             convert_scene=False, convert_scene_unit=True,
             normal_import_method=u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS)
        t.set_editor_property('options', o)
        tasks.append(t)
    AT.import_asset_tasks(tasks)

    S_IMPORTED = {}
    for p in panels:
        pkg2 = MESH_DIR + '/' + p['asset']
        m2 = u.load_asset(pkg2)
        if m2 is not None:
            b = m2.get_bounding_box()
            S_IMPORTED[p['asset']] = m2
            report['imported'].append(dict(
                asset=p['asset'], package=pkg2,
                bounds_cm=[round(b.max.x - b.min.x, 1), round(b.max.y - b.min.y, 1),
                           round(b.max.z - b.min.z, 1)],
                expected_cm=[round(p['length_m'] * 100, 1), None,
                             round(p['height_m'] * 100, 1)]))
        else:
            report['notes'].append('load_asset returned None for ' + pkg2)
    flush()

    for p in panels:
        name = p['asset']
        pkg = MESH_DIR + '/' + name
        mesh = S_IMPORTED.get(name)
        if mesh is None:
            report['notes'].append('import failed ' + name)
            continue

        # project materials, not FBX copies
        slots = []
        for i, slot in enumerate(mesh.static_materials):
            key = str(slot.material_slot_name)
            target = None
            for mk, mv in mats.items():
                if mv is not None and (key == mk or key.startswith(mk)):
                    target = mv
                    break
            if target is not None:
                mesh.set_material(i, target)
            slots.append(dict(index=i, slot=key,
                              assigned=(target.get_name() if target else None)))

        try:
            bs = mesh.get_editor_property('body_setup')
            prop(bs, collision_trace_flag=u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        except Exception as e:
            report['notes'].append('collision flag %s: %s' % (name, e))
        u.EditorAssetLibrary.save_loaded_asset(mesh)
        report['placed_slots'] = report.get('placed_slots', []) + [dict(asset=name, slots=slots)]

        # place
        loc = v(p['world_centre'])
        # source yaw is about +Z in Blender space; Unreal Y is negated
        rot = u.Rotator(roll=0.0, pitch=0.0, yaw=-p['yaw_degrees'])
        actor = EA.spawn_actor_from_class(u.StaticMeshActor, loc, rot)
        label = ACTOR_PREFIX + '%02d' % p['index']
        actor.set_actor_label(label)
        actor.set_folder_path('Airport38/Pass45/BridgeClosure')
        c = actor.static_mesh_component
        c.set_static_mesh(mesh)
        c.set_mobility(u.ComponentMobility.MOVABLE)
        c.set_collision_enabled(u.CollisionEnabled.QUERY_AND_PHYSICS)
        c.set_collision_profile_name('BlockAll')

        parent_label = PARENT_FOR.get(p['part'])
        if parent_label is None:
            pref = SLEEVE_PREFIX.get(p['part'])
            best, bestd = None, 1e9
            if pref:
                for lbl, a in actors.items():
                    if not lbl.startswith(pref):
                        continue
                    d = (a.get_actor_location() - loc).length()
                    if d < bestd:
                        best, bestd = lbl, d
            parent_label = best
        parent = actors.get(parent_label) if parent_label else None
        if parent is not None:
            actor.attach_to_actor(parent, u.Name('None'),
                                  u.AttachmentRule.KEEP_WORLD,
                                  u.AttachmentRule.KEEP_WORLD,
                                  u.AttachmentRule.KEEP_WORLD, False)
        else:
            report['notes'].append('no parent for ' + label)

        report['placed'].append(dict(
            actor=label, asset=name, part=p['part'],
            parent=parent_label, world_centre=p['world_centre'],
            yaw_degrees=p['yaw_degrees'], length_m=p['length_m']))

    assert u.EditorLoadingAndSavingUtils.save_map(
        u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world(), MAP), 'save failed'

    report.update(status='SUCCESS', map=MAP, finished=time.time(),
                  summary=dict(imported=len(report['imported']),
                               placed=len(report['placed'])))
    flush()
    print('CLOSURE45 IMPORT SUCCESS', flush=True)
except Exception:
    report.update(status='FAILED', error=traceback.format_exc())
    flush()
    raise
