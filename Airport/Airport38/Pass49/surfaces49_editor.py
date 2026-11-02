"""Pass49: real materials outdoors, limewash walls, Skyward carpet on the gallery.

(-run=pythonscript.) Imports the Pass49 maps and builds M_AP_Ground49, a
world-projected (tri-planar) finish: colour + roughness from one packed map
at TileMetres, blended across the three world planes by the surface normal,
times a very soft large-scale MacroVariation so no map reads as a repeat.
It needs no UVs, so it suits the airfield, the pavements, the roads and the
roof, whose meshes have none at a usable scale.

Every material listed in Surfaces49.json is resolved from the level (by its
name on any actor's slot, so every asset of that name in use is caught) and
re-parented in place, so nothing is rebound:
  ground   onto M_AP_Ground49, tinted by its old BaseColor over the map's
           mean colour (Textures49.json), so each keeps its colour and
           gains texture; Specular carried over
  finish   onto M_AP_Finish48 (UV0 metres), the limewash plaster maps
The level is loaded only to read it and is not saved. MUTATES AND SAVES
assets; the caller backs them up first.
"""
import unreal as u, json, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEST = '/Game/Airport38/Pass49'
MAP = '/Game/Airport38/L_Airport_Repair38'
R = dict(status='RUNNING', textures=[], instances=[])
AT = u.AssetToolsHelpers.get_asset_tools()
EA = u.EditorAssetLibrary
ML = u.MaterialEditingLibrary


def import_textures(names):
    tasks = []
    for name in names:
        t = u.AssetImportTask()
        for k, v in dict(filename=str(HERE / 'Textures' / (name + '.png')), destination_path=DEST + '/Textures',
                         destination_name='T_AP_' + name, automated=True, save=True, replace_existing=True).items():
            t.set_editor_property(k, v)
        tasks.append(t)
    AT.import_asset_tasks(tasks)
    tex = {}
    for name in names:
        a = u.load_asset(DEST + '/Textures/T_AP_' + name)
        assert a, name
        a.set_editor_property('srgb', name != 'Macro49')
        a.set_editor_property('address_x', u.TextureAddress.TA_WRAP)
        a.set_editor_property('address_y', u.TextureAddress.TA_WRAP)
        a.set_editor_property('mip_gen_settings', u.TextureMipGenSettings.TMGS_SIMPLE_AVERAGE)
        assert EA.save_loaded_asset(a)
        tex[name] = a
        R['textures'].append(a.get_path_name())
    return tex


def build_master(tex):
    mpath = DEST + '/Materials/M_AP_Ground49'
    m = u.load_asset(mpath) or AT.create_asset('M_AP_Ground49', DEST + '/Materials', u.Material, u.MaterialFactoryNew())
    ML.delete_all_material_expressions(m)
    m.set_editor_property('blend_mode', u.BlendMode.BLEND_OPAQUE)
    m.set_editor_property('used_with_instanced_static_meshes', True)     # the lawn and kerbs are instanced

    def ex(cls, x, y, **props):
        n = ML.create_material_expression(m, cls, x, y)
        for k, v in props.items():
            n.set_editor_property(k, v)
        return n

    def link(a, out, b, inp):
        assert ML.connect_material_expressions(a, out, b, inp), (out, inp)

    def scalar(name, val, x, y):
        return ex(u.MaterialExpressionScalarParameter, x, y, parameter_name=name, default_value=val)

    def op(cls, a, b, x, y, oa='', ob=''):
        n = ex(cls, x, y)
        link(a, oa, n, 'A'); link(b, ob, n, 'B')
        return n

    def mask(src, x, y, out='', **ch):
        n = ex(u.MaterialExpressionComponentMask, x, y, **{k: (k in ch) for k in 'rgba'})
        link(src, out, n, '')
        return n

    def sample(name, t, uvs, x, y, stype):
        n = ex(u.MaterialExpressionTextureSampleParameter2D, x, y, parameter_name=name, texture=t, sampler_type=stype)
        link(uvs, '', n, 'UVs')
        return n

    wp = ex(u.MaterialExpressionWorldPosition, -2000, 0)
    tile = ex(u.MaterialExpressionMultiply, -1800, 200, const_b=100.0)
    link(scalar('TileMetres', 8.0, -2000, 200), '', tile, 'A')
    uvw = op(u.MaterialExpressionDivide, wp, tile, -1600, 0)
    col = u.MaterialSamplerType.SAMPLERTYPE_COLOR
    first = tex['Grass49']
    s_xy = sample('GroundColourRoughness', first, mask(uvw, -1400, -300, r=1, g=1), -1150, -300, col)
    s_xz = sample('GroundColourRoughness', first, mask(uvw, -1400, 0, r=1, b=1), -1150, 0, col)
    s_yz = sample('GroundColourRoughness', first, mask(uvw, -1400, 300, g=1, b=1), -1150, 300, col)
    # Tri-planar weights: |N|^4, normalised.
    nrm = ex(u.MaterialExpressionVertexNormalWS, -2000, 600)
    ab = ex(u.MaterialExpressionAbs, -1800, 600); link(nrm, '', ab, '')
    pw = ex(u.MaterialExpressionPower, -1600, 600, const_exponent=4.0); link(ab, '', pw, 'Base')
    one = ex(u.MaterialExpressionConstant3Vector, -1600, 750, constant=u.LinearColor(1, 1, 1, 1))
    tot = op(u.MaterialExpressionDotProduct, pw, one, -1400, 700)
    w = op(u.MaterialExpressionDivide, pw, tot, -1200, 600)
    w_z, w_y, w_x = mask(w, -1000, 550, b=1), mask(w, -1000, 650, g=1), mask(w, -1000, 750, r=1)

    def blend(out, y):
        a = op(u.MaterialExpressionMultiply, s_xy, w_z, -800, y, oa=out)
        b = op(u.MaterialExpressionMultiply, s_xz, w_y, -800, y + 100, oa=out)
        c = op(u.MaterialExpressionMultiply, s_yz, w_x, -800, y + 200, oa=out)
        return op(u.MaterialExpressionAdd, op(u.MaterialExpressionAdd, a, b, -650, y), c, -500, y)
    rgb = blend('RGB', -300)
    alpha = blend('A', 200)
    # Large-scale variation.
    mtile = ex(u.MaterialExpressionMultiply, -1800, 1000, const_b=100.0)
    link(scalar('MacroMetres', 70.0, -2000, 1000), '', mtile, 'A')
    muv = op(u.MaterialExpressionDivide, mask(wp, -1800, 900, r=1, g=1), mtile, -1600, 950)
    ms = sample('MacroVariation', tex['Macro49'], muv, -1400, 950, u.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
    lerp = ex(u.MaterialExpressionLinearInterpolate, -1100, 950)
    link(scalar('MacroLow', .88, -1300, 1100), '', lerp, 'A')
    link(scalar('MacroHigh', 1.12, -1300, 1200), '', lerp, 'B')
    link(ms, 'R', lerp, 'Alpha')
    tint = ex(u.MaterialExpressionVectorParameter, -500, -500, parameter_name='Tint', default_value=u.LinearColor(1, 1, 1, 1))
    base = op(u.MaterialExpressionMultiply, op(u.MaterialExpressionMultiply, rgb, tint, -300, -300), lerp, -150, -300)
    assert ML.connect_material_property(base, '', u.MaterialProperty.MP_BASE_COLOR)
    rough = op(u.MaterialExpressionMultiply, alpha, scalar('RoughnessScale', 1.0, -500, 400), -300, 200)
    assert ML.connect_material_property(rough, '', u.MaterialProperty.MP_ROUGHNESS)
    assert ML.connect_material_property(scalar('Metallic', 0.0, -300, 600), '', u.MaterialProperty.MP_METALLIC)
    assert ML.connect_material_property(scalar('Specular', .3, -300, 700), '', u.MaterialProperty.MP_SPECULAR)
    ML.recompile_material(m)
    assert EA.save_loaded_asset(m)
    R['master'] = m.get_path_name()
    return m


def level_instances(names):
    """Every MaterialInstanceConstant of a wanted name bound on any static mesh in the level."""
    assert u.EditorLoadingAndSavingUtils.load_map(MAP)
    found = {}
    for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
        for c in a.get_components_by_class(u.StaticMeshComponent):
            for k in range(c.get_num_materials()):
                mi = c.get_material(k)
                if isinstance(mi, u.MaterialInstanceConstant) and mi.get_name() in names:
                    found.setdefault(mi.get_name(), {})[mi.get_path_name()] = mi
    return found


def main():
    spec = json.loads((HERE / 'Surfaces49.json').read_text(encoding='utf-8'))
    means = json.loads((HERE / 'Textures49.json').read_text(encoding='utf-8'))
    tex = import_textures(sorted(means))
    ground = build_master(tex)
    finish = u.load_asset('/Game/Airport38/Pass48/Materials/M_AP_Finish48')
    assert finish
    extra = {k: u.load_asset(v) for k, v in spec.get('extra_textures', {}).items()}
    assert all(extra.values()), extra
    tex.update(extra)
    found = level_instances({s['mi'] for s in spec['ground']})
    R['missing'] = sorted({s['mi'] for s in spec['ground']} - set(found))
    for s in spec['ground']:
        for path, mi in found.get(s['mi'], {}).items():
            old_spec = ML.get_material_instance_scalar_parameter_value(mi, 'Specular')
            if 'tint' in s:
                tint = s['tint']
            else:
                bc = ML.get_material_instance_vector_parameter_value(mi, 'BaseColor')
                mean = means[s['texture']]
                tint = [min(2.5, max(.2, v / m * k)) for v, m, k in zip((bc.r, bc.g, bc.b), mean, s.get('tint_scale', (1, 1, 1)))]
            ML.set_material_instance_parent(mi, ground)
            ML.set_material_instance_texture_parameter_value(mi, 'GroundColourRoughness', tex[s['texture']])
            ML.set_material_instance_texture_parameter_value(mi, 'MacroVariation', tex['Macro49'])
            ML.set_material_instance_scalar_parameter_value(mi, 'TileMetres', float(s['tile']))
            ML.set_material_instance_vector_parameter_value(mi, 'Tint', u.LinearColor(*tint, 1))
            ML.set_material_instance_scalar_parameter_value(mi, 'Specular', float(s.get('Specular', old_spec or .3)))
            for p in ('RoughnessScale', 'MacroLow', 'MacroHigh', 'MacroMetres'):
                if p in s:
                    ML.set_material_instance_scalar_parameter_value(mi, p, float(s[p]))
            ML.update_material_instance(mi)
            assert EA.save_loaded_asset(mi)
            R['instances'].append(dict(s, mi=path, parent='M_AP_Ground49', tint=[round(t, 3) for t in tint]))
    for s in spec['finish']:
        mi = u.load_asset(s['path'])
        assert mi, s['path']
        ML.set_material_instance_parent(mi, finish)
        ML.set_material_instance_texture_parameter_value(mi, 'FinishColourRoughness', tex[s['texture']])
        ML.set_material_instance_scalar_parameter_value(mi, 'MetreUVScale', 1.0 / s['tile'])
        ML.set_material_instance_vector_parameter_value(mi, 'Tint', u.LinearColor(1, 1, 1, 1))
        ML.set_material_instance_scalar_parameter_value(mi, 'Specular', float(s.get('Specular', .27)))
        ML.update_material_instance(mi)
        assert EA.save_loaded_asset(mi)
        R['instances'].append(dict(s, parent='M_AP_Finish48'))
    R['status'] = 'SUCCESS'


try:
    main()
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'Surfaces49Report.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
print('SURFACES49', R['status'])
