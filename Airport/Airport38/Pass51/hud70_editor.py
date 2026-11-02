"""Pass70: centred prompt text under the crosshair (-run=pythonscript). MUTATES AND SAVES the level and one material.

The player found the top-left print_string hints developer-style. gameplay66.hud()
now writes two short centred lines just under the crosshair (what you can do; what
just happened) on four level TextRenderActors (each line has a soft drop shadow),
placed 30 cm in front of the camera every frame:
  M_AP_P70HudText  translucent, unlit, no depth test (always on top, like the
                   crosshair dot): RobotoDistanceField through a soft threshold,
                   Colour x Strength, Opacity
  P70 hud prompt / prompt shadow / message / message shadow   hidden in game
                   until gameplay66 shows them; no collision; centred
"""
import unreal as u, json, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAP = '/Game/Airport38/L_Airport_Repair38'
DIR = '/Game/Airport38/Gameplay66/UI'
FONT = '/Engine/EngineFonts/RobotoDistanceField'
ML = u.MaterialEditingLibrary
R = dict(status='RUNNING', spawned=[])


def material():
    path = DIR + '/M_AP_P70HudText'
    if u.EditorAssetLibrary.does_asset_exist(path):
        u.EditorAssetLibrary.delete_asset(path)
    m = u.AssetToolsHelpers.get_asset_tools().create_asset('M_AP_P70HudText', DIR, u.Material, u.MaterialFactoryNew())
    m.set_editor_property('blend_mode', u.BlendMode.BLEND_TRANSLUCENT)
    m.set_editor_property('shading_model', u.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property('disable_depth_test', True)
    m.set_editor_property('two_sided', True)

    def ex(cls, x, y, **kw):
        e = ML.create_material_expression(m, cls, x, y)
        for k, v in kw.items():
            e.set_editor_property(k, v)
        return e
    fs = ex(u.MaterialExpressionFontSampleParameter, -800, 100, parameter_name='Font', font=u.load_asset(FONT), font_texture_page=0)
    half = ex(u.MaterialExpressionConstant, -800, 260, r=.5)
    sub = ex(u.MaterialExpressionSubtract, -600, 120)
    ML.connect_material_expressions(fs, 'A', sub, 'A'); ML.connect_material_expressions(half, '', sub, 'B')
    k = ex(u.MaterialExpressionConstant, -600, 260, r=7.0)
    mul = ex(u.MaterialExpressionMultiply, -450, 120)
    ML.connect_material_expressions(sub, '', mul, 'A'); ML.connect_material_expressions(k, '', mul, 'B')
    add = ex(u.MaterialExpressionAdd, -320, 120)
    ML.connect_material_expressions(mul, '', add, 'A'); ML.connect_material_expressions(half, '', add, 'B')
    sat = ex(u.MaterialExpressionSaturate, -200, 120); ML.connect_material_expressions(add, '', sat, '')
    op = ex(u.MaterialExpressionScalarParameter, -320, 260, parameter_name='Opacity', default_value=.95)
    vc = ex(u.MaterialExpressionVertexColor, -500, -120)                 # TextRender's colour (alpha: the shadow is soft)
    alpha0 = ex(u.MaterialExpressionMultiply, -150, 160)
    ML.connect_material_expressions(sat, '', alpha0, 'A'); ML.connect_material_expressions(op, '', alpha0, 'B')
    alpha = ex(u.MaterialExpressionMultiply, -40, 200)
    ML.connect_material_expressions(alpha0, '', alpha, 'A'); ML.connect_material_expressions(vc, 'A', alpha, 'B')
    st = ex(u.MaterialExpressionScalarParameter, -500, -20, parameter_name='Strength', default_value=110.0)   # the level's fixed EV 6.5: ~1/110 on screen
    col = ex(u.MaterialExpressionMultiply, -300, -80)
    ML.connect_material_expressions(vc, '', col, 'A'); ML.connect_material_expressions(st, '', col, 'B')
    ML.connect_material_property(col, '', u.MaterialProperty.MP_EMISSIVE_COLOR)
    ML.connect_material_property(alpha, '', u.MaterialProperty.MP_OPACITY)
    ML.recompile_material(m)
    assert u.EditorAssetLibrary.save_loaded_asset(m)
    return m


def main():
    m = material()
    assert u.EditorLoadingAndSavingUtils.load_map(MAP)
    EA = u.get_editor_subsystem(u.EditorActorSubsystem)
    for a in EA.get_all_level_actors():
        if a.get_actor_label().startswith('P70 hud'):
            EA.destroy_actor(a)
    font = u.load_asset(FONT)
    for name, colour, size in (('P70 hud prompt', (1.0, .93, .78), .8), ('P70 hud prompt shadow', (0.0, 0.0, 0.0), .8),
                               ('P70 hud message', (1.0, .8, .45), .66), ('P70 hud message shadow', (0.0, 0.0, 0.0), .66)):
        a = EA.spawn_actor_from_class(u.TextRenderActor, u.Vector(0, 0, -5000), u.Rotator(0, 0, 0))
        a.set_actor_label(name); a.set_folder_path('Gameplay/Pass70')
        c = a.text_render
        c.set_editor_property('text', u.Text(''))
        c.set_editor_property('font', font)
        c.set_text_material(m)
        c.set_editor_property('horizontal_alignment', u.HorizTextAligment.EHTA_CENTER)
        c.set_editor_property('vertical_alignment', u.VerticalTextAligment.EVRTA_TEXT_CENTER)
        c.set_editor_property('world_size', size)
        c.set_editor_property('text_render_color', u.Color(r=int(colour[0] * 255), g=int(colour[1] * 255), b=int(colour[2] * 255),
                                                           a=140 if 'shadow' in name else 255))
        c.set_editor_property('cast_shadow', False)
        c.set_mobility(u.ComponentMobility.MOVABLE)
        c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
        a.set_actor_hidden_in_game(True)
        a.set_actor_enable_collision(False)
        if 'shadow' in name:                                              # the shadow draws first, under the text
            c.set_editor_property('translucency_sort_priority', -1)
        else:
            c.set_editor_property('translucency_sort_priority', 1)
        R['spawned'].append(name)
    assert u.EditorLoadingAndSavingUtils.save_current_level()
    R['status'] = 'SUCCESS'


try:
    main()
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'Hud70.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
print('HUD70', R['status'])
