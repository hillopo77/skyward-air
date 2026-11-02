"""Pass48 makeover: new surfaces for the whole terminal (-run=pythonscript).

Imports the Pass48 maps (textures48_blender.py) and builds one master,
M_AP_Finish48: the Finish43 contract (UV0 in metres x MetreUVScale, packed
colour + roughness) plus a Tint, a RoughnessScale, an Emissive lift and real
Specular/Metallic. The existing finish instances are re-parented onto it, so
every mesh already bound to them changes at once and nothing is rebound:

  MI_AP_P43TFloor    -> polished terrazzo with brass strips
  MI_AP_P43TCarpet   -> Skyward gate carpet
  MI_AP_P43TWC       -> 50 mm mosaic
  MI_AP_P43TCeiling  -> bright panelled acoustic ceiling, slight lift
  MI_AP_P43TDado     -> light-oak board wainscot (was flat slate)
  MI_AP_P43TOak      -> richer oak grain

Plaster stays as it is. The previous assets are backed up by the caller.
Values come from Surfaces48.json beside this file so they can be tuned
without editing code. MUTATES AND SAVES assets (not the level).
"""
import unreal as u, json, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEST = '/Game/Airport38/Pass48'
FIN = '/Game/Airport38/Finish43'
R = dict(status='RUNNING', textures=[], instances=[])


def main():
    spec = json.loads((HERE / 'Surfaces48.json').read_text(encoding='utf-8'))
    AT = u.AssetToolsHelpers.get_asset_tools()
    EA = u.EditorAssetLibrary
    ML = u.MaterialEditingLibrary
    tasks = []
    for name in sorted({s['texture'] for s in spec['instances'].values()}):
        t = u.AssetImportTask()
        for k, v in dict(filename=str(HERE / 'Textures' / (name + '.png')), destination_path=DEST + '/Textures',
                         destination_name='T_AP_' + name, automated=True, save=True, replace_existing=True).items():
            t.set_editor_property(k, v)
        tasks.append(t)
    AT.import_asset_tasks(tasks)
    tex = {}
    for t in tasks:
        name = t.get_editor_property('destination_name')
        a = u.load_asset(DEST + '/Textures/' + name)
        assert a, name
        a.set_editor_property('srgb', True)
        a.set_editor_property('address_x', u.TextureAddress.TA_WRAP)
        a.set_editor_property('address_y', u.TextureAddress.TA_WRAP)
        a.set_editor_property('mip_gen_settings', u.TextureMipGenSettings.TMGS_SIMPLE_AVERAGE)
        assert EA.save_loaded_asset(a)
        tex[name[5:]] = a
        R['textures'].append(a.get_path_name())

    # Master graph.
    mpath = DEST + '/Materials/M_AP_Finish48'
    m = u.load_asset(mpath) or AT.create_asset('M_AP_Finish48', DEST + '/Materials', u.Material, u.MaterialFactoryNew())
    ML.delete_all_material_expressions(m)
    m.set_editor_property('blend_mode', u.BlendMode.BLEND_OPAQUE)

    def ex(cls, x, y):
        return ML.create_material_expression(m, cls, x, y)

    def scalar(name, val, x, y):
        n = ex(u.MaterialExpressionScalarParameter, x, y)
        n.set_editor_property('parameter_name', name); n.set_editor_property('default_value', val)
        return n

    uv = ex(u.MaterialExpressionTextureCoordinate, -900, -200)
    mul = ex(u.MaterialExpressionMultiply, -650, -200)
    ML.connect_material_expressions(uv, '', mul, 'A')
    ML.connect_material_expressions(scalar('MetreUVScale', .5, -900, 0), '', mul, 'B')
    smp = ex(u.MaterialExpressionTextureSampleParameter2D, -420, -200)
    smp.set_editor_property('parameter_name', 'FinishColourRoughness')
    smp.set_editor_property('texture', next(iter(tex.values())))
    smp.set_editor_property('sampler_type', u.MaterialSamplerType.SAMPLERTYPE_COLOR)
    ML.connect_material_expressions(mul, '', smp, 'UVs')
    tint = ex(u.MaterialExpressionVectorParameter, -420, 100)
    tint.set_editor_property('parameter_name', 'Tint'); tint.set_editor_property('default_value', u.LinearColor(1, 1, 1, 1))
    col = ex(u.MaterialExpressionMultiply, -150, -200)
    ML.connect_material_expressions(smp, 'RGB', col, 'A')
    ML.connect_material_expressions(tint, '', col, 'B')
    assert ML.connect_material_property(col, '', u.MaterialProperty.MP_BASE_COLOR)
    rough = ex(u.MaterialExpressionMultiply, -150, 0)
    ML.connect_material_expressions(smp, 'A', rough, 'A')
    ML.connect_material_expressions(scalar('RoughnessScale', 1.0, -420, 250), '', rough, 'B')
    assert ML.connect_material_property(rough, '', u.MaterialProperty.MP_ROUGHNESS)
    emi = ex(u.MaterialExpressionMultiply, -150, 200)
    ML.connect_material_expressions(col, '', emi, 'A')
    ML.connect_material_expressions(scalar('Emissive', 0.0, -420, 400), '', emi, 'B')
    assert ML.connect_material_property(emi, '', u.MaterialProperty.MP_EMISSIVE_COLOR)
    assert ML.connect_material_property(scalar('Metallic', 0.0, -420, 550), '', u.MaterialProperty.MP_METALLIC)
    assert ML.connect_material_property(scalar('Specular', .35, -420, 700), '', u.MaterialProperty.MP_SPECULAR)
    ML.recompile_material(m)
    assert EA.save_loaded_asset(m)
    R['master'] = m.get_path_name()

    for mi_name, s in spec['instances'].items():
        mi = u.load_asset(FIN + '/' + mi_name)
        assert mi, mi_name
        ML.set_material_instance_parent(mi, m)
        ML.set_material_instance_texture_parameter_value(mi, 'FinishColourRoughness', tex[s['texture']])
        ML.set_material_instance_scalar_parameter_value(mi, 'MetreUVScale', 1.0 / s['tile'])
        ML.set_material_instance_vector_parameter_value(mi, 'Tint', u.LinearColor(*s.get('tint', [1, 1, 1]), 1))
        for p in ('RoughnessScale', 'Emissive', 'Metallic', 'Specular'):
            if p in s:
                ML.set_material_instance_scalar_parameter_value(mi, p, float(s[p]))
        ML.update_material_instance(mi)
        assert EA.save_loaded_asset(mi)
        R['instances'].append(dict(mi=mi.get_path_name(), parent=mi.get_editor_property('parent').get_path_name(), **s))
    R['status'] = 'SUCCESS'


try:
    main()
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'Surfaces48Report.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
print('SURFACES48', R['status'])
