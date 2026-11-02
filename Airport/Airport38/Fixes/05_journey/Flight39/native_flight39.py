"""Root invokes this after importing Flight39 assets and placing new instances."""


def probe_api(u):
    """Read-only API preflight in root's existing editor, before mutations."""
    required={
      'Actor':['set_actor_location_and_rotation','set_actor_relative_rotation','attach_to_actor','detach_from_actor','get_attach_parent_actor','root_component'],
      'SceneComponent':['set_mobility'],
      'MathLibrary':['transform_location','inverse_transform_location','make_rot_from_yz','make_rot_from_z'],
      'TextRenderComponent':['set_text','set_world_size','set_text_render_color'],
      'LightComponent':['set_intensity','set_light_color','set_cast_shadows'],
    }
    missing=[cls+'.'+name for cls,names in required.items() for name in names if not hasattr(getattr(u,cls),name)]
    audio={kind:next((n for n in (kind+'2d',kind+'_2d') if hasattr(u.GameplayStatics,n)),None) for kind in ('spawn_sound','play_sound')}
    return dict(passed=not missing,missing=missing,checked=sum(len(v) for v in required.values()),optional_audio_aliases=audio)


def apply_native(ctx):
    u=ctx.u;EA=ctx.EA;D=ctx.D;meta=D['flight39'];actors={a.get_actor_label():a for a in EA.get_all_level_actors()}
    def spawn(cls,name,pos,rot=None):
        a=actors.get(name)
        if not a:a=EA.spawn_actor_from_class(cls,ctx.v(pos));a.set_actor_label(name);actors[name]=a
        a.set_actor_location(ctx.v(pos),False,True)
        if rot:a.set_actor_rotation(rot,False)
        a.root_component.set_mobility(u.ComponentMobility.MOVABLE);return a
    carrier=spawn(u.StaticMeshActor,meta['carrier'],meta['stand']);carrier.static_mesh_component.set_static_mesh(None);carrier.set_actor_enable_collision(False)
    replaced=[]
    for key,aid in [('SM_Plane_ExteriorAirframe',meta['airframe_fixed_asset']),('SM_Plane_AnalogDashboard',meta['dashboard_fixed_asset'])]:
        a=next((a for a in actors.values() if any(str(t)=='Skyward:'+key for t in a.tags)),None)
        if not a:raise RuntimeError('Native authored aircraft actor missing: '+key)
        a.static_mesh_component.set_static_mesh(ctx.mesh(aid));replaced.append(key)
    if meta.get('gear_fixed_asset'):
        key='SM_Plane_LandingGear';a=next((a for a in actors.values() if any(str(t)=='Skyward:'+key for t in a.tags)),None)
        if not a:raise RuntimeError('Native corrected landing gear actor missing')
        a.static_mesh_component.set_static_mesh(ctx.mesh(meta['gear_fixed_asset']));replaced.append(key)
    for name in meta['moving_names']:
        a=actors.get(name)
        if not a:raise RuntimeError('Dynamic authored part was incorrectly grouped or not placed: '+name)
        a.static_mesh_component.set_mobility(u.ComponentMobility.MOVABLE);a.set_actor_enable_collision(False)
    # Actual runway/apron top is the tyre contact plane. Collision belongs to
    # this visible mesh, not a giant invisible play floor under the whole map.
    support=[]
    for a in actors.values():
        for c in a.get_components_by_class(u.StaticMeshComponent):
            mesh=c.static_mesh
            if mesh and mesh.get_name() in meta['ground_support_assets']:
                c.set_collision_profile_name('BlockAll');mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE);support.append(a.get_actor_label())
    text=spawn(u.TextRenderActor,'Flight39 Status',meta['status_text_position'],u.Rotator(yaw=-90));c=text.get_component_by_class(u.TextRenderComponent)
    c.set_text('POWER OFF');c.set_world_size(3.2);c.set_text_render_color(u.Color(169,222,205,255));text.set_actor_enable_collision(False)
    chase=spawn(u.CameraActor,'Flight39 Chase',[16,74,17]);chase.set_actor_rotation(u.MathLibrary.find_look_at_rotation(chase.get_actor_location(),ctx.v([16,13,1])),False);chase.camera_component.set_field_of_view(76.)
    lights=[]
    for name,pos,colour,intensity,radius in [('Flight39 Beacon',[16,17,3.15],u.LinearColor(1,.12,.045,1),850,700),
        ('Flight39 Taxi left',[15.35,-6.15,-2.85],u.LinearColor(1,.84,.62,1),3600,1600),
        ('Flight39 Taxi right',[16.65,-6.15,-2.85],u.LinearColor(1,.84,.62,1),3600,1600),
        ('Flight39 Landing left',[9,12,-1.2],u.LinearColor(1,.89,.72,1),5200,2400),
        ('Flight39 Landing right',[23,12,-1.2],u.LinearColor(1,.89,.72,1),5200,2400),
        ('Flight39 Nav left',[39.3,21,1.1],u.LinearColor(1,.08,.025,1),45,90),
        ('Flight39 Nav right',[-7.3,21,1.1],u.LinearColor(.08,1,.22,1),45,90)]:
        cls=u.SpotLight if 'Taxi' in name or 'Landing' in name else u.PointLight
        a=spawn(cls,name,pos,u.Rotator(pitch=-4,yaw=90) if cls==u.SpotLight else u.Rotator());lc=a.light_component
        lc.set_intensity(intensity);lc.set_light_color(colour,False);lc.set_editor_property('attenuation_radius',radius);lc.set_cast_shadows(False)
        if cls==u.SpotLight:lc.set_editor_property('outer_cone_angle',28.);lc.set_editor_property('inner_cone_angle',17.)
        a.tags=list(a.tags)+[u.Name('SkywardLight:'+name),u.Name('Airport38PlaneShift16')];lights.append(name)
    # Remove the old grouped pavement rather than placing a second surface
    # over it. Root's placement phase must also honour retired_instances.
    return dict(carrier=carrier.get_actor_label(),replaced=replaced,moving_parts=len(meta['moving_names']),support_components=support,
                status_text=True,chase_camera=True,practical_lights=lights,audio_import='Run import_audio(ctx) after source wav generation')


def import_audio(ctx):
    from pathlib import Path
    u=ctx.u;folder=Path(__file__).parent/'Audio';tasks=[]
    for source in folder.glob('*.wav'):
        task=u.AssetImportTask();task.filename=str(source);task.destination_path=ctx.B+'/Flight39/Audio';task.destination_name=source.stem;task.automated=True;task.replace_existing=True;task.save=True;tasks.append(task)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    for task in tasks:
        for path in task.imported_object_paths:
            a=u.load_asset(path)
            if a and a.get_name()=='Engine39':a.set_editor_property('looping',True);u.EditorAssetLibrary.save_loaded_asset(a)
    return [str(t.filename) for t in tasks]
