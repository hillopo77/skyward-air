"""Import Blender kit and assemble editable UE 5.8 maps. Run once via Unreal Python.
No third party plugins or C++ compilation. Re-running rebuilds only this dedicated project.
"""
import unreal as u, json, math, traceback, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
DATA=json.loads((ROOT/'Exports'/'manifest.json').read_text())
AT=u.AssetToolsHelpers.get_asset_tools()
ML=u.MaterialEditingLibrary
EA=u.get_editor_subsystem(u.EditorActorSubsystem)
LS=u.get_editor_subsystem(u.LevelEditorSubsystem)
REPORT={'assets':[], 'maps':[], 'warnings':[]}
REPORT['source_sha256']=hashlib.sha256((ROOT/'Plane.blend').read_bytes()).hexdigest()
REPORT['manifest_sha256']=hashlib.sha256((ROOT/'Exports/manifest.json').read_bytes()).hexdigest()
SKY_CUBE=None
TEXT_MATERIAL=None

def save(a):u.EditorAssetLibrary.save_loaded_asset(a)
def prop(o,**kw):
    for k,v in kw.items():o.set_editor_property(k,v)

def create(name,path,cls,factory):
    return u.load_asset(path+'/'+name) or AT.create_asset(name,path,cls,factory)

def node(m,cls,x,y,**kw):
    n=ML.create_material_expression(m,cls,x,y);prop(n,**kw);return n

def materials():
    global SKY_CUBE,TEXT_MATERIAL
    text_path='/Game/Art/Materials/M_LabelDistanceField'
    TEXT_MATERIAL=u.load_asset(text_path)
    if not TEXT_MATERIAL:
        TEXT_MATERIAL=u.EditorAssetLibrary.duplicate_asset('/Engine/EngineMaterials/DefaultTextMaterialOpaque',text_path)
        if not TEXT_MATERIAL:raise RuntimeError('Cannot create native label material')
        old=ML.get_material_property_input_node(TEXT_MATERIAL,u.MaterialProperty.MP_EMISSIVE_COLOR)
        output=ML.get_material_property_input_node_output_name(TEXT_MATERIAL,u.MaterialProperty.MP_EMISSIVE_COLOR)
        if old:
            boost=node(TEXT_MATERIAL,u.MaterialExpressionMultiply,600,0,const_b=32)
            ML.connect_material_expressions(old,output,boost,'A');ML.connect_material_property(boost,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
        ML.recompile_material(TEXT_MATERIAL);save(TEXT_MATERIAL)
    surfaces={}
    for desc in DATA['materials'].values():
        if not desc.get('surface'):continue
        family=desc['surface']['texture']
        for kind in ('Color','Rough','Normal'):
            name=f'T_{family}_{kind}';path='/Game/Art/Textures/'+name
            tex=u.load_asset(path)
            if not tex:
                task=u.AssetImportTask();prop(task,filename=str(ROOT/'SourceAssets'/'Textures'/'Quality'/(name+'.png')),destination_path='/Game/Art/Textures',automated=True,save=True)
                AT.import_asset_tasks([task]);tex=u.load_asset(path)
            if not tex:raise RuntimeError('Missing surface texture '+name)
            if kind=='Normal':prop(tex,srgb=False,compression_settings=u.TextureCompressionSettings.TC_NORMALMAP)
            elif kind=='Rough':prop(tex,srgb=False,compression_settings=u.TextureCompressionSettings.TC_GRAYSCALE)
            else:prop(tex,srgb=True)
            save(tex);surfaces[(family,kind)]=tex
    opaque=create('M_StylizedOpaque','/Game/Art/Materials',u.Material,u.MaterialFactoryNew())
    # Rebuild deterministic master graph.
    ML.delete_all_material_expressions(opaque)
    base=node(opaque,u.MaterialExpressionVectorParameter,-500,0,parameter_name='BaseColor',default_value=u.LinearColor(.5,.5,.5,1))
    rough=node(opaque,u.MaterialExpressionScalarParameter,-500,150,parameter_name='Roughness',default_value=.55)
    metal=node(opaque,u.MaterialExpressionScalarParameter,-500,270,parameter_name='Metallic',default_value=0)
    emit=node(opaque,u.MaterialExpressionScalarParameter,-500,390,parameter_name='EmissionStrength',default_value=0)
    mul=node(opaque,u.MaterialExpressionMultiply,-200,390)
    ML.connect_material_expressions(base,'',mul,'A');ML.connect_material_expressions(emit,'',mul,'B')
    for n,p in [(base,u.MaterialProperty.MP_BASE_COLOR),(rough,u.MaterialProperty.MP_ROUGHNESS),(metal,u.MaterialProperty.MP_METALLIC),(mul,u.MaterialProperty.MP_EMISSIVE_COLOR)]:ML.connect_material_property(n,'',p)
    # Shared, original numerical weave normal; disabled by default for smooth surfaces.
    normalpath='/Game/Art/Textures/T_FineWeave_Normal'
    tex=u.load_asset(normalpath)
    if not tex:
        task=u.AssetImportTask();prop(task,filename=str(ROOT/'SourceAssets'/'Textures'/'T_FineWeave_Normal.png'),destination_path='/Game/Art/Textures',automated=True,save=True)
        AT.import_asset_tasks([task]);tex=u.load_asset(normalpath)
    prop(tex,srgb=False,compression_settings=u.TextureCompressionSettings.TC_NORMALMAP);save(tex)
    uv=node(opaque,u.MaterialExpressionTextureCoordinate,-1000,600)
    tiling=node(opaque,u.MaterialExpressionScalarParameter,-1000,700,parameter_name='DetailTiling',default_value=12)
    uvscale=node(opaque,u.MaterialExpressionMultiply,-800,600)
    ML.connect_material_expressions(uv,'',uvscale,'A');ML.connect_material_expressions(tiling,'',uvscale,'B')
    detail=node(opaque,u.MaterialExpressionTextureSampleParameter2D,-600,600,parameter_name='DetailNormal',texture=tex,sampler_type=u.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    assert ML.connect_material_expressions(uvscale,'',detail,'UVs')
    flat=node(opaque,u.MaterialExpressionConstant3Vector,-600,820,constant=u.LinearColor(0,0,1,1))
    strength=node(opaque,u.MaterialExpressionScalarParameter,-600,920,parameter_name='DetailStrength',default_value=0)
    lerp=node(opaque,u.MaterialExpressionLinearInterpolate,-200,650)
    for a,out,inp in [(flat,'','A'),(detail,'RGB','B'),(strength,'','Alpha')]:ML.connect_material_expressions(a,out,lerp,inp)
    ML.connect_material_property(lerp,'',u.MaterialProperty.MP_NORMAL)
    # Original material families retain a neutral colour multiplier and use their own
    # roughness/normal response. Legacy untextured materials keep a zero blend.
    color_tex=node(opaque,u.MaterialExpressionTextureSampleParameter2D,-600,-400,parameter_name='SurfaceColor',texture=surfaces[('Polymer','Color')],sampler_type=u.MaterialSamplerType.SAMPLERTYPE_COLOR)
    rough_tex=node(opaque,u.MaterialExpressionTextureSampleParameter2D,-600,-200,parameter_name='SurfaceRoughness',texture=surfaces[('Polymer','Rough')],sampler_type=u.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE)
    for n in (color_tex,rough_tex):assert ML.connect_material_expressions(uvscale,'',n,'UVs')
    blend=node(opaque,u.MaterialExpressionScalarParameter,-600,-600,parameter_name='SurfaceStrength',default_value=0)
    white=node(opaque,u.MaterialExpressionConstant3Vector,-600,-700,constant=u.LinearColor(1,1,1,1))
    tint=node(opaque,u.MaterialExpressionLinearInterpolate,-350,-400)
    for src,out,inp in [(white,'','A'),(color_tex,'RGB','B'),(blend,'','Alpha')]:ML.connect_material_expressions(src,out,tint,inp)
    color_mul=node(opaque,u.MaterialExpressionMultiply,-100,-400)
    ML.connect_material_expressions(base,'',color_mul,'A');ML.connect_material_expressions(tint,'',color_mul,'B')
    ML.connect_material_property(color_mul,'',u.MaterialProperty.MP_BASE_COLOR)
    rough_mix=node(opaque,u.MaterialExpressionLinearInterpolate,-100,-150)
    for src,out,inp in [(rough,'','A'),(rough_tex,'R','B'),(blend,'','Alpha')]:ML.connect_material_expressions(src,out,rough_mix,inp)
    ML.connect_material_property(rough_mix,'',u.MaterialProperty.MP_ROUGHNESS)
    spec=node(opaque,u.MaterialExpressionScalarParameter,-100,250,parameter_name='Specular',default_value=.5)
    ML.connect_material_property(spec,'',u.MaterialProperty.MP_SPECULAR)
    opaque.set_editor_property('two_sided',True);ML.recompile_material(opaque);save(opaque)
    glass=create('M_WindowGlass','/Game/Art/Materials',u.Material,u.MaterialFactoryNew())
    ML.delete_all_material_expressions(glass)
    prop(glass,blend_mode=u.BlendMode.BLEND_TRANSLUCENT,two_sided=True,translucency_lighting_mode=u.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
    c=node(glass,u.MaterialExpressionVectorParameter,-400,0,parameter_name='GlassColor',default_value=u.LinearColor(.45,.7,.8,1))
    r=node(glass,u.MaterialExpressionScalarParameter,-400,120,parameter_name='GlassRoughness',default_value=.09)
    a=node(glass,u.MaterialExpressionScalarParameter,-400,240,parameter_name='GlassOpacity',default_value=.06)
    gs=node(glass,u.MaterialExpressionScalarParameter,-400,360,parameter_name='GlassSpecular',default_value=.25)
    ML.connect_material_property(gs,'',u.MaterialProperty.MP_SPECULAR)
    for n,p in [(c,u.MaterialProperty.MP_BASE_COLOR),(r,u.MaterialProperty.MP_ROUGHNESS),(a,u.MaterialProperty.MP_OPACITY)]:ML.connect_material_property(n,'',p)
    ML.recompile_material(glass);save(glass)
    skypath='/Game/Art/Textures/T_CloudySky'
    SKY_CUBE=u.load_asset(skypath)
    if not SKY_CUBE:
        task=u.AssetImportTask();prop(task,filename=str(ROOT/'SourceAssets'/'Textures'/'kloofendal_48d_partly_cloudy_puresky_2k.hdr'),destination_path='/Game/Art/Textures',destination_name='T_CloudySky',automated=True,save=True)
        AT.import_asset_tasks([task]);SKY_CUBE=u.load_asset(skypath)
    sky=create('M_CloudySky','/Game/Art/Materials',u.Material,u.MaterialFactoryNew())
    ML.delete_all_material_expressions(sky);prop(sky,two_sided=True,shading_model=u.MaterialShadingModel.MSM_UNLIT,is_sky=True)
    sample=node(sky,u.MaterialExpressionTextureSampleParameterCube,-400,0,parameter_name='Sky',texture=SKY_CUBE,sampler_type=u.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
    direction=node(sky,u.MaterialExpressionCameraVectorWS,-850,0)
    reverse=node(sky,u.MaterialExpressionMultiply,-650,0,const_b=-1)
    ML.connect_material_expressions(direction,'',reverse,'A');assert ML.connect_material_expressions(reverse,'',sample,'UVs')
    exposure=node(sky,u.MaterialExpressionMultiply,-180,0,const_b=35)
    ML.connect_material_expressions(sample,'RGB',exposure,'A');ML.connect_material_property(exposure,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
    ML.recompile_material(sky);save(sky)
    ife=create('M_IFEScreen','/Game/Art/Materials',u.Material,u.MaterialFactoryNew())
    ML.delete_all_material_expressions(ife);prop(ife,two_sided=True,shading_model=u.MaterialShadingModel.MSM_UNLIT)
    ui_textures={}
    for values in DATA['materials'].values():
        if not values.get('ui_texture'):continue
        source=values['ui_texture'];name='T_'+Path(source).stem;path='/Game/Art/Textures/'+name
        tex=u.load_asset(path)
        if not tex:
            task=u.AssetImportTask();prop(task,filename=str(ROOT/source),destination_path='/Game/Art/Textures',destination_name=name,automated=True,save=True)
            AT.import_asset_tasks([task]);tex=u.load_asset(path)
        prop(tex,srgb=True);save(tex);ui_textures[source]=tex
    if ui_textures:
        ui=node(ife,u.MaterialExpressionTextureSampleParameter2D,-400,0,parameter_name='ScreenImage',texture=next(iter(ui_textures.values())),sampler_type=u.MaterialSamplerType.SAMPLERTYPE_COLOR)
        boost=node(ife,u.MaterialExpressionMultiply,-100,0,const_b=42)
        ML.connect_material_expressions(ui,'RGB',boost,'A');ML.connect_material_property(boost,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
    ML.recompile_material(ife);save(ife)
    result={}
    for name,values in DATA['materials'].items():
        mi=create(name.replace('.','_'),'/Game/Art/Materials/Instances',u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew())
        if values.get('ui_texture'):
            ML.set_material_instance_parent(mi,ife);ML.set_material_instance_texture_parameter_value(mi,'ScreenImage',ui_textures[values['ui_texture']]);save(mi);result[name]=mi;continue
        ML.set_material_instance_parent(mi,glass if values['glass'] else opaque)
        if not values['glass']:
            ML.set_material_instance_vector_parameter_value(mi,'BaseColor',u.LinearColor(*values['color']))
            for p,k in [('Roughness','roughness'),('Metallic','metallic'),('EmissionStrength','emission')]:ML.set_material_instance_scalar_parameter_value(mi,p,values[k]*(30 if k=='emission' else 1))
            ML.set_material_instance_scalar_parameter_value(mi,'DetailStrength',values.get('detail',{}).get('strength',0)*2)
            ML.set_material_instance_scalar_parameter_value(mi,'DetailTiling',12 if 'Carpet' in name else 7)
            ML.set_material_instance_scalar_parameter_value(mi,'SurfaceStrength',1 if values.get('surface') else 0)
            ML.set_material_instance_scalar_parameter_value(mi,'Specular',values.get('specular',.5))
            if values.get('surface'):
                family=values['surface']['texture']
                ML.set_material_instance_texture_parameter_value(mi,'SurfaceColor',surfaces[(family,'Color')])
                ML.set_material_instance_texture_parameter_value(mi,'SurfaceRoughness',surfaces[(family,'Rough')])
                ML.set_material_instance_texture_parameter_value(mi,'DetailNormal',surfaces[(family,'Normal')])
                ML.set_material_instance_scalar_parameter_value(mi,'DetailTiling',values['surface']['tiling'])
                ML.set_material_instance_scalar_parameter_value(mi,'DetailStrength',values['surface']['normal_strength']*.32)
        else:
            ML.set_material_instance_vector_parameter_value(mi,'GlassColor',u.LinearColor(*values['color']))
            ML.set_material_instance_scalar_parameter_value(mi,'GlassOpacity',values.get('glass_opacity',.06))
            ML.set_material_instance_scalar_parameter_value(mi,'GlassRoughness',.12 if 'Instrument' in name else .09)
            ML.set_material_instance_scalar_parameter_value(mi,'GlassSpecular',.015 if 'Instrument' in name else .25)
        save(mi);result[name]=mi
    return result

def imports(mats):
    meshes={}
    hashfile=ROOT/'UnrealProject'/'Saved'/'SkywardImportHashes.json'
    hashes=json.loads(hashfile.read_text()) if hashfile.exists() else {}
    updated={}
    for a in DATA['assets']:
        name=a['id'];path='/Game/Art/Meshes/'+name
        if a.get('triangles',0)<=0:raise RuntimeError('Source mesh has no faces: '+name)
        digest=(a.get('signature') or hashlib.sha256((ROOT/'Exports'/'FBX'/(name+'.fbx')).read_bytes()).hexdigest())+('-material-remap-02' if name.startswith('SM_Plane_') else '')
        mesh=u.load_asset(path)
        preserve_existing=bool(mesh and '-SkywardPlaneOnly' in u.SystemLibrary.get_command_line() and not name.startswith('SM_Plane_'))
        if not preserve_existing and (not mesh or hashes.get(name)!=digest):
            if mesh and name.startswith('SM_Plane_'):
                # UE can retain unused slots from a removed monitor or dashboard
                # despite ResetToFbxOnMaterialConflict. Rebuild the table from FBX.
                mesh.set_editor_property('static_materials',[])
            task=u.AssetImportTask()
            prop(task,filename=str(ROOT/'Exports'/'FBX'/(name+'.fbx')),destination_path='/Game/Art/Meshes',destination_name=name,automated=True,replace_existing=True,save=True)
            opts=u.FbxImportUI()
            prop(opts,automated_import_should_detect_type=False,mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH,import_as_skeletal=False,import_mesh=True,import_animations=False,import_materials=False,import_textures=False,reset_to_fbx_on_material_conflict=True)
            imp=opts.get_editor_property('static_mesh_import_data')
            prop(imp,combine_meshes=True,auto_generate_collision=any(k in name for k in ['Suitcase','CoffeeCup']),convert_scene=False,convert_scene_unit=True,force_front_x_axis=False,normal_import_method=u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS)
            imp.set_editor_property('generate_lightmap_u_vs',False)
            imp.set_editor_property('reorder_material_to_fbx_order',True)
            task.set_editor_property('options',opts);AT.import_asset_tasks([task]);mesh=u.load_asset(path)
            if not task.get_editor_property('imported_object_paths'):raise RuntimeError('FBX import did not return a mesh: '+name)
        if not mesh:raise RuntimeError('Import failed: '+name)
        slots=mesh.get_editor_property('static_materials')
        # Reimport must use current Blender section names, not restore stale slot names.
        # In particular, gauge glass and monitor materials changed in revision 02.
        if name.startswith('SM_Plane_'):
            actual={str(slot.get_editor_property('imported_material_slot_name')) for slot in slots}
            expected=set(a['materials'])
            assert actual==expected,{'asset':name,'expected':sorted(expected),'actual':sorted(actual)}
        for i,slot in enumerate(slots):
            # ImportedMaterialSlotName tracks the current FBX section. The editable
            # display name can survive reimport from an older section arrangement.
            slotname=str(slot.get_editor_property('imported_material_slot_name'))
            if not slotname or slotname=='None':slotname=str(slot.get_editor_property('material_slot_name'))
            match=mats.get(slotname)
            if not match:match=u.load_asset('/Game/Art/Materials/Instances/'+slotname)
            if not match:
                for k,v in mats.items():
                    if slotname.startswith(k):match=v;break
            if not match:raise RuntimeError('Unmapped material '+name+': '+slotname)
            if slot.get_editor_property('material_interface')!=match:mesh.set_material(i,match)
        if name.startswith('SM_Plane_'):
            for i,slot in enumerate(mesh.get_editor_property('static_materials')):
                src=str(slot.get_editor_property('imported_material_slot_name'))
                assert slot.get_editor_property('material_interface')==mats[src],{'asset':name,'section':i,'source':src}
        body=mesh.get_editor_property('body_setup')
        # Compound concave architectural parts need accurate openings for art-tour navigation.
        # Dynamic props retain the importer-generated convex collision for future interaction.
        if body and not any(x in name for x in ['Suitcase','CoffeeCup']) and body.get_editor_property('collision_trace_flag')!=u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE:body.set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        save(mesh);meshes[name]=mesh
        bounds=mesh.get_bounds()
        REPORT['assets'].append({'id':name,'size_cm':[bounds.box_extent.x*2,bounds.box_extent.y*2,bounds.box_extent.z*2],'material_slots':len(slots),'source_material_names_match':not name.startswith('SM_Plane_') or actual==expected,'preserved_existing_historical_asset':preserve_existing})
        updated[name]=digest
        # Successful, validated imports can be reused even if a later asset fails.
        hashes[name]=digest
        hashfile.write_text(json.dumps(hashes,indent=2))
    # 1.02m repeat length, .18m thickness: numeric scale gate before placing hundreds of parts.
    ref=next(a for a in REPORT['assets'] if a['id']=='SM_Cabin_FloorModule')
    assert abs(ref['size_cm'][0]-472)<3 and abs(ref['size_cm'][1]-52)<3,ref
    hashfile.write_text(json.dumps(updated,indent=2))
    return meshes

def location(v):return u.Vector(v[0]*100,-v[1]*100,v[2]*100)
def zrotation(v):return u.Rotator(pitch=0,yaw=-math.degrees(v[2]),roll=0)
def camrot(e):
    # Blender camera looks down local -Z, Y up. Convert its forward vector to UE look rot.
    x,y,z=e
    forward=(-math.sin(y)*math.cos(x)*math.cos(z)-math.sin(x)*math.sin(z),-math.sin(y)*math.cos(x)*math.sin(z)+math.sin(x)*math.cos(z),-math.cos(y)*math.cos(x))
    return u.MathLibrary.make_rot_from_x(u.Vector(forward[0],-forward[1],forward[2]))

def gameplay():
    fac=u.BlueprintFactory();fac.set_editor_property('parent_class',u.DefaultPawn)
    bp=create('BP_ArtTourPawn','/Game/Gameplay',u.Blueprint,fac)
    cdo=u.get_default_object(bp.generated_class())
    movement=cdo.get_component_by_class(u.FloatingPawnMovement)
    if movement:
        prop(movement,max_speed=190,acceleration=900,deceleration=1100)
        movement.set_plane_constraint_normal(u.Vector(0,0,1))
        movement.set_plane_constraint_origin(u.Vector(0,0,162))
        movement.set_plane_constraint_enabled(True)
    sphere=cdo.get_component_by_class(u.SphereComponent)
    if sphere:sphere.set_sphere_radius(18)
    save(bp)
    fac=u.BlueprintFactory();fac.set_editor_property('parent_class',u.GameModeBase)
    gm=create('BP_ArtTourGameMode','/Game/Gameplay',u.Blueprint,fac)
    u.get_default_object(gm.generated_class()).set_editor_property('default_pawn_class',bp.generated_class());save(gm)
    return gm.generated_class()

def assemble(name,data,meshes,gm):
    plane_scene=name in ('L_Plane_Reference','L_Plane_Exterior15')
    map_path='/Game/Maps/'+name
    if u.EditorAssetLibrary.does_asset_exist(map_path):
        if not LS.load_level(map_path):raise RuntimeError('Could not load '+map_path)
        removable=[a for a in EA.get_all_level_actors() if isinstance(a,(u.StaticMeshActor,u.TextRenderActor,u.Light,u.CameraActor,u.PlayerStart,u.SkyAtmosphere,u.PostProcessVolume,u.VolumetricCloud,u.DefaultPawn))]
        EA.destroy_actors(removable)
    elif not LS.new_level(map_path):raise RuntimeError('Could not create '+map_path)
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    world.get_world_settings().set_editor_property('default_game_mode',gm)
    count=0;actors_by_name={}
    moving_items=[item for item in data.get('interactions',[]) if item.get('motion') or item.get('kind')=='door']
    moving_names={item['actor'] for item in moving_items}
    moving_names.update(child for item in moving_items for child in item.get('linked_actors',[]))
    kinematic_names={link['actor'] for item in moving_items for link in item.get('kinematic_links',[])}
    moving_names.update(kinematic_names)
    moving_names.update(target['actor'] for item in data.get('interactions',[]) if item.get('kind')=='control' for target in item.get('targets',[]) if 'actor' in target and ('rotation_states' in target or 'translation_states' in target))
    inspect_items=[item for item in data.get('interactions',[]) if item.get('kind')=='inspect' and item.get('hold')]
    moving_names.update(item['actor'] for item in inspect_items)
    moving_names.update(child for item in inspect_items for child in item.get('linked_actors',[]))
    moving_names.update(child for item in inspect_items for child in item.get('hold_actors',[]))
    for item in moving_items:
        motion=item.get('motion')
        if not motion:continue
        for stage in motion.get('stages',[]) if motion.get('type')=='compound' else [motion]:
            if stage.get('type','rotate')=='rotate':assert stage.get('axis','z').lower() in ('x','y','z'),item
            else:assert stage['type']=='slide' and len(stage['delta'])==3,item
            assert float(stage.get('end',1))>float(stage.get('start',0)),item
    for i in data['instances']:
        a=EA.spawn_actor_from_class(u.StaticMeshActor,location(i['location']),zrotation(i['rotation']))
        a.set_actor_label(i['name']);a.set_folder_path('Art/'+i['asset'].split('_')[1])
        a.set_editor_property('tags',[u.Name('Skyward:'+i['name'])])
        c=a.static_mesh_component;c.set_static_mesh(meshes[i['asset']]);a.set_actor_scale3d(u.Vector(*i['scale']))
        actors_by_name[i['name']]=a
        if i['name'] in moving_names or i['asset']=='SM_Plane_CockpitDoor':c.set_mobility(u.ComponentMobility.MOVABLE)
        if data.get('layout',{}).get('exterior_revision') and i['asset'] in ('SM_Plane_ExteriorAirframe','SM_Plane_OuterWindowBarrel','SM_Plane_DoorBay07','SM_Plane_LandingGear','SM_Plane_PassengerDoor07_L','SM_Plane_PassengerDoor07_R','SM_Plane_CargoBay10','SM_Plane_ExteriorCargoDoor10','SM_Plane_ReviewApron15'):
            c.set_editor_property('lighting_channels',u.LightingChannels(channel0=True,channel1=True,channel2=False))
        c.set_collision_profile_name('BlockAll')
        if i['name'] in kinematic_names:c.set_collision_profile_name('NoCollision');a.set_actor_enable_collision(False)
        if i['asset'] in ['SM_Terminal_GlassBay','SM_Cabin_WindowWall_R','SM_Cabin_WindowWall_L']:c.set_cast_shadow(False)
        count+=1
    for item in moving_items:
        assert item['actor'] in actors_by_name,{'missing_interactive_actor':item['actor']}
        # The art-tour pawn is a standing eye-height sphere. Low suite doors
        # need a hidden full-height footprint that follows their real leaf,
        # otherwise a player can walk through the visible closed door.
        if item.get('collision_box'):
            parent=actors_by_name[item['actor']];spec=item['collision_box']
            offset=location(spec.get('offset',[0,0,1.1]))
            a=EA.spawn_actor_from_class(u.StaticMeshActor,parent.get_actor_location()+offset,parent.get_actor_rotation())
            a.set_actor_label('MOTION_PROXY '+item['actor']);a.set_folder_path('Collision/Moving')
            c=a.static_mesh_component;c.set_mobility(u.ComponentMobility.MOVABLE)
            c.set_static_mesh(u.load_asset('/Engine/BasicShapes/Cube'))
            a.set_actor_scale3d(u.Vector(*spec['size']));c.set_collision_profile_name('BlockAll')
            c.set_collision_response_to_channel(u.CollisionChannel.ECC_VISIBILITY,next(getattr(u.CollisionResponseType,n) for n in dir(u.CollisionResponseType) if n.lower().endswith('ignore')))
            c.set_editor_property('visible',False);c.set_editor_property('cast_shadow',False)
            a.set_actor_hidden_in_game(True);a.set_actor_enable_collision(True)
            a.attach_to_actor(parent,u.Name('None'),u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,False)
        for child in item.get('linked_actors',[]):
            assert child in actors_by_name,{'missing_linked_actor':child}
            actors_by_name[child].attach_to_actor(actors_by_name[item['actor']],u.Name('None'),u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,False)
    for item in inspect_items:
        for child in dict.fromkeys(item.get('linked_actors',[])+item.get('hold_actors',[])):
            actors_by_name[child].attach_to_actor(actors_by_name[item['actor']],u.Name('None'),u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,False)
    for index,label in enumerate(data.get('labels',[])):
        right=label['right'];up=label['up']
        # Native text advances along -local Y and has +local Z up. Convert the
        # authored label basis together with the scene's handedness conversion.
        rot=u.MathLibrary.make_rot_from_yz(u.Vector(-right[0],right[1],-right[2]),u.Vector(up[0],-up[1],up[2]))
        a=EA.spawn_actor_from_class(u.TextRenderActor,location(label['location']),rot)
        a.set_actor_label('Label '+str(index)+' '+label['text'][:40]);a.set_folder_path('Art/Labels')
        a.set_actor_enable_collision(False);c=a.get_component_by_class(u.TextRenderComponent)
        c.set_text(u.Text(label['text']));c.set_world_size(100)
        c.set_horizontal_alignment(u.HorizTextAligment.EHTA_CENTER)
        c.set_vertical_alignment(u.VerticalTextAligment.EVRTA_TEXT_CENTER)
        c.set_text_material(TEXT_MATERIAL);c.set_editor_property('cast_shadow',False)
        size=c.get_text_local_size()
        if size.y>0 and size.z>0:
            # The distance-field cell includes padding above/below the visible ink.
            c.set_x_scale(label['width']*100/size.y);c.set_y_scale(label['height']*100*1.8/size.z)
        # Vertex colour is a linear UNorm attribute, not an sRGB texture sample.
        c.set_text_render_color(u.Color(*[round(255*max(0,min(1,v))) for v in label['color']],255))
        if label.get('source_instance') in moving_names and label.get('source_instance') in actors_by_name:
            c.set_mobility(u.ComponentMobility.MOVABLE)
            a.attach_to_actor(actors_by_name[label['source_instance']],u.Name('None'),u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,False)
    cameras=[]
    for c in data['cameras']:
        a=EA.spawn_actor_from_class(u.CameraActor,location(c['location']),camrot(c['rotation']))
        a.set_actor_label(c['name']);a.camera_component.set_field_of_view(c['fov']);a.camera_component.set_editor_property('constrain_aspect_ratio',False)
        a.set_editor_property('tags',[u.Name('SkywardCamera:'+c['name'])])
        a.set_folder_path('Cameras');cameras.append(a)
    lights_by_name={}
    for i,l in enumerate(data['lights']):
        if l['type']=='SUN':
            a=EA.spawn_actor_from_class(u.DirectionalLight,location(l['location']),camrot(l['rotation']));c=a.light_component
            c.set_intensity(20 if plane_scene else 35000);c.set_editor_property('atmosphere_sun_light',True);c.set_editor_property('forward_shading_priority',1)
            if plane_scene:c.set_editor_property('light_source_angle',5.0)
        elif l['type']=='SPOT':
            a=EA.spawn_actor_from_class(u.SpotLight,location(l['location']),camrot(l['rotation']));c=a.light_component
            c.set_intensity(l['energy']*7);c.set_editor_property('attenuation_radius',175)
            c.set_editor_property('outer_cone_angle',27.5);c.set_editor_property('inner_cone_angle',15)
            c.set_editor_property('cast_shadows',False);c.set_editor_property('source_radius',4.5)
        else:
            a=EA.spawn_actor_from_class(u.RectLight,location(l['location']),camrot(l['rotation']));c=a.light_component
            factor=(2 if 'window' in l['name'].lower() else 7) if plane_scene else 9
            c.set_intensity(l['energy']*factor);c.set_editor_property('source_width',l['size']*100);c.set_editor_property('source_height',l['size']*100)
            c.set_editor_property('attenuation_radius',1000 if name=='L_Airport_Gate07' else 450)
            if plane_scene and any(t in l['name'].lower() for t in ('window','practical','daylight')):c.set_editor_property('cast_shadows',False)
        c.set_light_color(u.LinearColor(*l['color'],1));c.set_mobility(u.ComponentMobility.MOVABLE);a.set_actor_label(l['name']);a.set_folder_path('Lighting')
        a.set_editor_property('tags',[u.Name('SkywardLight:'+l['name'])]);lights_by_name[l['name']]=a
    # Save the same authored initial states that runtime applies at startup.
    # Streams and small status indicators never become invisible blockers.
    for item in data.get('interactions',[]):
        if item.get('kind')!='control':continue
        index=int(item.get('initial_state',0))
        assert len(item.get('states',[]))>=2,item
        for spec in item.get('targets',[]):
            if 'actor' in spec:
                actor=actors_by_name[spec['actor']];component=actor.static_mesh_component
                if 'visible_states' in spec:actor.set_actor_hidden_in_game(index not in spec['visible_states'])
                if spec.get('collision') is False:
                    actor.set_actor_enable_collision(False);component.set_collision_profile_name('NoCollision')
                if 'materials' in spec:
                    names=set(spec['materials']+[spec.get('slot_material',spec['materials'][0])])
                    slot=next((i for i in range(component.get_num_materials()) if component.get_material(i) and component.get_material(i).get_name() in names),None)
                    assert slot is not None,{'missing_control_material_slot':spec['actor']}
                    material=u.load_asset('/Game/Art/Materials/Instances/'+spec['materials'][index]);assert material,spec
                    component.set_material(slot,material)
            if 'light' in spec:lights_by_name[spec['light']].light_component.set_intensity(float(spec['intensity_states'][index]))
    if plane_scene:
        # Low-cost indirect-light approximation for the compatible SM5 runtime.
        layout=data.get('layout',{})
        if layout:
            cabin_end=float(layout.get('rear_service_end_y_m',layout.get('cabin_end_y_m',max(layout.get('economy_rows',[12.5]))+3.0)))
            bounce_y=list(range(150,math.ceil(cabin_end*100)+1,300))+[-130,-280]
        else:bounce_y=[150,450,750,1050,-130]
        for y in bounce_y:
            a=EA.spawn_actor_from_class(u.RectLight,u.Vector(0,-y,105),u.Rotator(pitch=-90,yaw=0,roll=0));c=a.light_component
            c.set_mobility(u.ComponentMobility.MOVABLE);c.set_intensity(100 if y>0 else 75)
            prop(c,source_width=220,source_height=220,attenuation_radius=360,cast_shadows=False)
            c.set_light_color(u.LinearColor(.83,.90,1,1));a.set_actor_label('Ceiling bounce approximation');a.set_folder_path('Lighting/Bounce')
            a=EA.spawn_actor_from_class(u.PointLight,u.Vector(0,-y,155));c=a.light_component
            c.set_mobility(u.ComponentMobility.MOVABLE);c.set_intensity(160)
            prop(c,attenuation_radius=380,cast_shadows=False,source_radius=65)
            c.set_light_color(u.LinearColor(.84,.9,1,1));a.set_actor_label('Soft indirect fill');a.set_folder_path('Lighting/Bounce')
        for zone in layout.get('navigation_floors',[]):
            if zone.get('slope') or float(zone.get('height',0))>-.5:continue
            xmin,xmax,ymin,ymax=zone['rect'];floor=float(zone['height'])
            number=max(1,math.ceil((ymax-ymin)/2.7))
            for index in range(number):
                y=ymin+(index+.5)*(ymax-ymin)/number
                a=EA.spawn_actor_from_class(u.PointLight,location(((xmin+xmax)/2,y,floor+1.25)))
                c=a.light_component;c.set_mobility(u.ComponentMobility.MOVABLE);c.set_intensity(110)
                prop(c,attenuation_radius=270,cast_shadows=False,source_radius=45)
                c.set_light_color(u.LinearColor(1,.89,.74,1));a.set_actor_label(zone['name']+' warm service fill '+str(index+1));a.set_folder_path('Lighting/LowerHold')
    if plane_scene and data.get('layout',{}).get('exterior_revision'):
        # SM5 exterior daylight fill has its own channel; cabin fittings keep their reviewed lighting.
        for title,pitch,yaw,power in [('Exterior daylight key',-35,-120,160),('Exterior broad sky fill',-18,45,65),('Exterior underside bounce',35,-90,30)]:
            a=EA.spawn_actor_from_class(u.DirectionalLight,u.Vector(0,0,1000),u.Rotator(pitch=pitch,yaw=yaw,roll=0));c=a.light_component
            c.set_mobility(u.ComponentMobility.MOVABLE);c.set_intensity(power);c.set_editor_property('light_source_angle',5.0);c.set_editor_property('forward_shading_priority',10 if title=='Exterior daylight key' else 0)
            c.set_editor_property('lighting_channels',u.LightingChannels(channel0=False,channel1=True,channel2=False));c.set_editor_property('cast_shadows',title=='Exterior daylight key');a.set_actor_label(title);a.set_folder_path('Lighting/Exterior')
    sky=EA.spawn_actor_from_class(u.SkyLight,u.Vector(0,0,600));sky.light_component.set_mobility(u.ComponentMobility.MOVABLE)
    sky.light_component.set_editor_property('real_time_capture',True);sky.light_component.set_intensity(.65 if plane_scene else .8)
    EA.spawn_actor_from_class(u.SkyAtmosphere,u.Vector(0,0,0))
    if plane_scene:
        dome=EA.spawn_actor_from_class(u.StaticMeshActor,u.Vector(0,0,0));dome.set_actor_label('SkyCloudDome')
        dome.static_mesh_component.set_static_mesh(u.load_asset('/Engine/BasicShapes/Sphere'))
        dome.static_mesh_component.set_material(0,u.load_asset('/Game/Art/Materials/M_CloudySky'))
        dome.static_mesh_component.set_collision_profile_name('NoCollision')
        dome.static_mesh_component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION);dome.set_actor_enable_collision(False)
        dome.static_mesh_component.set_editor_property('cast_shadow',False);dome.set_actor_scale3d(u.Vector(1000,1000,1000))
        sky.light_component.set_editor_property('source_type',u.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
        sky.light_component.set_editor_property('cubemap',SKY_CUBE);sky.light_component.set_editor_property('real_time_capture',False)
        sky.light_component.set_editor_property('lower_hemisphere_is_black',True)
        sky.light_component.set_lower_hemisphere_color(u.LinearColor(.22,.27,.34,1))
    pp=EA.spawn_actor_from_class(u.PostProcessVolume,u.Vector(0,0,0));pp.set_editor_property('unbound',True)
    settings=pp.get_editor_property('settings')
    ev=10 if name=='L_Airport_Gate07' else (6.5 if plane_scene else 6)
    prop(settings,override_auto_exposure_method=True,auto_exposure_method=u.AutoExposureMethod.AEM_HISTOGRAM,override_auto_exposure_min_brightness=True,auto_exposure_min_brightness=ev,override_auto_exposure_max_brightness=True,auto_exposure_max_brightness=ev,override_bloom_intensity=True,bloom_intensity=.12,override_vignette_intensity=True,vignette_intensity=0,override_motion_blur_amount=True,motion_blur_amount=0)
    pp.set_editor_property('settings',settings)
    if plane_scene:
        import reticle13
        prop(settings,override_ambient_occlusion_intensity=True,ambient_occlusion_intensity=.35,override_ambient_occlusion_radius=True,ambient_occlusion_radius=25,override_film_grain_intensity=True,film_grain_intensity=0,override_scene_fringe_intensity=True,scene_fringe_intensity=0,override_depth_of_field_focal_distance=True,depth_of_field_focal_distance=0)
        pp.set_editor_property('settings',settings)
        pp.add_or_update_blendable(reticle13.build(),1.0)
    if plane_scene:
        # Simple invisible bounds make first-person boundaries independent of visual glass normals.
        bounds=[]
        for side in (-1,1):
            bounds.extend([(f'COL_CabinSide_{side}',(side*2.41,5.75,1.3),(.10,11.5,2.6)),(f'COL_ServiceSide_{side}',(side*2.43,12.64,1.3),(.10,2.28,2.6)),(f'COL_CockpitSide_{side}',(side*1.71,-1.25,1.3),(.12,2.5,2.6))])
        bounds.append(('COL_FrontWindscreen',(0,-2.58,1.8),(3.4,.10,1.3)))
        bounds.append(('COL_RearBulkhead',(0,13.77,1.3),(4.82,.10,2.6)))
        for side in (-1,1):
            bounds.append((f'COL_ForwardGalley_{side}',(side*1.72,.48,1.10),(1.22,.67,2.20)))
            bounds.append((f'COL_VanityFootprint_{side}',(side*2.05,12.19,.98),(.43,.66,1.96)))
            bounds.append((f'COL_ToiletFootprint_{side}',(side*1.77,12.92,.98),(.50,.60,1.96)))
        bounds.append(('COL_AftGalley',(0,13.34,1.10),(2.15,.67,2.20)))
        # An eye-height sphere otherwise clears the tops of chairs. These footprints
        # keep the fixed-height art tour from walking through the seating rows.
        for index,instance in enumerate(data['instances']):
            if instance['asset'] in ('SM_Plane_Seat','SM_Plane_SeatPair'):
                x,y,z=instance['location'];width=1.46 if instance['asset']=='SM_Plane_SeatPair' else .77
                bounds.append((f'COL_SeatFootprint_{index}',(x,y+.02,.98),(width,.67,1.96)))
        if data.get('navigation_bounds'):
            bounds=[(b['name'],b['location'],b['size']) for b in data['navigation_bounds']]
        for label,pos,size in bounds:
            a=EA.spawn_actor_from_class(u.StaticMeshActor,location(pos));a.set_actor_label(label);a.set_folder_path('Collision/ArtTour')
            c=a.static_mesh_component;c.set_static_mesh(u.load_asset('/Engine/BasicShapes/Cube'))
            a.set_actor_scale3d(u.Vector(*size));c.set_collision_profile_name('BlockAll');a.set_actor_enable_collision(True)
            c.set_collision_response_to_channel(u.CollisionChannel.ECC_VISIBILITY,next(getattr(u.CollisionResponseType,n) for n in dir(u.CollisionResponseType) if n.lower().endswith('ignore')))
            c.set_editor_property('visible',False);c.set_editor_property('cast_shadow',False);a.set_actor_hidden_in_game(True)
    start=next((a for a in cameras if a.get_actor_label()=='CAM_Plane_Business07'),cameras[0])
    player=EA.spawn_actor_from_class(u.PlayerStart,start.get_actor_location(),start.get_actor_rotation());player.set_actor_label('ArtTour_Start')
    # Native component overrides are saved on the placed pawn instance for reliable PIE/standalone behavior.
    pawn=EA.spawn_actor_from_class(u.load_asset('/Game/Gameplay/BP_ArtTourPawn').generated_class(),start.get_actor_location(),start.get_actor_rotation())
    pawn.set_actor_label('ArtTour_Pawn');pawn.set_editor_property('auto_possess_player',u.AutoReceiveInput.PLAYER0)
    pawn.set_editor_property('base_eye_height',0)
    move=pawn.get_component_by_class(u.FloatingPawnMovement)
    prop(move,max_speed=190,acceleration=900,deceleration=1100,snap_to_plane_at_start=True)
    move.set_plane_constraint_normal(u.Vector(0,0,1));move.set_plane_constraint_origin(u.Vector(0,0,162));move.set_plane_constraint_enabled(True)
    pawn.get_component_by_class(u.SphereComponent).set_sphere_radius(18)
    visual=pawn.get_component_by_class(u.StaticMeshComponent)
    if visual:visual.set_visibility(False);visual.set_hidden_in_game(True)
    u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(start.get_actor_location(),start.get_actor_rotation())
    LS.save_current_level();u.EditorAssetLibrary.save_directory('/Game',only_if_is_dirty=True,recursive=True)
    REPORT['maps'].append({'map':map_path,'mesh_actors':count,'native_label_actors':len(data.get('labels',[])),'moving_interaction_actors':sorted(moving_names),'cameras':[a.get_actor_label() for a in cameras],'start_cm':list(start.get_actor_location().to_tuple())})

def interaction_material_preflight():
    """Inactive pages and control states must survive a clean source rebuild."""
    required=set()
    for scene in DATA['scenes'].values():
        for item in scene.get('interactions',[]):
            if item.get('kind')=='screen':required.update(item.get('pages',[]));required.add(item['slot_material'])
            for target in item.get('targets',[]):
                required.update(target.get('materials',[]))
                if target.get('slot_material'):required.add(target['slot_material'])
    source_missing=sorted(required-set(DATA['materials']))
    native_missing=sorted(name for name in required if not u.load_asset('/Game/Art/Materials/Instances/'+name))
    REPORT['interaction_material_preflight']={'required_count':len(required),'required_names':sorted(required),'source_missing':source_missing,'native_missing':native_missing,'status':'FAILED' if source_missing or native_missing else 'SUCCESS'}
    if source_missing or native_missing:
        raise RuntimeError('Interaction material preflight failed; missing source definitions: '+', '.join(source_missing)+'; missing native assets: '+', '.join(native_missing))

def main():
    mats=materials();interaction_material_preflight();meshes=imports(mats);gm=gameplay()
    for name,data in DATA['scenes'].items():assemble(name,data,meshes,gm)
    LS.load_level('/Game/Maps/L_Plane_Reference')
    dome=next(a for a in EA.get_all_level_actors() if a.get_actor_label()=='SkyCloudDome')
    REPORT['sky_collision_after_reload']={'actor_enabled':dome.get_actor_enable_collision(),'component_mode':str(dome.static_mesh_component.get_collision_enabled()),'profile':str(dome.static_mesh_component.get_collision_profile_name()),'casts_shadow':dome.static_mesh_component.get_editor_property('cast_shadow')}
    assert not dome.get_actor_enable_collision(),REPORT['sky_collision_after_reload']
    assert str(dome.static_mesh_component.get_collision_profile_name())=='NoCollision',REPORT['sky_collision_after_reload']
    REPORT['navigation_bounds_after_reload']=[{'name':a.get_actor_label(),'profile':str(a.static_mesh_component.get_collision_profile_name()),'pawn_response':str(a.static_mesh_component.get_collision_response_to_channel(u.CollisionChannel.ECC_PAWN)),'visibility_response':str(a.static_mesh_component.get_collision_response_to_channel(u.CollisionChannel.ECC_VISIBILITY)),'visible':a.static_mesh_component.get_editor_property('visible')} for a in EA.get_all_level_actors() if a.get_actor_label().startswith('COL_')]
    expected_bounds=len(DATA['scenes']['L_Plane_Reference'].get('navigation_bounds',[])) or 41
    assert len(REPORT['navigation_bounds_after_reload'])==expected_bounds
    REPORT['layout']=DATA['scenes']['L_Plane_Reference'].get('layout',{})
    interactive_names={item['actor'] for item in DATA['scenes']['L_Plane_Reference'].get('interactions',[]) if item.get('motion') or item.get('kind')=='door'}
    REPORT['movable_interactions_after_reload']=[{'actor':a.get_actor_label(),'mobility':str(a.static_mesh_component.get_editor_property('mobility'))} for a in EA.get_all_level_actors() if isinstance(a,u.StaticMeshActor) and a.get_actor_label() in interactive_names]
    assert len(REPORT['movable_interactions_after_reload'])==len(interactive_names)
    assert all('MOVABLE' in item['mobility'] for item in REPORT['movable_interactions_after_reload'])
    assert all('BLOCK' in a['pawn_response'] and 'IGNORE' in a['visibility_response'] and not a['visible'] for a in REPORT['navigation_bounds_after_reload'])
    interaction_material_preflight()
    REPORT['status']='SUCCESS'
    (ROOT/'ArtBible'/'UnrealBuildReport.json').write_text(json.dumps(REPORT,indent=2))
    u.log('SKYWARD_BUILD_SUCCESS')

try:main()
except Exception:
    REPORT['status']='FAILED';REPORT['error']=traceback.format_exc()
    (ROOT/'ArtBible'/'UnrealBuildReport.json').write_text(json.dumps(REPORT,indent=2))
    raise
