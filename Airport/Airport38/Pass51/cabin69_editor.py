"""Pass69: the cabin lit like a cabin (-run=pythonscript). MUTATES AND SAVES the level and materials.

Player feedback on Pass68: the only light seems to come through the windows
and off the floor; the ceiling is patchy with shadows; some bins are light
sources themselves; the floor lines do not read as lights; shadows are harsh.
Reference: Dear Passengers, where buttons and panels are luminous and glow.

What this does (plane66_editor.py, run after it, builds the strips):
  cove     (rev 69d: 70 cd - at 260 the ceiling blew out to white and outshone the seats)
           the 24 'Cabin broad practical' rect lights on the bin top edges turn
           to wash UP onto the curved ceiling (pitch +40, inward), shadowless,
           barn-doored so none of it lands on the bin faces: the ceiling itself
           becomes the soft, glowing source, as in a real airliner
  bins     the glowing 'P58 cabin strip' bars on the bin edges are hidden in
           game (the cove light sits behind the lip, unseen)
  glow     MI_AP_P69CeilingGlow (centre ceiling strip), MI_AP_P69PathGlow (floor
           path diffusers): emission high enough to bloom at EV 6.5
  grade    'P69 cabin grade', an unbound post-process volume at blend 0 that
           cabin68.py fades in while the camera is in the cabin: bloom so lit
           things glow, soft ambient occlusion so things sit on surfaces; neutral white
           balance (the terminal's 6900 K turned the cabin sepia), no flat
           ambient fill; priority 5000, above every room grade
  details  (rev 69c: reading lights stay skyward_runtime controls; cabin68.py
           gives their On state the glowing lens and switches ~40% on)
           rev 69b: reading lenses, read / call keys and indicators, seat-belt
           icons, galley indicators and lavatory lamps glow (per actor); ~40%
           of the reading lights are on, with their lenses lit; the carpet's
           white stitch line (it read as a light strip) takes the carpet colour
Originals of the cove lights are in Cabin69.orig.json; re-runnable.
"""
import unreal as u, json, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAP = '/Game/Airport38/L_Airport_Repair38'
DIR = '/Game/Airport38/Pass48/Materials'
MASTER = '/Game/Airport38/Materials/M_AP_Satin23'
ORIG = HERE / 'Cabin69.orig.json'
MATS = {'MI_AP_P69CeilingGlow': ((1.0, .95, .88), 60.0, .5), 'MI_AP_P69PathGlow': ((1.0, .86, .64), 260.0, .4),
        # luminous details (Dear Passengers). Rev 69e: at the level's fixed EV 6.5 on-screen = emission / ~110, so
        # anything meant to bloom (threshold 1.0) needs ~150+; rev 69b's 18-45 only read as pale paint
        'MI_AP_P69LensOn': ((1.0, .93, .8), 260.0, .3), 'MI_AP_P69LensOff': ((.95, .93, .9), 2.5, .3),
        'MI_AP_P69KeyRead': ((1.0, .9, .72), 110.0, .4), 'MI_AP_P69KeyCall': ((.3, .6, 1.0), 160.0, .4),
        'MI_AP_P69IndWarm': ((1.0, .78, .42), 240.0, .3), 'MI_AP_P69IndCall': ((.25, .55, 1.0), 260.0, .3),
        'MI_AP_P69SignIcon': ((1.0, .97, .9), 55.0, .4), 'MI_AP_P69Amber': ((1.0, .55, .12), 240.0, .3),
        'MI_AP_P69Green': ((.3, 1.0, .45), 240.0, .3), 'MI_AP_P69Sage': ((.55, 1.0, .7), 90.0, .3),
        'MI_AP_P69Lamp': ((1.0, .95, .85), 160.0, .3),
        'MI_AP_P70BinGlow': ((1.0, .93, .82), 150.0, .4)}           # Pass70: the visible source under every bin
COVE = dict(cd=300.0, pitch=-90.0, z=1.97, width=260.0, height=10.0, barn_angle=88.0, barn_length=8.0, temp=4000.0, att=520.0)
BIN_WORDS = ('Overhead bin', 'Rack', 'bin')                       # Pass70: each light sits just under its own bin
PANELS = ('Passenger service unit', 'PSU ', 'Centre PSU ceiling attachment')   # Pass70: hidden (player: remove them)
# rev 69f: no light from the ceiling at all - washed, its arches read as a rib cage. The same 24 lights now sit
# tucked under the bins' aisle edge, shining down onto seats and aisle (the under-bin wash of a real cabin)
GRADE = dict(bloom_intensity=.9, bloom_threshold=1.0, ambient_occlusion_intensity=.85, ambient_occlusion_radius=70.0,
             vignette_intensity=.25, white_temp=5200.0, ambient_cubemap_intensity=0.0,
             auto_exposure_min_brightness=6.0, auto_exposure_max_brightness=6.0)   # Pass70: 5.6 read harsh   # rev 69h: eyes adapt indoors (+0.9 EV
             # over the terminal's 6.5); a soft, direction-less stand-in for bounce so the bins and ceiling are not grey
GRADE_PRIORITY = 5000.0                                             # above every room grade (they top out at 1538)
READING_ON = .4                                                     # share of reading lights switched on: a lived-in cabin
# (mesh, slot material name, new material): per actor, only in the cabin; '/Name' = an existing material
SLOTS = [('SM_Plane_PSUReadKey12', 'MI_Plane_DetailInk12', 'MI_AP_P69KeyRead'),
         ('SM_Plane_PSUCallKey12', 'MI_Plane_DetailInk12', 'MI_AP_P69KeyCall'),
         ('SM_Plane_PSUReadIndicator12', 'MI_Plane_DetailWarm12', 'MI_AP_P69IndWarm'),
         ('SM_Plane_PSUCallIndicator12', 'MI_Plane_DetailCall12', 'MI_AP_P69IndCall'),
         ('SM_AP_A42PSUCarrier', 'MI_Plane_DetailInk12', 'MI_AP_P69SignIcon'),
         ('SM_Plane_Service12_Mid_lower_oven_heat_indicator', 'MI_Plane_SvcAmber12', 'MI_AP_P69Amber'),
         ('SM_Plane_Service12_Mid_upper_oven_heat_indicator', 'MI_Plane_SvcAmber12', 'MI_AP_P69Amber'),
         ('SM_Plane_Service12_Mid_coffee_brew_indicator', 'MI_Plane_SvcGreen12', 'MI_AP_P69Green'),
         ('SM_Plane_Service12_Mid_lower_oven_power', 'MI_Plane_SvcSage12', 'MI_AP_P69Sage'),
         ('SM_Plane_Service12_Mid_upper_oven_power', 'MI_Plane_SvcSage12', 'MI_AP_P69Sage'),
         ('SM_Plane_Service12_Mid_coffee_brew', 'MI_Plane_SvcSage12', 'MI_AP_P69Sage'),
         ('SM_Plane_Lavatory_L', 'MI_Plane_Lamp', 'MI_AP_P69Lamp'), ('SM_Plane_Lavatory_R', 'MI_Plane_Lamp', 'MI_AP_P69Lamp'),
         ('SM_Plane_Lavatory_L', 'MI_Plane_Footlight', 'MI_AP_P69Lamp'), ('SM_Plane_Lavatory_R', 'MI_Plane_Footlight', 'MI_AP_P69Lamp'),
         ('SM_Plane_FittedCarpet07', 'MI_Plane_Stitch09', '/MI_Plane_Carpet07')]   # the white stitch line read as a light
R = dict(status='RUNNING', mats=[], cove=[], hidden=[], grade=None, slots=[], reading=[])
BOX = ((12.9, -1.5, -0.6), (19.1, 30.5, 3.4))                       # source metres: the cabin at the gate
ML = u.MaterialEditingLibrary


def materials():
    master = u.load_asset(MASTER)
    if master is None:
        reg = u.AssetRegistryHelpers.get_asset_registry()
        master = next(a for a in reg.get_assets_by_class(u.TopLevelAssetPath('/Script/Engine', 'Material'), True)
                      if str(a.asset_name) == 'M_AP_Satin23').get_asset()
    tools = u.AssetToolsHelpers.get_asset_tools()
    for name, (rgb, emission, rough) in MATS.items():
        path = DIR + '/' + name
        mi = u.load_asset(path) if u.EditorAssetLibrary.does_asset_exist(path) else \
            tools.create_asset(name, DIR, u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
        ML.set_material_instance_parent(mi, master)
        ML.set_material_instance_vector_parameter_value(mi, 'BaseColor', u.LinearColor(*rgb, 1))
        ML.set_material_instance_scalar_parameter_value(mi, 'Emission', emission)
        ML.set_material_instance_scalar_parameter_value(mi, 'Roughness', rough)
        ML.update_material_instance(mi)
        assert u.EditorAssetLibrary.save_loaded_asset(mi)
        R['mats'].append([name, emission])


def bin_bottom(actors, p):
    """Lowest edge (UE z) of the overhead bin directly above UE point p, or None."""
    best = None
    for a in actors:
        lab = a.get_actor_label()
        if not isinstance(a, u.StaticMeshActor) or not any(w in lab for w in BIN_WORDS) or lab.startswith('P'):
            continue
        o, e = a.get_actor_bounds(False)
        if abs(o.x - p.x) <= e.x + 25 and abs(o.y - p.y) <= e.y + 12 and 150 < o.z - e.z < 240:   # +12: lights on bay seams
            z = o.z - e.z
            best = z if best is None else min(best, z)
    return best


def cove(actors):
    orig = json.loads(ORIG.read_text(encoding='utf-8')) if ORIG.exists() else {}
    cube = u.load_asset('/Engine/BasicShapes/Cube'); glow = u.load_asset(DIR + '/MI_AP_P70BinGlow')
    EA = u.get_editor_subsystem(u.EditorActorSubsystem)
    for a in actors:
        if a.get_actor_label().startswith('P70 cabin bin glow'):
            EA.destroy_actor(a)
    for a in actors:
        lab = a.get_actor_label()
        if not (isinstance(a, u.RectLight) and lab.startswith('Cabin broad practical')):
            continue
        c = a.get_component_by_class(u.RectLightComponent)
        p, r = a.get_actor_location(), a.get_actor_rotation()
        orig.setdefault(lab, dict(p=[p.x, p.y, p.z], rot=[r.roll, r.pitch, r.yaw], i=c.get_editor_property('intensity'),
                                  shadows=c.get_editor_property('cast_shadows')))
        o = orig[lab]
        inward = 0.0 if o['p'][0] < 1600 else 180.0                  # left bins face +x, right bins -x
        bottom = bin_bottom(actors, u.Vector(o['p'][0], o['p'][1], 200))
        z = (bottom - 1.5) if bottom else 215.0                         # no bin (the door bay): high, dimmer, no bar
        a.set_actor_location(u.Vector(o['p'][0], o['p'][1], z), False, False)
        R.setdefault('bins', []).append([lab, round(z / 100, 3), bottom is not None])
        c0 = a.get_component_by_class(u.RectLightComponent)
        if not bottom:
            c0.set_editor_property('intensity', COVE['cd'] * .4); c0.set_editor_property('cast_shadows', False)
            a.set_actor_rotation(u.Rotator(0, COVE['pitch'], 0 if o['p'][0] < 1600 else 180.0), False)
            continue
        g = EA.spawn_actor_from_class(u.StaticMeshActor, u.Vector(o['p'][0], o['p'][1], z + 1.0), u.Rotator(0, 0, 0))
        g.set_actor_label('P70 cabin bin glow ' + lab.replace('Cabin broad practical', '').strip('. ') or '0')
        g.tags = [u.Name('Skyward:P70 cabin bin glow'), u.Name('Airport38PlaneShift16')]; g.set_folder_path('Lighting/Pass70')
        m = g.static_mesh_component
        m.set_static_mesh(cube); m.set_material(0, glow); m.set_mobility(u.ComponentMobility.MOVABLE)
        m.set_collision_enabled(u.CollisionEnabled.NO_COLLISION); m.set_editor_property('cast_shadow', False)
        g.set_actor_scale3d(u.Vector(.035, COVE['width'] / 100 * .95, .006))
        a.set_actor_rotation(u.Rotator(0, COVE['pitch'], inward), False)       # straight down
        c.set_editor_property('intensity_units', u.LightUnits.CANDELAS)
        c.set_editor_property('intensity', COVE['cd'])
        c.set_editor_property('source_width', COVE['width'])
        c.set_editor_property('source_height', COVE['height'])
        c.set_editor_property('barn_door_angle', COVE['barn_angle'])
        c.set_editor_property('barn_door_length', COVE['barn_length'])
        c.set_editor_property('cast_shadows', True)                 # Pass70: the light visibly comes from the bin
        c.set_editor_property('use_temperature', True)
        c.set_editor_property('temperature', COVE['temp'])
        c.set_editor_property('attenuation_radius', COVE['att'])
        c.set_editor_property('specular_scale', .2)
        R['cove'].append(lab)
    ORIG.write_text(json.dumps(orig, indent=1), encoding='utf-8')


def grade(EA, actors):
    for a in actors:
        if a.get_actor_label() == 'P69 cabin grade':
            EA.destroy_actor(a)
    v = EA.spawn_actor_from_class(u.PostProcessVolume, u.Vector(1600, -1500, 150), u.Rotator(0, 0, 0))
    v.set_actor_label('P69 cabin grade'); v.set_folder_path('Lighting/Pass69')
    v.set_editor_property('unbound', True)
    v.set_editor_property('priority', GRADE_PRIORITY)
    v.set_editor_property('blend_weight', 0.0)                       # cabin68.py fades it in aboard
    s = v.get_editor_property('settings')
    for k, val in GRADE.items():
        s.set_editor_property('override_' + k, True)
        s.set_editor_property(k, val)
    v.set_editor_property('settings', s)
    R['grade'] = GRADE


def in_cabin(a):
    p = a.get_actor_location(); q = (p.x / 100, -p.y / 100, p.z / 100)
    return all(BOX[0][i] <= q[i] <= BOX[1][i] for i in range(3))


def luminous(actors, orig):
    """Per-actor material swaps that make the cabin's small things glow, and the reading lights."""
    mats = orig.setdefault('__materials', {})
    reg = u.AssetRegistryHelpers.get_asset_registry()

    def find(name):
        if name.startswith('/'):                                    # an existing material, by asset name
            return next((a.get_asset() for a in reg.get_assets_by_class(u.TopLevelAssetPath('/Script/Engine', 'MaterialInstanceConstant'), True)
                         if str(a.asset_name) == name[1:]), None)
        return u.load_asset(DIR + '/' + name)
    cache = {}
    for a in actors:                                                # rev 69c: the reading lights are skyward_runtime
        lab = a.get_actor_label()                                   # controls (E toggles them); cabin68.py switches some
        if isinstance(a, u.SpotLight) and 'light:' + lab in mats:   # on at run time. Undo rev 69b's level edits.
            a.get_component_by_class(u.LightComponent).set_editor_property('intensity', float(mats['light:' + lab]))
            R['reading'].append(lab)
    for a in actors:
        if not isinstance(a, u.StaticMeshActor) or not in_cabin(a):
            continue
        c = a.static_mesh_component; m = c.static_mesh if c else None
        if not m:
            continue
        lab = a.get_actor_label(); names = [str(n) for n in c.get_material_slot_names()]
        jobs = [(slot, new) for mesh, slot, new in SLOTS if mesh == m.get_name()]
        if m.get_name() == 'SM_AP_A42PSUCarrier':                   # the lens slot is the reading-light control's: restore it
            for i in range(c.get_num_materials()):
                orig_path = mats.get('%s|%d' % (lab, i))
                cur = c.get_material(i)
                if orig_path and cur and cur.get_name().startswith('MI_AP_P69Lens'):
                    c.set_material(i, u.load_asset(orig_path)); R.setdefault('restored', []).append(lab)
        for slot, new in jobs:
            idx = next((i for i, n in enumerate(names) if n.split('.')[0] == slot), None)
            if idx is None:
                continue
            mi = cache.get(new) or find(new); cache[new] = mi
            if mi is None:
                R.setdefault('notes', []).append('missing ' + new); continue
            key = '%s|%d' % (lab, idx)
            old = c.get_material(idx)
            mats.setdefault(key, old.get_path_name() if old else None)
            c.set_material(idx, mi)
            R['slots'].append([lab, slot, new])


try:
    materials()
    assert u.EditorLoadingAndSavingUtils.load_map(MAP)
    EA = u.get_editor_subsystem(u.EditorActorSubsystem)
    actors = EA.get_all_level_actors()
    cove(actors)
    orig = json.loads(ORIG.read_text(encoding='utf-8'))
    luminous(actors, orig)
    ORIG.write_text(json.dumps(orig, indent=1), encoding='utf-8')
    for a in actors:
        lab = a.get_actor_label()
        if lab.startswith('P58 cabin strip') and isinstance(a, u.StaticMeshActor):
            a.set_actor_hidden_in_game(True); R['hidden'].append(lab)
        elif lab.startswith(PANELS) and in_cabin(a):                    # Pass70: the overhead controls, gone
            a.set_actor_hidden_in_game(True); a.set_actor_enable_collision(False); R.setdefault('panels', []).append(lab)
    grade(EA, actors)
    assert u.EditorLoadingAndSavingUtils.save_current_level()
    R['status'] = 'SUCCESS'
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'Cabin69.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
print('CABIN69', R['status'])
