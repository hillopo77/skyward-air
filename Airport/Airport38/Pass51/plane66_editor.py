"""Pass66 (rev 68): very soft light strips in the aircraft cabin (-run=pythonscript).
MUTATES AND SAVES the level and two materials.

Heights come from Pass48/Ceil66.json (ceil66_probe.py, traced in -game: the
commandlet has no collision to trace against).

  ceiling  a strip above every aisle (two economy aisles, the business
           aisle), on the traced ceiling, in 4 m segments: a 5 cm warm glowing
           core (MI_AP_P66CabinStrip), a 34 cm soft halo either side
           (MI_AP_P66HaloCeiling) and a long, thin, dim rect light aimed down
  floor    path strips along both edges of each aisle runner, flush with the
           carpet: a soft 7 cm glow only (MI_AP_P66HaloFloor), no hard core and
           no lights (rev 67's white cores read as paint, and its centre-line
           up-lights drew a line down the aisle)
  halo     M_AP_P66Halo: unlit, additive, Colour x Strength x sin(pi U)^2 across
           and soft 8% fades at the ends, on the engine Plane (U across)
Rev 68: pieces overlap by their end fade, so each strip is one seamless line;
ceiling heights ignore window-wall and frame hits (aisle 17.105 had hung
0.46 m low on SM_Plane_WindowWall_R) and fall back to the mirror aisle;
ceiling lights cast shadows, so their light visibly comes from the strip.
Rev 69 (cabin69_editor.py runs first): the ceiling strip is the visible source of a
broad, soft, shadowless fill (FILL) that lights the seats from above; the floor
strips are real path-light fittings - a brushed channel with a glowing diffuser
that blooms, and a warm spill on the carpet.
Lights and fittings are MOVABLE and tagged 'Skyward:...' and
'Airport38PlaneShift16', so they fly with the aircraft. Re-runnable: earlier
'P66 cabin' actors are replaced.
"""
import unreal as u, json, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAP = '/Game/Airport38/L_Airport_Repair38'
MATDIR = '/Game/Airport38/Pass48/Materials'
CORE = MATDIR + '/MI_AP_P69CeilingGlow'                        # cabin69_editor.py makes these two
PATH = MATDIR + '/MI_AP_P69PathGlow'
FILL = dict(lm=3400.0, att=700.0, height=60.0, temp=4300.0)       # per piece: soft light from the ceiling strip
BOUNCE = dict(z=1.2, lm=600.0, att=320.0, height=60.0, temp=4200.0)   # Pass70: a faint trace; the light comes from the bins  # rev 69h: light bounced up off seats and carpet
CEILING = False                                                # rev 69f: the player wants no light source on the ceiling
CEIL = json.loads((HERE.parent / 'Pass48' / 'Ceil66.json').read_text(encoding='utf-8'))
AISLES = [(14.895, 12.6, 27.6, .33), (17.105, 12.6, 27.6, .33), (16.0, 3.6, 9.4, .70)]   # (centre x, y0, y1, floor strip offset):
                                                                                           # business: just inside the runner's cream trim (~0.79)
SKIP = ('WindowWall', 'frame', 'Lavatory', 'Exit')             # trace hits that are not the aisle ceiling
FADE = 12.0                                                    # M_AP_P66Halo end fade: 1/12 of a piece at each end
SEG = 4.0
R = dict(status='RUNNING', ceiling=[], floor=[], spawned=0)
ML = u.MaterialEditingLibrary


def ue(x, y, z):
    return u.Vector(x * 100, -y * 100, z * 100)


def heights(ax, y0, y1):
    """Median traced ceiling and floor over [y0, y1] for the aisle at ax; the cabin is symmetric
    about x 16, so an aisle whose ceiling traces all hit other things borrows its mirror's."""
    def row_of(x):
        return min(CEIL['aisles'], key=lambda a: abs(a[0] - x))
    def ceil(row):
        cs = sorted(c for y, c, lab in row[1] if c is not None and y0 - .01 <= y <= y1 + .01 and c < 3.4
                    and not any(k in (lab or '') for k in SKIP))
        return cs[len(cs) // 2] if cs else None
    row = row_of(ax)
    c = ceil(row)
    if c is None and abs(ax - 16.0) > .5:
        c = ceil(row_of(32.0 - ax))
    fs = sorted(f for y, f in row[2] if f is not None and y0 - .01 <= y <= y1 + .01 and -.2 < f < .3)
    return c, (fs[len(fs) // 2] if fs else .012)


def pieces(y0, y1):
    """Halo pieces over [y0, y1]: neighbours overlap by exactly one end fade, so the linear fades
    cross-fade to a constant and the strip reads as one line. Yields (centre y, length)."""
    n = max(1, round((y1 - y0) / SEG))
    L = (y1 - y0) / (n - (n - 1) / FADE)
    for k in range(n):
        a = y0 + k * L * (1 - 1 / FADE)
        yield a + L / 2, L


def halo_material():
    path = MATDIR + '/M_AP_P66Halo'
    if u.EditorAssetLibrary.does_asset_exist(path):
        u.EditorAssetLibrary.delete_asset(path)
    m = u.AssetToolsHelpers.get_asset_tools().create_asset('M_AP_P66Halo', MATDIR, u.Material, u.MaterialFactoryNew())
    m.set_editor_property('blend_mode', u.BlendMode.BLEND_ADDITIVE)
    m.set_editor_property('shading_model', u.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property('two_sided', True)

    def ex(cls, x, y, **kw):
        e = ML.create_material_expression(m, cls, x, y)
        for k, v in kw.items():
            e.set_editor_property(k, v)
        return e
    uv = ex(u.MaterialExpressionTextureCoordinate, -900, 0)
    mu = ex(u.MaterialExpressionComponentMask, -700, -60, r=True, g=False, b=False, a=False)
    mv = ex(u.MaterialExpressionComponentMask, -700, 80, r=False, g=True, b=False, a=False)
    ML.connect_material_expressions(uv, '', mu, ''); ML.connect_material_expressions(uv, '', mv, '')
    side = ex(u.MaterialExpressionSine, -550, -60, period=2.0)                 # sin(pi U)
    ML.connect_material_expressions(mu, '', side, '')
    sq = ex(u.MaterialExpressionMultiply, -400, -60)                           # squared: a soft falloff
    ML.connect_material_expressions(side, '', sq, 'A'); ML.connect_material_expressions(side, '', sq, 'B')
    k = ex(u.MaterialExpressionConstant, -700, 180, r=12.0)
    a1 = ex(u.MaterialExpressionMultiply, -550, 80)                            # min(1, 12V) * min(1, 12(1-V))
    ML.connect_material_expressions(mv, '', a1, 'A'); ML.connect_material_expressions(k, '', a1, 'B')
    s1 = ex(u.MaterialExpressionSaturate, -420, 80); ML.connect_material_expressions(a1, '', s1, '')
    om = ex(u.MaterialExpressionOneMinus, -700, 260); ML.connect_material_expressions(mv, '', om, '')
    a2 = ex(u.MaterialExpressionMultiply, -550, 260)
    ML.connect_material_expressions(om, '', a2, 'A'); ML.connect_material_expressions(k, '', a2, 'B')
    s2 = ex(u.MaterialExpressionSaturate, -420, 260); ML.connect_material_expressions(a2, '', s2, '')
    ends = ex(u.MaterialExpressionMultiply, -300, 160)
    ML.connect_material_expressions(s1, '', ends, 'A'); ML.connect_material_expressions(s2, '', ends, 'B')
    shape = ex(u.MaterialExpressionMultiply, -200, 0)
    ML.connect_material_expressions(sq, '', shape, 'A'); ML.connect_material_expressions(ends, '', shape, 'B')
    col = ex(u.MaterialExpressionVectorParameter, -400, -260, parameter_name='Colour', default_value=u.LinearColor(1, .82, .58, 1))
    st = ex(u.MaterialExpressionScalarParameter, -400, -160, parameter_name='Strength', default_value=.6)
    cs = ex(u.MaterialExpressionMultiply, -200, -200)
    ML.connect_material_expressions(col, '', cs, 'A'); ML.connect_material_expressions(st, '', cs, 'B')
    out = ex(u.MaterialExpressionMultiply, 0, -100)
    ML.connect_material_expressions(cs, '', out, 'A'); ML.connect_material_expressions(shape, '', out, 'B')
    ML.connect_material_property(out, '', u.MaterialProperty.MP_EMISSIVE_COLOR)
    ML.recompile_material(m)
    assert u.EditorAssetLibrary.save_loaded_asset(m)
    insts = {}
    for name, strength in (('MI_AP_P66HaloCeiling', .5), ('MI_AP_P66HaloFloor', 1.3)):
        p = MATDIR + '/' + name
        if u.EditorAssetLibrary.does_asset_exist(p):
            u.EditorAssetLibrary.delete_asset(p)
        mi = u.AssetToolsHelpers.get_asset_tools().create_asset(name, MATDIR, u.MaterialInstanceConstant,
                                                                u.MaterialInstanceConstantFactoryNew())
        ML.set_material_instance_parent(mi, m)
        ML.set_material_instance_scalar_parameter_value(mi, 'Strength', strength)
        assert u.EditorAssetLibrary.save_loaded_asset(mi)
        insts[name] = mi
    return insts


def tag(a, name):
    a.tags = [u.Name('Skyward:' + name), u.Name('Airport38PlaneShift16')]
    a.set_folder_path('Lighting/Pass66')


def piece(EA, mesh, mat, label, x, y, z, scale, rot=u.Rotator(0, 0, 0)):
    s = EA.spawn_actor_from_class(u.StaticMeshActor, ue(x, y, z), rot)
    s.set_actor_label(label); tag(s, label)
    m = s.static_mesh_component
    m.set_static_mesh(mesh); m.set_material(0, mat)
    m.set_mobility(u.ComponentMobility.MOVABLE)
    m.set_collision_profile_name('NoCollision')
    m.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
    m.set_editor_property('cast_shadow', False)
    s.set_actor_scale3d(scale)
    R['spawned'] += 1


def light(EA, label, x, y, z, up, length, lm, att, temp=3700, height=6.0, shadows=True):
    """A long rect light along the strip; a wide, shadowless one reads as soft light from the ceiling."""
    a = EA.spawn_actor_from_class(u.RectLight, ue(x, y, z), u.Rotator(0, 90 if up else -90, 0))
    a.set_actor_label(label); tag(a, label)
    c = a.get_component_by_class(u.RectLightComponent)
    c.set_mobility(u.ComponentMobility.MOVABLE)
    c.set_editor_property('intensity_units', u.LightUnits.LUMENS)
    c.set_editor_property('intensity', float(lm))
    c.set_editor_property('use_temperature', True)
    c.set_editor_property('temperature', float(temp))
    c.set_editor_property('attenuation_radius', float(att))
    c.set_editor_property('source_width', float(length * 100))
    c.set_editor_property('source_height', float(height))
    c.set_editor_property('cast_shadows', bool(shadows))
    c.set_editor_property('specular_scale', .3)
    R['spawned'] += 1


def main():
    assert CEIL.get('status') == 'SUCCESS', 'run ceil66_probe.py first'
    halos = halo_material()
    assert u.EditorLoadingAndSavingUtils.load_map(MAP)
    EA = u.get_editor_subsystem(u.EditorActorSubsystem)
    for a in EA.get_all_level_actors():
        if a.get_actor_label().startswith('P66 cabin'):
            EA.destroy_actor(a)
    cube = u.load_asset('/Engine/BasicShapes/Cube')
    plane = u.load_asset('/Engine/BasicShapes/Plane')
    core = u.load_asset(CORE); glow = u.load_asset(PATH)
    reg = u.AssetRegistryHelpers.get_asset_registry()
    mics = {str(a.asset_name): a for a in reg.get_assets_by_class(u.TopLevelAssetPath('/Script/Engine', 'MaterialInstanceConstant'), True)
            if str(a.asset_name) in ('MI_AP_P27Steel', 'MI_Plane_Carpet07')}
    steel = mics['MI_AP_P27Steel'].get_asset(); carpet = mics['MI_Plane_Carpet07'].get_asset()
    assert cube and plane and core and glow and steel and carpet
    flip = u.Rotator(180, 0, 0)                                    # a ceiling halo faces down
    for i, (ax, y0, y1, off) in enumerate(AISLES):
        zc, zf = heights(ax, y0, y1)
        R['ceiling'].append([i, zc]); R['floor'].append([i, zf, off])
        if zc is not None and CEILING:                              # the glowing core is one unbroken bar
            piece(EA, cube, core, 'P66 cabin ceiling strip %d' % i, ax, (y0 + y1) / 2, zc - .006, u.Vector(.05, y1 - y0, .012))
        for k, (yc, L) in enumerate(pieces(y0, y1)):
            if zc is not None and CEILING:
                piece(EA, plane, halos['MI_AP_P66HaloCeiling'], 'P66 cabin ceiling halo %d%02d' % (i, k), ax, yc, zc - .004,
                      u.Vector(.34, L, 1), flip)
                light(EA, 'P66 cabin ceiling light %d%02d' % (i, k), ax, yc, zc - .03, False, L * (1 - 1 / FADE), FILL['lm'],
                      FILL['att'], FILL['temp'], FILL['height'], False)
            light(EA, 'P66 cabin bounce light %d%02d' % (i, k), ax, yc, zf + BOUNCE['z'], True, L * (1 - 1 / FADE), BOUNCE['lm'],
                  BOUNCE['att'], BOUNCE['temp'], BOUNCE['height'], False)  # from below: lights the ceiling evenly, rakes no ribs
            for dx in (-off, off):                                  # the warm spill the fitting throws on the carpet
                piece(EA, plane, halos['MI_AP_P66HaloFloor'], 'P66 cabin floor halo %d%02d%s' % (i, k, 'L' if dx < 0 else 'R'),
                      ax + dx, yc, zf + .0045, u.Vector(.22, L, 1))
        if off < .5:                                                # rev 69e: the economy carpet has a pale line down the aisle
            piece(EA, plane, carpet, 'P66 cabin floor seam cover %d' % i, ax, (y0 + y1) / 2, zf + .0015,   # centre that reads as
                  u.Vector(.035, y1 - y0, 1))                                                             # a light: cover it
        for dx in (-off, off):                                      # the fitting: a low brushed channel, a glowing diffuser
            side = 'L' if dx < 0 else 'R'
            piece(EA, cube, steel, 'P66 cabin floor channel %d%s' % (i, side), ax + dx, (y0 + y1) / 2, zf + .004,
                  u.Vector(.026, y1 - y0, .008))
            piece(EA, cube, glow, 'P66 cabin floor diffuser %d%s' % (i, side), ax + dx, (y0 + y1) / 2, zf + .0085,
                  u.Vector(.012, y1 - y0 - .02, .002))
    assert u.EditorLoadingAndSavingUtils.save_current_level()
    R['status'] = 'SUCCESS'


try:
    main()
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'Plane66.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
print('PLANE66', R['status'])
