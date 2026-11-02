"""Pass72: the cabin glows, the cockpit buttons glow in their colours, and a red panic line (-run=pythonscript).
MUTATES AND SAVES the level and materials. Run after cabin69_editor.py and plane66_editor.py.

Player brief: lights really glowy, and the surroundings glow with the colour of the light; in the
cockpit the green and red buttons shine onto the panels around them. Another line of lights at
the top of the plane, identical to the floor ones, off - and when there is panic in the plane they
turn on, panicky red, while the floor ones stay on at a lower white.

  panic line   along both edges of every aisle at the ceiling (economy +-0.33 m, business +-0.70 m),
               the same channel + diffuser as the floor path lights, facing down; 'P72 cabin panic
               strip *' (diffuser, dark) and 'P72 cabin panic light *' (red rect lights at 0). cabin68.py
               drives them: off normally; in a panic they pulse red and flood the cabin
  floor glow   a soft up-facing rect light along every floor path strip ('P72 cabin floor glow *'),
               so the carpet and the seat bases take the warm colour of the strip
  cockpit      the lit buttons glow onto the panel around them: a glowing collar in the button's colour
               just behind each one and a small point light of that colour just aft ('P72 cockpit
               collar / glow *'): green and red status pushlights, the two red emergency buttons
               (one is reject-takeoff, the panic trigger), amber side pushbuttons, the radar in phosphor
               green. The buttons' own materials are never swapped: skyward_runtime finds each
               control's slot by its material name, and a swap stops the game at start-up. Only
               MI_Plane_FunGreen10 / FunRed10, each used by one pushlight and nothing else, get more
               emission in the asset.
  grade        'P69 cabin grade' bloom 1.3 (threshold 0.8): lit things bloom into their surroundings
  ribs         the 13 'Cabin frame10 *' arch ribs across the ceiling are hidden, no collision (player: remove them)
"""
import unreal as u, json, math, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAP = '/Game/Airport38/L_Airport_Repair38'
DIR = '/Game/Airport38/Pass48/Materials'
MASTER = '/Game/Airport23/Materials/M_AP_Satin23'
CEIL = json.loads((HERE.parent / 'Pass48' / 'Ceil66.json').read_text(encoding='utf-8'))
AISLES = [(14.895, 12.6, 27.6, .33), (17.105, 12.6, 27.6, .33), (16.0, 3.6, 9.4, .70)]
MATS = {'MI_AP_P72PanicStrip': ((.12, .12, .13), 0.0, .3),           # dormant grey glass until cabin68 lights it red
        'MI_AP_P72GlowGreen': ((.25, 1.0, .35), 220.0, .3), 'MI_AP_P72GlowRed': ((1.0, .1, .06), 240.0, .3),
        'MI_AP_P72GlowAmber': ((1.0, .55, .1), 220.0, .3), 'MI_AP_P72GlowCyan': ((.2, .8, 1.0), 120.0, .3),
        'MI_AP_P72GlowWhite': ((1.0, .96, .9), 160.0, .3)}
COLOURS = {'green': (.25, 1.0, .35), 'red': (1.0, .1, .06), 'amber': (1.0, .55, .1), 'cyan': (.2, .8, 1.0), 'white': (1.0, .96, .9)}
R = dict(status='RUNNING', panic=0, floor=0, cockpit=[])
ML = u.MaterialEditingLibrary


def ue(x, y, z):
    return u.Vector(x * 100, -y * 100, z * 100)


def ceiling(ax):
    def row_of(x):
        return min(CEIL['aisles'], key=lambda a: abs(a[0] - x))
    for x in (ax, 32.0 - ax):
        cs = sorted(c for y, c, lab in row_of(x)[1] if c is not None and c < 3.4 and not any(k in (lab or '') for k in ('WindowWall', 'frame', 'Lavatory', 'Exit')))
        if cs:
            return cs[len(cs) // 2]
    return 2.86


def materials():
    master = u.load_asset(MASTER)
    if master is None:
        reg = u.AssetRegistryHelpers.get_asset_registry()
        master = next(a for a in reg.get_assets_by_class(u.TopLevelAssetPath('/Script/Engine', 'Material'), True)
                      if str(a.asset_name) == 'M_AP_Satin23').get_asset()
    tools = u.AssetToolsHelpers.get_asset_tools()
    out = {}
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
        out[name] = mi
    return out


def tag(a, name, folder='Lighting/Pass72'):
    a.tags = [u.Name('Skyward:' + name), u.Name('Airport38PlaneShift16')]
    a.set_folder_path(folder)


def piece(EA, mesh, mat, label, at, scale):
    s = EA.spawn_actor_from_class(u.StaticMeshActor, at, u.Rotator(0, 0, 0))
    s.set_actor_label(label); tag(s, label)
    m = s.static_mesh_component
    m.set_static_mesh(mesh); m.set_material(0, mat); m.set_mobility(u.ComponentMobility.MOVABLE)
    m.set_collision_enabled(u.CollisionEnabled.NO_COLLISION); m.set_editor_property('cast_shadow', False)
    s.set_actor_scale3d(scale)
    return s


def rect(EA, label, at, pitch, length, lm, att, colour, temp=None):
    a = EA.spawn_actor_from_class(u.RectLight, at, u.Rotator(0, pitch, 0))
    a.set_actor_label(label); tag(a, label)
    c = a.get_component_by_class(u.RectLightComponent)
    c.set_mobility(u.ComponentMobility.MOVABLE)
    c.set_editor_property('intensity_units', u.LightUnits.LUMENS)
    c.set_editor_property('intensity', float(lm))
    c.set_editor_property('light_color', u.Color(r=int(colour[0] * 255), g=int(colour[1] * 255), b=int(colour[2] * 255), a=255))
    if temp:
        c.set_editor_property('use_temperature', True); c.set_editor_property('temperature', float(temp))
    c.set_editor_property('attenuation_radius', float(att))
    c.set_editor_property('source_width', float(length * 100)); c.set_editor_property('source_height', 4.0)
    c.set_editor_property('cast_shadows', False); c.set_editor_property('specular_scale', .4)
    return a


LIT = {'Cockpit status pushlight 112': 'green', 'Cockpit status pushlight 212': 'red',
       'Cockpit emergency test 112': 'red', 'Cockpit emergency test 212': 'red',
       **{'Cockpit side pushbutton 0%d12' % i: 'amber' for i in range(1, 7)}}
LIGHT_CD = {'green': 8.0, 'red': 8.0, 'amber': 2.5, 'cyan': 4.0}
EXCLUSIVE = {'MI_Plane_FunGreen10': 260.0, 'MI_Plane_FunRed10': 260.0}
COCKPIT_CENTRE = (16.0, -3.5, 1.4)


def glow_light(EA, label, at, colour, cd, att):
    L = EA.spawn_actor_from_class(u.PointLight, at, u.Rotator(0, 0, 0))
    L.set_actor_label(label); tag(L, label)
    pc = L.get_component_by_class(u.PointLightComponent)
    pc.set_mobility(u.ComponentMobility.MOVABLE)
    pc.set_editor_property('intensity_units', u.LightUnits.CANDELAS)
    pc.set_editor_property('intensity', cd)
    rgb = COLOURS[colour]
    pc.set_editor_property('light_color', u.Color(r=int(rgb[0] * 255), g=int(rgb[1] * 255), b=int(rgb[2] * 255), a=255))
    pc.set_editor_property('attenuation_radius', att); pc.set_editor_property('source_radius', 1.5)
    pc.set_editor_property('cast_shadows', False); pc.set_editor_property('specular_scale', .6)


def cockpit(EA, mats, cube):
    for name, emission in EXCLUSIVE.items():
        mi = next((a.get_asset() for a in u.AssetRegistryHelpers.get_asset_registry().get_assets_by_class(
            u.TopLevelAssetPath('/Script/Engine', 'MaterialInstanceConstant'), True) if str(a.asset_name) == name), None)
        if mi and 'Emission' in [str(n) for n in ML.get_scalar_parameter_names(mi)]:
            before = ML.get_material_instance_scalar_parameter_value(mi, 'Emission')
            ML.set_material_instance_scalar_parameter_value(mi, 'Emission', emission); ML.update_material_instance(mi)
            u.EditorAssetLibrary.save_loaded_asset(mi); R['cockpit'].append([name, 'emission', before, emission])
    acts = {a.get_actor_label(): a for a in EA.get_all_level_actors()}
    for lab, colour in LIT.items():
        a = acts.get(lab)
        if a is None:
            R['cockpit'].append([lab, 'missing']); continue
        o, e = a.get_actor_bounds(False)                                  # UE cm; source = (x, -y, z)
        c = (o.x / 100, -o.y / 100, o.z / 100); ext = (e.x / 100, e.y / 100, e.z / 100)
        ax = min(range(3), key=lambda i: ext[i])                          # the button's thin axis = the panel normal
        out = (1 if c[0] > COCKPIT_CENTRE[0] else -1) if ax == 0 else -1  # panels face aft (nose side) or up; side panels outboard
        back = list(c); back[ax] = c[ax] + out * (ext[ax] + .002)        # just behind the button, on the panel
        size = [ext[i] * 2 + .035 for i in range(3)]; size[ax] = .003
        if colour != 'amber':                                             # square collars suit the square / plated buttons only
            piece(EA, cube, mats['MI_AP_P72Glow' + colour.capitalize()], 'P72 cockpit collar ' + lab, ue(*back),
                  u.Vector(size[0], size[1], size[2]))
        front = list(c); front[ax] = c[ax] - out * .07                    # 7 cm out in front of the panel
        glow_light(EA, 'P72 cockpit glow ' + lab, ue(*front), colour, LIGHT_CD[colour], 55.0 if colour != 'amber' else 35.0)
        R['cockpit'].append([lab, colour, [round(v, 3) for v in c], 'xyz'[ax], out])
    r = acts.get('Cockpit radar phosphor graphics12')
    if r:
        o, e = r.get_actor_bounds(False)
        glow_light(EA, 'P72 cockpit glow radar', u.Vector(o.x, o.y - 10.0, o.z), 'green', 4.0, 60.0)


def main():
    mats = materials()
    assert u.EditorLoadingAndSavingUtils.load_map(MAP)
    EA = u.get_editor_subsystem(u.EditorActorSubsystem)
    for a in EA.get_all_level_actors():
        if a.get_actor_label().startswith(('P72 cabin', 'P72 cockpit')):
            EA.destroy_actor(a)
    cube = u.load_asset('/Engine/BasicShapes/Cube')
    reg = u.AssetRegistryHelpers.get_asset_registry()
    steel = next(a.get_asset() for a in reg.get_assets_by_class(u.TopLevelAssetPath('/Script/Engine', 'MaterialInstanceConstant'), True)
                 if str(a.asset_name) == 'MI_AP_P27Steel')
    # the panic line at the ceiling, identical in build to the floor path lights; and the floor glow
    for i, (ax, y0, y1, off) in enumerate(AISLES):
        zc, yc, L = ceiling(ax), (y0 + y1) / 2, y1 - y0
        for dx in (-off, off):
            side = 'L' if dx < 0 else 'R'
            piece(EA, cube, steel, 'P72 cabin panic channel %d%s' % (i, side), ue(ax + dx, yc, zc - .004), u.Vector(.026, L, .008))
            piece(EA, cube, mats['MI_AP_P72PanicStrip'], 'P72 cabin panic strip %d%s' % (i, side), ue(ax + dx, yc, zc - .0085),
                  u.Vector(.012, L - .02, .002))
            rect(EA, 'P72 cabin panic light %d%s' % (i, side), ue(ax + dx, yc, zc - .03), -90, L, 0.0, 420, (1.0, .06, .04))
            rect(EA, 'P72 cabin floor glow %d%s' % (i, side), ue(ax + dx, yc, .03), 90, L, 140.0, 110, (1.0, .82, .6), temp=3600)
            R['panic'] += 1; R['floor'] += 1
    cockpit(EA, mats, cube)
    for a in EA.get_all_level_actors():                                 # the player: remove the bars across the ceiling
        if isinstance(a, u.StaticMeshActor) and a.get_actor_label().startswith('Cabin frame10 ') and                 a.static_mesh_component.static_mesh and 'ArchRib' in a.static_mesh_component.static_mesh.get_name():
            a.modify(); a.set_actor_hidden_in_game(True); a.set_actor_enable_collision(False)
            a.set_editor_property('hidden', True)
            R['ribs_hidden'] = R.get('ribs_hidden', 0) + 1
    for v in EA.get_all_level_actors():                                 # bloom: lit things glow into their surroundings
        if v.get_actor_label() == 'P69 cabin grade':
            s = v.get_editor_property('settings')
            for k, val in (('bloom_intensity', 1.3), ('bloom_threshold', .8)):
                s.set_editor_property('override_' + k, True); s.set_editor_property(k, val)
            v.set_editor_property('settings', s)
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    assert u.EditorLoadingAndSavingUtils.save_map(world, MAP), 'save failed'
    R['status'] = 'SUCCESS'


try:
    main()
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'Cabin72.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
print('CABIN72', R['status'])
