"""Small depth-independent crosshair, authored as an editable post-process material."""
import unreal as u

def build():
 ml=u.MaterialEditingLibrary;path='/Game/Gameplay/M_AimReticle13'
 mat=u.load_asset(path) or u.AssetToolsHelpers.get_asset_tools().create_asset('M_AimReticle13','/Game/Gameplay',u.Material,u.MaterialFactoryNew())
 mat.set_editor_property('material_domain',u.MaterialDomain.MD_POST_PROCESS)
 ml.delete_all_material_expressions(mat)
 uv=ml.create_material_expression(mat,u.MaterialExpressionScreenPosition,-600,0)
 size=ml.create_material_expression(mat,u.MaterialExpressionViewSize,-600,150)
 scene=ml.create_material_expression(mat,u.MaterialExpressionSceneTexture,-600,300)
 scene.set_editor_property('scene_texture_id',u.SceneTextureId.PPI_POST_PROCESS_INPUT0)
 custom=ml.create_material_expression(mat,u.MaterialExpressionCustom,-200,0)
 custom.set_editor_property('output_type',u.CustomMaterialOutputType.CMOT_FLOAT3)
 inputs=[]
 for name in ('UV','Size','Scene'):
  inp=u.CustomInput();inp.set_editor_property('input_name',name);inputs.append(inp)
 custom.set_editor_property('inputs',inputs)
 custom.set_editor_property('code','''float2 p=abs((UV-float2(.5,.5))*Size);
float inner=max((1-smoothstep(.55,1.05,p.x))*(1-smoothstep(4,4.5,p.y)),(1-smoothstep(.55,1.05,p.y))*(1-smoothstep(4,4.5,p.x)));
float outer=max((1-smoothstep(1.25,1.75,p.x))*(1-smoothstep(5,5.5,p.y)),(1-smoothstep(1.25,1.75,p.y))*(1-smoothstep(5,5.5,p.x)));
return lerp(lerp(Scene.rgb,float3(.025,.035,.045),outer*.85),float3(.94,.97,1),inner*.94);''')
 assert ml.connect_material_expressions(uv,'ViewportUV',custom,'UV'),'Viewport UV connection failed'
 assert ml.connect_material_expressions(size,'',custom,'Size'),'View size connection failed'
 assert ml.connect_material_expressions(scene,'Color',custom,'Scene'),'Scene input connection failed'
 assert ml.connect_material_property(custom,'',u.MaterialProperty.MP_EMISSIVE_COLOR),'Reticle output connection failed'
 ml.recompile_material(mat);u.EditorAssetLibrary.save_loaded_asset(mat)
 return mat
