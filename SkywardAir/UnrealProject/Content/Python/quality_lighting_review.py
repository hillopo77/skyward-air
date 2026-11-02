"""Inspect the imported material bindings and review soft interior lighting in-engine."""
import unreal as u, json, time, traceback
from pathlib import Path
R=Path(__file__).resolve().parents[3];ML=u.MaterialEditingLibrary
LS=u.get_editor_subsystem(u.LevelEditorSubsystem);EA=u.get_editor_subsystem(u.EditorActorSubsystem)
LS.load_level('/Game/Maps/L_Plane_Reference')
report={'materials':{},'slots':{},'lights':[]}
for name in ('MI_Plane_Blue','MI_Plane_DisplayBlack','MI_Plane_Dial','MI_Plane_InstrumentGlass','MI_Plane_Glass'):
    mi=u.load_asset('/Game/Art/Materials/Instances/'+name)
    report['materials'][name]={'parent':mi.get_editor_property('parent').get_path_name(),'base':str(ML.get_material_instance_vector_parameter_value(mi,'BaseColor')),'rough':ML.get_material_instance_scalar_parameter_value(mi,'Roughness'),'surface':ML.get_material_instance_scalar_parameter_value(mi,'SurfaceStrength'),'opacity':ML.get_material_instance_scalar_parameter_value(mi,'GlassOpacity')}
for aid in ('SM_Plane_Seat','SM_Plane_AnalogDashboard','SM_Plane_CockpitShell'):
    mesh=u.load_asset('/Game/Art/Meshes/'+aid)
    report['slots'][aid]=[(str(s.material_slot_name),s.material_interface.get_path_name() if s.material_interface else None) for s in mesh.get_editor_property('static_materials')]
for a in EA.get_all_level_actors():
    if isinstance(a,u.Light):
        c=a.light_component
        report['lights'].append({'name':a.get_actor_label(),'intensity':c.get_editor_property('intensity'),'shadows':c.get_editor_property('cast_shadows')})
        if isinstance(a,u.DirectionalLight):c.set_intensity(35)
        elif 'practical' in a.get_actor_label().lower() or 'daylight' in a.get_actor_label().lower():c.set_editor_property('cast_shadows',False)
    if isinstance(a,u.PostProcessVolume):
        settings=a.get_editor_property('settings')
        for k,v in dict(override_ambient_occlusion_intensity=True,ambient_occlusion_intensity=.7,override_ambient_occlusion_radius=True,ambient_occlusion_radius=25).items():settings.set_editor_property(k,v)
        a.set_editor_property('settings',settings)
# Glass Fresnel reflection is separate from its opacity, and must be reduced explicitly.
glass=u.load_asset('/Game/Art/Materials/M_WindowGlass')
spec=ML.create_material_expression(glass,u.MaterialExpressionScalarParameter,-400,360);spec.set_editor_property('parameter_name','GlassSpecular');spec.set_editor_property('default_value',.3)
ML.connect_material_property(spec,'',u.MaterialProperty.MP_SPECULAR);ML.recompile_material(glass)
for name,val in [('MI_Plane_InstrumentGlass',.015),('MI_Plane_Glass',.25)]:
    mi=u.load_asset('/Game/Art/Materials/Instances/'+name);ML.set_material_instance_scalar_parameter_value(mi,'GlassSpecular',val);u.EditorAssetLibrary.save_loaded_asset(mi)
u.EditorAssetLibrary.save_loaded_asset(glass)
LS.save_current_level()
(R/'ArtBible'/'QualityMaterialInspection.json').write_text(json.dumps(report,indent=2))
# Show the actual screen-space result after temporal history and shaders settle.
u.SystemLibrary.execute_console_command(None,'r.AntiAliasingMethod 2')
u.SystemLibrary.execute_console_command(None,'r.PostProcessAAQuality 6')
shots=[('CAM_Plane_SeatStudy','UE_15_soft_light_seat.png'),('CAM_Plane_CockpitWide','UE_16_soft_light_cockpit.png')]
state={'i':0,'after':time.monotonic()+15,'busy':False,'phase':'shot'}
def tick(dt):
    if state['busy'] or time.monotonic()<state['after']:return
    state['busy']=True
    try:
        if state['phase']=='shot':
            cam,file=shots[state['i']];a=next(a for a in EA.get_all_level_actors() if isinstance(a,u.CameraActor) and a.get_actor_label().startswith(cam))
            state['task']=u.AutomationLibrary.take_high_res_screenshot(1440,900,str(R/'Screenshots'/file),a,delay=3)
            state['phase']='next';state['after']=time.monotonic()+9
        else:
            state['i']+=1
            if state['i']==len(shots):u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
            else:state['phase']='shot';state['after']=time.monotonic()+4
    except Exception:
        (R/'ArtBible'/'QualityReviewError.txt').write_text(traceback.format_exc());u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
    finally:state['busy']=False
handle=u.register_slate_post_tick_callback(tick);u.EditorPythonScripting.set_keep_python_script_alive(True)
