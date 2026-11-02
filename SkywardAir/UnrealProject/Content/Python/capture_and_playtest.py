"""Real UE viewport captures and PIE navigation smoke test. Run in the full editor.
Produces actual engine screenshots, separate from Blender lookdev images.
"""
import unreal as u, time, json, traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
LS=u.get_editor_subsystem(u.LevelEditorSubsystem)
EA=u.get_editor_subsystem(u.EditorActorSubsystem)
UE=u.get_editor_subsystem(u.UnrealEditorSubsystem)
shots=[('L_Plane_Reference',cam,file) for cam,file in [('CAM_Plane_Business','UE_36_business.png'),('CAM_Plane_Economy','UE_37_economy.png'),('CAM_Plane_ClassCurtain','UE_38_class_curtain.png'),('CAM_Plane_CockpitEntry','UE_39_cockpit_entry.png'),('CAM_Plane_Vestibule','UE_40_vestibule.png'),('CAM_Plane_Lavatory','UE_41_lavatory.png'),('CAM_Plane_ServiceAft','UE_42_aft_galley.png'),('CAM_Plane_CockpitWide','UE_43_flightdeck.png')]]
state={'phase':'load','index':0,'after':time.monotonic()+10,'task':None,'frames':0,'began':time.monotonic()}
results={'captures':[],'navigation':[],'status':'RUNNING','revision':'06 — business and economy, curtain divider, service vestibule, enlarged cockpit entry'}
visual_only='-SkywardVisualOnly' in u.SystemLibrary.get_command_line()
if visual_only:
    preceding=json.loads((ROOT/'ArtBible'/'EngineValidation.json').read_text())
    assert preceding['status']=='SUCCESS'
    results['navigation']=preceding['navigation'];results['pawn_settings']=preceding.get('pawn_settings',{})
    results['navigation_retained_from_verified_unchanged_controller']=True
tests=[
 {'name':'left aisle through both classes','start':(-118,-250,162),'dir':(0,-1,0),'duration':5.5,'axis':1,'range':(-1350,-1200)},
 {'name':'right aisle through both classes','start':(118,-250,162),'dir':(0,-1,0),'duration':5.5,'axis':1,'range':(-1350,-1200)},
 {'name':'front service cross aisle','start':(-110,-145,162),'dir':(1,0,0),'duration':1.25,'axis':0,'range':(90,145)},
 {'name':'cross reinforced cockpit doorway','start':(0,-80,162),'dir':(0,1,0),'duration':.8,'axis':1,'range':(40,100)},
 {'name':'standing space across rear of flightdeck','start':(-70,75,162),'dir':(1,0,0),'duration':.75,'axis':0,'range':(40,90)},
 {'name':'cockpit entry ends before radio pedestal','start':(0,40,162),'dir':(0,1,0),'duration':1,'axis':1,'range':(118,138)},
 {'name':'service vestibule into business','start':(118,-150,162),'dir':(0,-1,0),'duration':.85,'axis':1,'range':(-320,-260)},
 {'name':'right curtain opening is walkable','start':(118,-530,162),'dir':(0,-1,0),'duration':.85,'axis':1,'range':(-710,-650)},
 {'name':'left curtain opening is walkable','start':(-118,-530,162),'dir':(0,-1,0),'duration':.85,'axis':1,'range':(-710,-650)},
 {'name':'center class bulkhead blocks player','start':(0,-640,162),'dir':(0,1,0),'duration':.65,'axis':1,'range':(-612,-600)},
 {'name':'enter right lavatory','start':(85,-1445,162),'dir':(1,0,0),'duration':.55,'axis':0,'range':(150,190)},
 {'name':'enter left lavatory','start':(-85,-1445,162),'dir':(-1,0,0),'duration':.55,'axis':0,'range':(-190,-150)},
 {'name':'extended rear service access','start':(0,-1370,162),'dir':(0,-1,0),'duration':.7,'axis':1,'range':(-1510,-1430)},
 {'name':'galley cabinet blocks player','start':(172,-150,162),'dir':(0,1,0),'duration':1.1,'axis':1,'range':(-120,-90)},
 {'name':'side wall blocks between economy rows','start':(111,-750,162),'dir':(1,0,0),'duration':2,'axis':0,'range':(190,240)},
 {'name':'business seat blocks player','start':(118,-305,162),'dir':(1,0,0),'duration':1,'axis':0,'range':(132,142)},
 {'name':'economy seat blocks player','start':(118,-805,162),'dir':(1,0,0),'duration':1,'axis':0,'range':(125,139)}]
if '-SkywardNavOnly' in u.SystemLibrary.get_command_line():
    previous=ROOT/'ArtBible'/'EngineValidation.json'
    if previous.exists():results['captures']=json.loads(previous.read_text()).get('captures',[])
    state['phase']='play_load';results['mode']='Navigation only; retained preceding visual captures'
def write(): (ROOT/'ArtBible'/'EngineValidation.json').write_text(json.dumps(results,indent=2))
def done():
    u.unregister_slate_post_tick_callback(handle);write();u.SystemLibrary.quit_editor()

def reposition(pawn,target):
    movement=pawn.get_component_by_class(u.FloatingPawnMovement)
    movement.stop_movement_immediately();pawn.consume_movement_input_vector()
    result=pawn.set_actor_location(target,False,True)
    loc=pawn.get_actor_location()
    results['navigation'].append({'test':'test reposition','target_cm':[target.x,target.y,target.z],'actual_cm':[loc.x,loc.y,loc.z],'result':str(result),'passed':((loc.x-target.x)**2+(loc.y-target.y)**2+(loc.z-target.z)**2)**.5<2})
def tick(dt):
    # Loading worlds and screenshots can pump Slate recursively.
    if state.get('busy'):return
    state['busy']=True
    try:
        now=time.monotonic()
        if now-state['began']>600:raise RuntimeError('Capture/test exceeded ten minute timeout')
        if now<state['after']:return
        p=state['phase']
        if p=='load':
            name,cam,file=shots[state['index']]
            if state['index']==0 and not LS.load_level('/Game/Maps/'+name):raise RuntimeError('Cannot load '+name)
            if state['index']==0:
                u.SystemLibrary.execute_console_command(UE.get_editor_world(),'r.HighResScreenshotDelay 16')
                u.SystemLibrary.execute_console_command(UE.get_editor_world(),'r.TemporalAASamples 16')
            state['phase']='capture';state['after']=now+12
        elif p=='capture':
            name,cam,file=shots[state['index']]
            camera=next(a for a in EA.get_all_level_actors() if isinstance(a,u.CameraActor) and a.get_actor_label().startswith(cam))
            state['capture_time']=time.time()
            state['task']=u.AutomationLibrary.take_high_res_screenshot(1440,900,str(ROOT/'Screenshots'/file),camera,delay=3)
            state['phase']='await_capture';state['after']=now+6
        elif p=='await_capture':
            name,cam,file=shots[state['index']]
            path=ROOT/'Screenshots'/file
            if not path.exists() or path.stat().st_mtime<state['capture_time']:
                state['after']=now+3;return
            results['captures'].append({'map':name,'camera':cam,'file':file,'bytes':path.stat().st_size});write()
            state['index']+=1
            state['phase']='load' if state['index']<len(shots) else ('finish' if visual_only else 'play_load');state['after']=now+2
        elif p=='play_load':
            LS.editor_request_begin_play()
            state['phase']='play_start';state['after']=now+5
        elif p=='play_start':
            world=UE.get_game_world()
            pawn=u.GameplayStatics.get_player_pawn(world,0) if world else None
            if not pawn:raise RuntimeError('PIE has no possessed pawn')
            state['pawn']=pawn
            movement=pawn.get_component_by_class(u.FloatingPawnMovement)
            results['pawn_settings']={'max_speed_cm_s':movement.get_editor_property('max_speed'),'collision_radius_cm':pawn.get_component_by_class(u.SphereComponent).get_unscaled_sphere_radius()}
            state['test_index']=0;state['phase']='test_start'
        elif p=='test_start':
            t=tests[state['test_index']];reposition(state['pawn'],u.Vector(*t['start']))
            state['until']=now+t['duration'];state['phase']='test_move'
        elif p=='test_move':
            t=tests[state['test_index']];pawn=state['pawn'];pawn.add_movement_input(u.Vector(*t['dir']),1)
            if now>state['until']:
                loc=pawn.get_actor_location()
                pos=[loc.x,loc.y,loc.z];value=pos[t['axis']]
                results['navigation'].append({'test':t['name'],'start_cm':list(t['start']),'end_cm':pos,'accepted_range_cm':list(t['range']),'passed':t['range'][0]<value<t['range'][1]});write()
                state['test_index']+=1
                if state['test_index']<len(tests):state['phase']='test_start';state['after']=now+.25
                else:LS.editor_request_end_play();state['phase']='finish';state['after']=now+3
        elif p=='finish':
            results['status']='SUCCESS' if all(v['passed'] for v in results['navigation']) else 'FAILED';done()
    except Exception:
        results['status']='FAILED';results['error']=traceback.format_exc();done()
    finally:
        state['busy']=False
write()
handle=u.register_slate_post_tick_callback(tick)
u.EditorPythonScripting.set_keep_python_script_alive(True)
