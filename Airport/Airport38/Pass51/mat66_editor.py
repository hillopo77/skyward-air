"""Pass66: look-at feedback for Gameplay66 (-run=pythonscript). MUTATES AND SAVES two materials and one level actor.

  M_AP_P66Highlight  translucent, unlit overlay: a warm fresnel rim with a slow
                     breathing pulse, put on whatever the crosshair finds
                     grabbable (as an overlay material, so the object keeps
                     its own look underneath)
  M_AP_P66Dot        translucent, unlit, no depth test: the crosshair dot
  'P66 crosshair dot' a tiny sphere actor in the level, hidden in game,
                     MOVABLE, no collision; Gameplay66 shows it and keeps it
                     25 cm in front of the eye
Re-runnable: both materials and the actor are replaced.
"""
import unreal as u, json, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAP = '/Game/Airport38/L_Airport_Repair38'
DIR = '/Game/Airport38/Pass48/Materials'
R = dict(status='RUNNING')
ML = u.MaterialEditingLibrary


def material(name):
    path = DIR + '/' + name
    if u.EditorAssetLibrary.does_asset_exist(path):
        u.EditorAssetLibrary.delete_asset(path)
    m = u.AssetToolsHelpers.get_asset_tools().create_asset(name, DIR, u.Material, u.MaterialFactoryNew())
    m.set_editor_property('blend_mode', u.BlendMode.BLEND_TRANSLUCENT)
    m.set_editor_property('shading_model', u.MaterialShadingModel.MSM_UNLIT)

    def ex(cls, x, y, **kw):
        e = ML.create_material_expression(m, cls, x, y)
        for k, v in kw.items():
            e.set_editor_property(k, v)
        return e
    return m, ex


def highlight():
    m, ex = material('M_AP_P66Highlight')
    fr = ex(u.MaterialExpressionFresnel, -700, 0, exponent=2.6, base_reflect_fraction=0.0)
    t = ex(u.MaterialExpressionTime, -900, 250)
    sn = ex(u.MaterialExpressionSine, -750, 250, period=1.6)
    ML.connect_material_expressions(t, '', sn, '')
    half = ex(u.MaterialExpressionMultiply, -600, 250)
    ML.connect_material_expressions(sn, '', half, 'A')
    q = ex(u.MaterialExpressionConstant, -750, 330, r=.18)
    ML.connect_material_expressions(q, '', half, 'B')
    pulse = ex(u.MaterialExpressionAdd, -450, 250)                      # 0.82 .. 1.18
    ML.connect_material_expressions(half, '', pulse, 'A')
    one = ex(u.MaterialExpressionConstant, -600, 330, r=1.0)
    ML.connect_material_expressions(one, '', pulse, 'B')
    rim = ex(u.MaterialExpressionMultiply, -450, 0)                     # fresnel * 2.4 + 0.18
    ML.connect_material_expressions(fr, '', rim, 'A')
    k = ex(u.MaterialExpressionConstant, -600, 80, r=2.4)
    ML.connect_material_expressions(k, '', rim, 'B')
    base = ex(u.MaterialExpressionAdd, -300, 0)
    ML.connect_material_expressions(rim, '', base, 'A')
    b0 = ex(u.MaterialExpressionConstant, -450, 80, r=.18)
    ML.connect_material_expressions(b0, '', base, 'B')
    lit = ex(u.MaterialExpressionMultiply, -150, 0)
    ML.connect_material_expressions(base, '', lit, 'A')
    ML.connect_material_expressions(pulse, '', lit, 'B')
    col = ex(u.MaterialExpressionVectorParameter, -300, -200, parameter_name='Colour', default_value=u.LinearColor(1.0, .74, .36, 1))
    em = ex(u.MaterialExpressionMultiply, 50, -100)
    ML.connect_material_expressions(col, '', em, 'A')
    ML.connect_material_expressions(lit, '', em, 'B')
    ML.connect_material_property(em, '', u.MaterialProperty.MP_EMISSIVE_COLOR)
    op = ex(u.MaterialExpressionMultiply, -150, 150)                    # (fresnel * .55 + .06) * pulse
    a = ex(u.MaterialExpressionMultiply, -450, 150)
    ML.connect_material_expressions(fr, '', a, 'A')
    k2 = ex(u.MaterialExpressionConstant, -600, 170, r=.55)
    ML.connect_material_expressions(k2, '', a, 'B')
    a2 = ex(u.MaterialExpressionAdd, -300, 150)
    ML.connect_material_expressions(a, '', a2, 'A')
    k3 = ex(u.MaterialExpressionConstant, -450, 200, r=.06)
    ML.connect_material_expressions(k3, '', a2, 'B')
    ML.connect_material_expressions(a2, '', op, 'A')
    ML.connect_material_expressions(pulse, '', op, 'B')
    ML.connect_material_property(op, '', u.MaterialProperty.MP_OPACITY)
    ML.recompile_material(m)
    assert u.EditorAssetLibrary.save_loaded_asset(m)
    return m


def dot():
    m, ex = material('M_AP_P66Dot')
    m.set_editor_property('disable_depth_test', True)
    col = ex(u.MaterialExpressionVectorParameter, -300, -100, parameter_name='Colour', default_value=u.LinearColor(1, .97, .92, 1))
    k = ex(u.MaterialExpressionScalarParameter, -300, 0, parameter_name='Strength', default_value=1.6)
    em = ex(u.MaterialExpressionMultiply, -100, -50)
    ML.connect_material_expressions(col, '', em, 'A')
    ML.connect_material_expressions(k, '', em, 'B')
    ML.connect_material_property(em, '', u.MaterialProperty.MP_EMISSIVE_COLOR)
    op = ex(u.MaterialExpressionScalarParameter, -300, 120, parameter_name='Opacity', default_value=.85)
    ML.connect_material_property(op, '', u.MaterialProperty.MP_OPACITY)
    ML.recompile_material(m)
    assert u.EditorAssetLibrary.save_loaded_asset(m)
    return m


def main():
    h = highlight()
    d = dot()
    assert u.EditorLoadingAndSavingUtils.load_map(MAP)
    EA = u.get_editor_subsystem(u.EditorActorSubsystem)
    for a in EA.get_all_level_actors():
        if a.get_actor_label() == 'P66 crosshair dot':
            EA.destroy_actor(a)
    s = EA.spawn_actor_from_class(u.StaticMeshActor, u.Vector(0, 0, -5000), u.Rotator(0, 0, 0))
    s.set_actor_label('P66 crosshair dot')
    s.set_folder_path('Gameplay/Pass66')
    c = s.static_mesh_component
    c.set_static_mesh(u.load_asset('/Engine/BasicShapes/Sphere'))
    c.set_material(0, d)
    c.set_mobility(u.ComponentMobility.MOVABLE)
    c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
    c.set_editor_property('cast_shadow', False)
    c.set_editor_property('hidden_in_game', True)
    s.set_actor_scale3d(u.Vector(.003, .003, .003))
    assert u.EditorLoadingAndSavingUtils.save_current_level()
    R.update(status='SUCCESS', highlight=h.get_path_name(), dot=d.get_path_name())


try:
    main()
except Exception:
    R['status'] = 'ERROR'; R['error'] = traceback.format_exc()
(HERE / 'Mat66.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
print('MAT66', R['status'])
