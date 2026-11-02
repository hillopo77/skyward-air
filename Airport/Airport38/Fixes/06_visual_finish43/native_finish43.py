"""Explicit Unreal parity for Finish43 metre-projected colour/roughness maps.

Call AFTER root fresh import/placement; this does not launch or save a map.
Each graph samples the same packed authored PNG as Blender. UV0 is measured
in source metres by airport_export24, so 1/tile is a real physical scale.
No normal texture, world-position animation, fine procedural noise or decals.
"""
from pathlib import Path
import importlib.util

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('terminal_finish43_palette',HERE/'finish43.py')
palette=importlib.util.module_from_spec(spec);spec.loader.exec_module(palette)

def apply_native(ctx):
 u=ctx.u;ML=u.MaterialEditingLibrary;EA=u.EditorAssetLibrary;AT=u.AssetToolsHelpers.get_asset_tools()
 B=ctx.B+'/Finish43';textures={};materials={};saved=[]
 tasks=[]
 for suffix,(file,colour,rough,metal,tile) in palette.MATERIALS.items():
  if not file:continue
  path=HERE/'Textures'/file;assert path.exists(),str(path)
  t=u.AssetImportTask()
  for k,v in dict(filename=str(path),destination_path=B+'/Textures',destination_name='T_AP_'+suffix+'43',automated=True,save=True,replace_existing=True).items():t.set_editor_property(k,v)
  tasks.append(t)
 AT.import_asset_tasks(tasks)
 for suffix,(file,colour,rough,metal,tile) in palette.MATERIALS.items():
  if not file:continue
  tex=u.load_asset(B+'/Textures/T_AP_'+suffix+'43');assert tex,('Missing imported finish43 image',suffix)
  tex.set_editor_property('srgb',True)
  tex.set_editor_property('address_x',u.TextureAddress.TA_WRAP);tex.set_editor_property('address_y',u.TextureAddress.TA_WRAP)
  # Default streamed mip chain is intentional; the floor joint must diminish
  # quietly at range instead of remaining a high-contrast geometry line.
  tex.set_editor_property('mip_gen_settings',u.TextureMipGenSettings.TMGS_SIMPLE_AVERAGE)
  assert EA.save_loaded_asset(tex);textures[suffix]=tex
 def expr(mat,cls,x,y):return ML.create_material_expression(mat,cls,x,y)
 def scalar(mat,name,value,x,y):
  n=expr(mat,u.MaterialExpressionScalarParameter,x,y);n.set_editor_property('parameter_name',name);n.set_editor_property('default_value',value);return n
 def linear(h):
  rgb=[int(h[i:i+2],16)/255 for i in (0,2,4)]
  rgb=[c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in rgb]
  return u.LinearColor(*rgb,1.)
 for suffix,(file,colour,rough,metal,tile) in palette.MATERIALS.items():
  name='MI_AP_'+palette.PREFIX+suffix
  # Graph is retained as an editable master per small finish role. It cannot
  # silently fall back to the legacy basecolour-only terminal material.
  parentname='M_AP_Finish43_'+suffix
  parent=u.load_asset(B+'/'+parentname) or AT.create_asset(parentname,B,u.Material,u.MaterialFactoryNew())
  assert parent
  ML.delete_all_material_expressions(parent)
  parent.set_editor_property('blend_mode',u.BlendMode.BLEND_OPAQUE)
  parent.set_editor_property('two_sided',False)
  if file:
   uv=expr(parent,u.MaterialExpressionTextureCoordinate,-700,-200);uv.set_editor_property('coordinate_index',0)
   mul=expr(parent,u.MaterialExpressionMultiply,-420,-200)
   assert ML.connect_material_expressions(uv,'',mul,'A')
   assert ML.connect_material_expressions(scalar(parent,'MetreUVScale',1/tile,-700,0),'',mul,'B')
   sample=expr(parent,u.MaterialExpressionTextureSampleParameter2D,-180,-200)
   sample.set_editor_property('parameter_name','FinishColourRoughness');sample.set_editor_property('texture',textures[suffix]);sample.set_editor_property('sampler_type',u.MaterialSamplerType.SAMPLERTYPE_COLOR)
   assert ML.connect_material_expressions(mul,'',sample,'UVs')
   assert ML.connect_material_property(sample,'RGB',u.MaterialProperty.MP_BASE_COLOR)
   assert ML.connect_material_property(sample,'A',u.MaterialProperty.MP_ROUGHNESS)
  else:
   tint=expr(parent,u.MaterialExpressionVectorParameter,-500,-200);tint.set_editor_property('parameter_name','BaseColor');tint.set_editor_property('default_value',linear(colour))
   assert ML.connect_material_property(tint,'RGB',u.MaterialProperty.MP_BASE_COLOR)
   assert ML.connect_material_property(scalar(parent,'Roughness',rough,-500,0),'',u.MaterialProperty.MP_ROUGHNESS)
  assert ML.connect_material_property(scalar(parent,'Metallic',metal,-500,180),'',u.MaterialProperty.MP_METALLIC)
  assert ML.connect_material_property(scalar(parent,'Specular',.27,-500,340),'',u.MaterialProperty.MP_SPECULAR)
  ML.recompile_material(parent);assert EA.save_loaded_asset(parent)
  mi=u.load_asset(B+'/'+name) or AT.create_asset(name,B,u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew())
  ML.set_material_instance_parent(mi,parent)
  if file:
   ML.set_material_instance_texture_parameter_value(mi,'FinishColourRoughness',textures[suffix])
   ML.set_material_instance_scalar_parameter_value(mi,'MetreUVScale',1/tile)
   assert abs(ML.get_material_instance_scalar_parameter_value(mi,'MetreUVScale')-1/tile)<1e-6
  assert mi.get_editor_property('parent')==parent
  assert EA.save_loaded_asset(mi);materials[name]=mi;saved.append(dict(role=suffix,material=mi.get_path_name(),tile_metres=tile,texture=str(file)))
 bindings=[];seen=set()
 for actor in ctx.EA.get_all_level_actors():
  for component in actor.get_components_by_class(u.StaticMeshComponent):
   sm=component.get_editor_property('static_mesh')
   if not sm:continue
   slots=list(sm.static_materials);changed=False
   for index,slot in enumerate(slots):
    name=str(slot.material_slot_name)
    if name not in materials:continue
    slot.set_editor_property('material_interface',materials[name]);slots[index]=slot;changed=True
    component.set_material(index,materials[name]);assert component.get_material(index)==materials[name]
    bindings.append(dict(actor=actor.get_actor_label(),mesh=sm.get_name(),slot=index,material=name))
   if changed and sm.get_path_name() not in seen:
    sm.set_editor_property('static_materials',slots);assert EA.save_loaded_asset(sm);seen.add(sm.get_path_name())
 required=set(palette.OWNED+palette.STRUCTURAL)
 assert required.issubset({b['mesh'] for b in bindings}),('Finish43 fresh mesh binding missing',required-{b['mesh'] for b in bindings})
 return dict(status='APPLIED_REQUIRES_NATIVE_GAMEPLAY_VISUAL_REVIEW',materials=saved,bindings=bindings,
             textures=len(textures),graphs=len(materials),source_uv_unit='metres',floor_joint_width_m=.003,
             pattern_parity='Same authored packed sRGB colour/linear roughness PNG and 1/tile UV0 scale in both editors',
             temporal_design='Mipmapped low-contrast surface variation; no fine normal/noise or geometric floor grids')
