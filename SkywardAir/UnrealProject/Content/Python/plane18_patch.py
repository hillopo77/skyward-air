"""Install only the revised fittings into a copy of the aircraft map."""
import unreal as u,json,math
from pathlib import Path
R=Path(__file__).resolve().parents[3];OUT=R/'Revision18';D=json.loads((OUT/'Exports/manifest.json').read_text());SC=D['scenes']['L_Plane_Reference'];FACT=json.loads((OUT/'Source18.json').read_text());EA=u.get_editor_subsystem(u.EditorActorSubsystem);AT=u.AssetToolsHelpers.get_asset_tools();MESH={}
def prop(o,**kw):
 for k,v in kw.items():o.set_editor_property(k,v)
def v(p):return u.Vector(p[0]*100,-p[1]*100,p[2]*100)
def rot(p):return u.Rotator(pitch=math.degrees(p[0]),yaw=-math.degrees(p[2]),roll=math.degrees(p[1]))
def glass_material():
 path='/Game/Plane18/Materials/MI_Plane_SkyGlass18';m=u.load_asset(path) or AT.create_asset('MI_Plane_SkyGlass18','/Game/Plane18/Materials',u.Material,u.MaterialFactoryNew());ML=u.MaterialEditingLibrary;ML.delete_all_material_expressions(m);prop(m,blend_mode=u.BlendMode.BLEND_TRANSLUCENT,two_sided=True,translucency_lighting_mode=u.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
 for slot,kind,value in [(u.MaterialProperty.MP_BASE_COLOR,u.MaterialExpressionConstant3Vector,u.LinearColor(.75,.88,.94,1)),(u.MaterialProperty.MP_OPACITY,u.MaterialExpressionConstant,.065),(u.MaterialProperty.MP_ROUGHNESS,u.MaterialExpressionConstant,.045),(u.MaterialProperty.MP_SPECULAR,u.MaterialExpressionConstant,.60)]:
  node=ML.create_material_expression(m,kind,0,0);node.set_editor_property('constant' if kind==u.MaterialExpressionConstant3Vector else 'r',value);ML.connect_material_property(node,'',slot)
 ML.recompile_material(m);u.EditorAssetLibrary.save_loaded_asset(m)

def imports():
 glass_material()
 for aid in FACT['changed_assets']:
  task=u.AssetImportTask();prop(task,filename=str(OUT/'Exports/FBX'/(aid+'.fbx')),destination_path='/Game/Plane18/Meshes',destination_name=aid,automated=True,save=True,replace_existing=True);opt=u.FbxImportUI();prop(opt,import_mesh=True,import_as_skeletal=False,import_materials=False,import_textures=False,automated_import_should_detect_type=False,mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH);prop(opt.static_mesh_import_data,combine_meshes=True,auto_generate_collision=False,reorder_material_to_fbx_order=True,convert_scene=False,convert_scene_unit=True,force_front_x_axis=False,normal_import_method=u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS);task.set_editor_property('options',opt);AT.import_asset_tasks([task]);m=u.load_asset('/Game/Plane18/Meshes/'+aid);assert m,aid
  desc=next(q for q in D['assets'] if q['id']==aid);slots=[]
  for n in desc['materials']:
   mat=u.load_asset(('/Game/Plane18/Materials/'+n if n=='MI_Plane_SkyGlass18' else '/Game/Art/Materials/Instances/'+n));assert mat,n;s=u.StaticMaterial();prop(s,material_interface=mat,material_slot_name=u.Name(n));slots.append(s)
  m.set_editor_property('static_materials',slots);m.get_editor_property('body_setup').set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE);u.EditorAssetLibrary.save_loaded_asset(m);MESH[aid]=m
 return MESH

def apply():
 actors={a.get_actor_label():a for a in EA.get_all_level_actors()};changed=[];dynamic={q['actor'] for q in SC['interactions'] if q.get('motion')}|{s['actor'] for q in SC['interactions'] for s in q.get('roller_parts',[])}|{s['actor'] for q in SC['interactions'] for s in q.get('targets',[]) if s.get('actor')}
 for q in SC['instances']:
  if q['asset'] not in MESH and q['name'] not in FACT['actor_deltas']:continue
  a=actors.get(q['name'])
  if not a:a=EA.spawn_actor_from_class(u.StaticMeshActor,v(q['location']),rot(q['rotation']));a.set_actor_label(q['name']);a.tags=[u.Name('Skyward:'+q['name'])];a.set_folder_path('Aircraft17/Fittings');actors[q['name']]=a
  c=a.static_mesh_component;c.set_mobility(u.ComponentMobility.MOVABLE)
  if q['asset'] in MESH:c.set_editor_property('override_materials',[]);c.set_static_mesh(MESH[q['asset']])
  a.set_actor_location(v(q['location']),False,True);a.set_actor_rotation(rot(q['rotation']),False);a.set_actor_scale3d(u.Vector(*q['scale']));c.set_collision_profile_name('BlockAll');c.set_mobility(u.ComponentMobility.MOVABLE if q['name'] in dynamic else u.ComponentMobility.STATIC);changed.append(q['name'])
 for q in SC['navigation_bounds']:
  a=actors.get(q['name'])
  if a:a.set_actor_location(v(q['location']),False,True);a.set_actor_scale3d(u.Vector(*q['size']))
 # Native distance-field text is rebuilt from the updated source mounting frames.
 for a in list(EA.get_all_level_actors()):
  if isinstance(a,u.TextRenderActor) and a.get_actor_label().startswith('Label '):EA.destroy_actor(a)
 moving={q['actor'] for q in SC['interactions'] if q.get('motion') or q['kind'] in ('control','inspect')}
 for index,q in enumerate(SC.get('labels',[])):
  right=q['right'];up=q['up'];r=u.MathLibrary.make_rot_from_yz(u.Vector(-right[0],right[1],-right[2]),u.Vector(up[0],-up[1],up[2]));a=EA.spawn_actor_from_class(u.TextRenderActor,v(q['location']),r);a.set_actor_label('Label '+str(index)+' '+q['text'][:40]);a.set_folder_path('Aircraft17/Labels');a.set_actor_enable_collision(False);c=a.get_component_by_class(u.TextRenderComponent);c.set_text(u.Text(q['text']));c.set_world_size(100);c.set_horizontal_alignment(u.HorizTextAligment.EHTA_CENTER);c.set_vertical_alignment(u.VerticalTextAligment.EVRTA_TEXT_CENTER);c.set_text_material(u.load_asset('/Game/Art/Materials/M_LabelDistanceField'));c.set_editor_property('cast_shadow',False);sz=c.get_text_local_size()
  if sz.y>0 and sz.z>0:c.set_x_scale(q['width']*100/sz.y);c.set_y_scale(q['height']*180/sz.z)
  c.set_text_render_color(u.Color(*[round(255*max(0,min(1,x))) for x in q['color']],255))
  if q.get('source_instance') in moving and q['source_instance'] in actors:
   c.set_mobility(u.ComponentMobility.MOVABLE);a.attach_to_actor(actors[q['source_instance']],u.Name('None'),u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,False)
 for q in SC['cameras']:
  if '17' not in q['name']:continue
  a=EA.spawn_actor_from_class(u.CameraActor,v(q['location']),rot(q['rotation']));a.set_actor_label(q['name']);a.tags=[u.Name('SkywardCamera:'+q['name'])];a.camera_component.set_field_of_view(q['fov']);a.camera_component.set_editor_property('constrain_aspect_ratio',False)
 return dict(changed_actors=changed,new_trays=FACT['trays'])
