"""Root invokes after targeted native import; defaults work before any action."""
from pathlib import Path
def apply_native(ctx):
    u=ctx.u;AT=u.AssetToolsHelpers.get_asset_tools();ML=u.MaterialEditingLibrary
    B='/Game/Airport38/EquipmentScreens';T=Path(__file__).resolve().parent/'DisplayArt';EA=u.EditorAssetLibrary
    textures={};tasks=[]
    for p in sorted(T.glob('T_AP_UI38_*.png')):
        t=u.AssetImportTask();t.set_editor_property('filename',str(p));t.set_editor_property('destination_path',B);t.set_editor_property('destination_name',p.stem);t.set_editor_property('automated',True);t.set_editor_property('replace_existing',True);t.set_editor_property('save',True);tasks.append(t)
    assert tasks,'Equipment38 display artwork missing'
    AT.import_asset_tasks(tasks)
    parent_path=B+'/M_AP_Interface38';parent=u.load_asset(parent_path)
    if not parent:
        parent=AT.create_asset('M_AP_Interface38',B,u.Material,u.MaterialFactoryNew())
    ML.delete_all_material_expressions(parent)
    parent.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT);parent.set_editor_property('two_sided',True);parent.set_editor_property('used_with_instanced_static_meshes',True)
    sample=ML.create_material_expression(parent,u.MaterialExpressionTextureSampleParameter2D,-400,0);sample.set_editor_property('parameter_name','ScreenImage');sample.set_editor_property('texture',u.load_asset(B+'/T_AP_UI38_Checkin'))
    level=ML.create_material_expression(parent,u.MaterialExpressionScalarParameter,-400,200);level.set_editor_property('parameter_name','ScreenLuminance');level.set_editor_property('default_value',70.)
    mult=ML.create_material_expression(parent,u.MaterialExpressionMultiply,-120,0);ML.connect_material_expressions(sample,'RGB',mult,'A');ML.connect_material_expressions(level,'',mult,'B');ML.connect_material_property(mult,'',u.MaterialProperty.MP_EMISSIVE_COLOR);ML.recompile_material(parent);assert EA.save_loaded_asset(parent)
    mats={}
    for p in sorted(T.glob('T_AP_UI38_*.png')):
        key=p.stem.removeprefix('T_AP_UI38_');tex=u.load_asset(B+'/'+p.stem);assert tex
        mi=u.load_asset(B+'/MI_AP_UI38_'+key) or AT.create_asset('MI_AP_UI38_'+key,B,u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew())
        ML.set_material_instance_parent(mi,parent);ML.set_material_instance_texture_parameter_value(mi,'ScreenImage',tex);ML.set_material_instance_scalar_parameter_value(mi,'ScreenLuminance',70.);assert abs(ML.get_material_instance_scalar_parameter_value(mi,'ScreenLuminance')-70)<1e-5;EA.save_loaded_asset(mi);mats[key]=mi
    assigned=[]
    for n,key in ctx.D['repair38']['equipment']['screen_roles38'].items():
        actor=ctx.actors.get(n)
        if not actor:continue
        c=actor.get_component_by_class(u.StaticMeshComponent)
        if not c or not c.static_mesh:continue
        for j,slot in enumerate(c.static_mesh.static_materials):
            if str(slot.material_slot_name).startswith('MI_AP_Screen'):c.set_material(j,mats[key]);assigned.append(dict(actor=n,slot=j,role=key))
    assert len(assigned)>=13,('Not all actual screen faces were assigned',assigned)
    return dict(status='APPLIED',screens=assigned,materials=list(mats),slot_match='MI_AP_Screen including inherited numeric suffixes')
