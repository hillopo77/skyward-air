"""Pass54: the sun-shaft material (-run=pythonscript). MUTATES AND SAVES one new
material, M_AP_P54SunShaft (re-runnable).

Unlit, additive, two-sided: Colour x Strength x (1 - V)^1.6 x min(1, 6V) x sin(pi U). On the
shaft cards (rays54_blender.py) V runs from the window (0) to the floor (1)
and U across each face, so a shaft fades in just inside the glass, fades out before
the floor and has soft sides, with no hard edge anywhere.
"""
import unreal as u, json, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIR, NAME = '/Game/Airport38/Pass48/Materials', 'M_AP_P54SunShaft'
R = dict(status='RUNNING')
ML = u.MaterialEditingLibrary


def main():
    path = DIR + '/' + NAME
    if u.EditorAssetLibrary.does_asset_exist(path):
        u.EditorAssetLibrary.delete_asset(path)
    m = u.AssetToolsHelpers.get_asset_tools().create_asset(NAME, DIR, u.Material, u.MaterialFactoryNew())
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
    mv = ex(u.MaterialExpressionComponentMask, -700, 60, r=False, g=True, b=False, a=False)
    ML.connect_material_expressions(uv, '', mu, '')
    ML.connect_material_expressions(uv, '', mv, '')
    side = ex(u.MaterialExpressionSine, -500, -60, period=2.0)          # sin(pi U)
    ML.connect_material_expressions(mu, '', side, '')
    fade = ex(u.MaterialExpressionOneMinus, -500, 60)
    ML.connect_material_expressions(mv, '', fade, '')
    soft = ex(u.MaterialExpressionPower, -350, 60)                     # (1-V)^1.6: long gentle tail
    ML.connect_material_expressions(fade, '', soft, 'Base')
    ex_exp = ex(u.MaterialExpressionConstant, -500, 160, r=1.6)
    ML.connect_material_expressions(ex_exp, '', soft, 'Exp')
    grow = ex(u.MaterialExpressionMultiply, -500, 260)                 # fade in over the first 1/6
    ML.connect_material_expressions(mv, '', grow, 'A')
    six = ex(u.MaterialExpressionConstant, -650, 300, r=6.0)
    ML.connect_material_expressions(six, '', grow, 'B')
    grow_s = ex(u.MaterialExpressionSaturate, -350, 260)
    ML.connect_material_expressions(grow, '', grow_s, '')
    ends = ex(u.MaterialExpressionMultiply, -250, 120)
    ML.connect_material_expressions(soft, '', ends, 'A')
    ML.connect_material_expressions(grow_s, '', ends, 'B')
    a = ex(u.MaterialExpressionMultiply, -200, 0)
    ML.connect_material_expressions(side, '', a, 'A')
    ML.connect_material_expressions(ends, '', a, 'B')
    col = ex(u.MaterialExpressionVectorParameter, -350, -250, parameter_name='Colour',
             default_value=u.LinearColor(1.0, .78, .5, 1))
    k = ex(u.MaterialExpressionScalarParameter, -350, -150, parameter_name='Strength', default_value=4.5)
    b = ex(u.MaterialExpressionMultiply, -150, -200)
    ML.connect_material_expressions(col, '', b, 'A')
    ML.connect_material_expressions(k, '', b, 'B')
    c = ex(u.MaterialExpressionMultiply, 50, -100)
    ML.connect_material_expressions(b, '', c, 'A')
    ML.connect_material_expressions(a, '', c, 'B')
    ML.connect_material_property(c, '', u.MaterialProperty.MP_EMISSIVE_COLOR)
    ML.recompile_material(m)
    assert u.EditorAssetLibrary.save_loaded_asset(m)
    R['status'] = 'SUCCESS'; R['path'] = m.get_path_name()


try:
    main()
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'RayMat54.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
print('RAYMAT54', R['status'])
