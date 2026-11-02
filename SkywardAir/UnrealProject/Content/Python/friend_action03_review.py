"""Focused native review of paired inventory transfer and the emote camera."""
import unreal as u,time,json,math,traceback,hashlib
from pathlib import Path
from friend_action03_model import sample
S={};M=None
R=Path(__file__).resolve().parents[4]/'Animations/FriendRefinement07'

def save(status='RUNNING',**kw):
    (R/S.get('report','NativeReview.json')).write_text(json.dumps({'status':status,'checks':S['checks'],'captures':S['captures'],**kw},indent=2))
def check(name,passed,**kw):
    S['checks'].append({'name':name,'passed':bool(passed),**kw})
    if not passed:raise AssertionError(name+': '+str(kw))
def finish(status,**kw):
    if S.get('input_saved'):M.S['pack'].S['emotes'].process_input=S.pop('input_saved')
    save(status,palm_gaps_cm=S.get('palm_gaps',[]),**kw)
    if S.get('handle'):u.unregister_slate_post_tick_callback(S['handle']);S['handle']=None
    u.SystemLibrary.quit_game(M.S['world'],M.S['game'].P.STATE['pc'],u.QuitPreference.QUIT,False)
def capture(name,now):
    path=R/'Captures'/('FirstPerson06' if S.get('only_fp') else '')/(name+'.png');path.parent.mkdir(parents=True,exist_ok=True)
    S.update(wait=path,requested=time.time(),wait_mono=now)
    u.SystemLibrary.execute_console_command(M.S['world'],'Shot '+('' if name.startswith('Motion/') else 'showui ')+'-nosuffix filename="'+path.as_posix()+'"',M.S['game'].P.STATE['pc'])
def begin_steps(phase,steps,now):
    S.update(phase=phase,steps=steps,index=0,posed=False,next=now+.2)
def angle():
    comp=M.S['demo_friend'].skeletal_mesh_component
    vector=comp.get_socket_location(u.Name('Neck'))-comp.get_socket_location(u.Name('Hips'))
    if 'upright' not in S:S['upright']=vector
    cosine=sum(a*b for a,b in zip(vector.to_tuple(),S['upright'].to_tuple()))/(vector.length()*S['upright'].length())
    return math.degrees(math.acos(max(-1.,min(1.,cosine))))
def palm_gap():
    active=M.S['active'];CP=M.S['pack'];item=active['item'];rotation=item.get_actor_rotation();grip=active['grip_local'];scale=item.get_actor_scale3d()
    wrist=CP.S['avatar'].skeletal_mesh_component.get_socket_location(u.Name('RightHand'))
    palm=wrist+u.MathLibrary.get_right_vector(active['target'].get_actor_rotation())*4+u.Vector(0,0,-2.5)
    point=item.get_actor_location()+u.MathLibrary.get_forward_vector(rotation)*(grip.x*scale.x)+u.MathLibrary.get_right_vector(rotation)*(grip.y*scale.y)+u.MathLibrary.get_up_vector(rotation)*(grip.z*scale.z)
    return (palm-point).length()
def fp_hand_gap():
    active=M.S['active'];item=active['item'];rotation=item.get_actor_rotation();grip=active['grip_local'];scale=item.get_actor_scale3d()
    point=item.get_actor_location()+u.MathLibrary.get_forward_vector(rotation)*(grip.x*scale.x)+u.MathLibrary.get_right_vector(rotation)*(grip.y*scale.y)+u.MathLibrary.get_up_vector(rotation)*(grip.z*scale.z)
    return (M.S['legacy'].S['hands']['R'].get_actor_location()-point).length()

def tick(dt):
    try:
        real=time.monotonic();G=M.S['game'];CP=M.S['pack'];pc=G.P.STATE['pc'];ctrl=CP.S['emotes']
        if S.get('wait'):
            path=S['wait']
            if path.exists() and path.stat().st_mtime>=S['requested']:
                S['captures'].append({'file':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'kind':'native_gameplay'});S.pop('wait');S['index']+=1;S['posed']=False;save()
            elif real-S['wait_mono']>20:raise TimeoutError('Screenshot timed out')
            return
        if real<S['next']:return
        phase=S['phase']
        if phase=='emote_setup':
            pc.set_control_rotation(u.Rotator(pitch=-5.,yaw=-90.,roll=0.))
            S['input_saved']=ctrl.process_input
            ctrl.process_input=lambda dt,now:ctrl.ui.animate(dt,ctrl.opened_at,now) if CP.S['wheel_open'] else None
            CP.open_wheel();check('Native wheel opens independently of paired action',CP.S['wheel_open'])
            ctrl.selection.update(0,-180);ctrl.ui.refresh();S.update(phase='wheel',index=0,next=real+.8);return
        if phase=='setup':
            check('Demo begins before pickup',G.S.get('held') is None)
            check('Empty hands reject transfer',M.request('review_friend')==(False,'no_held_item'))
            G.act({'kind':'pickup','actor':M.S['demo_item'],'point':[-47.,-12.,.8]})
            check('Real pickup holds hammer',G.S['held']==M.S['demo_item'])
            item=G.S['actors'][M.S['demo_item']];lo,hi=item.static_mesh_component.get_local_bounds()
            size=max((hi-lo).to_tuple());check('Enlarged hammer dimensions',42<size<44,length_cm=size)
            S.update(phase='begin_action',index=0,next=real+.8);return
        if phase=='begin_action':
            if S['index']==0:capture('00_HeldFirstPerson',real);return
            M.S['manual_time']=0.;check('First-person action starts',M.request('review_friend')==(True,'started'))
            M.S['manual_time']=M.S['action'].cfg.bend_seconds+.47*M.S['action'].cfg.cycle_seconds;M.update_action();S.update(phase='first_person',index=0,next=real+.6);return
        if phase=='first_person':
            if S['index']==0:
                check('Hidden player hand bones update during action',CP.S['avatar'].get_editor_property('hidden') and palm_gap()<6.,palm_gap_cm=palm_gap())
                check('Visible first-person hand follows the actual grip',fp_hand_gap()<1.,hand_actor_gap_cm=fp_hand_gap())
                pitch=(pc.get_control_rotation().pitch+180)%360-180
                check('Initial camera alignment keeps contact in view',-60<pitch<-48,pitch_degrees=pitch)
                capture('00_FirstPersonContact',real);return
            if S.get('only_fp'):
                M.S['manual_time']=M.S['action'].cfg.pop_time+.12;M.update_action();S.update(phase='fp_release',index=0,next=real+.5);return
            M.cancel('review_first_person');check('First-person cancellation restores held hammer',G.S['held']==M.S['demo_item'])
            M.S['manual_time']=0.;check('Transfer starts',M.request('review_friend')==(True,'started'))
            library=u.get_default_object(u.GameplayStatics);transform=u.Transform()
            cam=library.call_method('BeginDeferredActorSpawnFromClass',(M.S['world'],u.CameraActor,transform,u.SpawnActorCollisionHandlingMethod.ALWAYS_SPAWN,None,u.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT));cam=library.call_method('FinishSpawningActor',(cam,transform,u.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT))
            base=M.S['demo_friend'].get_actor_location();eye=base+u.Vector(-300,-145,145);goal=base+u.Vector(0,-32,95)
            cam.set_actor_location(eye,False,True);cam.set_actor_rotation(u.MathLibrary.find_look_at_rotation(eye,goal),False);cam.camera_component.set_field_of_view(65.);S['cam']=cam
            cfg=M.S['action'].cfg
            span=cfg.pop_time-cfg.bend_seconds
            steps=[('01_Held',0.),('02_Bend',cfg.bend_seconds),('03_Contact',cfg.bend_seconds+.18*span),('04_Load',cfg.bend_seconds+.30*span),('05_FirstYield',cfg.bend_seconds+.40*span),('06_SecondHold',cfg.bend_seconds+.58*span),('07_SecondYield',cfg.bend_seconds+.66*span),('08_FinalHold',cfg.bend_seconds+.98*span),('09_Pop',cfg.pop_time+.05),('10_Upright',cfg.duration+.1)]
            if S['film']:steps=[('Motion/Frame_%04d'%i,min(cfg.duration+.1,i/20)) for i in range(math.ceil((cfg.duration+.1)*20)+1)]
            begin_steps('transfer',steps,real);return
        if phase=='fp_release':
            if S['index']==0:
                check('First-person hand releases the prop after the pop',M.S['legacy'].S['hands']['R'].static_mesh_component.static_mesh==M.S['legacy'].S['hand_meshes']['SM_CH12_ViewHand_R'])
                capture('00_FirstPersonRelease',real);return
            M.S['manual_time']=M.S['action'].cfg.duration+.1;M.update_action()
            check('Hand ownership released after action',not M.S['legacy'].S.get('paired_hand_owner'))
            finish('SUCCESS',scope='Focused native first-person hand placement, camera alignment, pop/release and ownership restoration.');return
        if phase in ['transfer','retrieve']:
            CP.S['force_visible']=True;CP.S['avatar'].set_actor_hidden_in_game(False);pc.set_view_target_with_blend(S['cam'],0)
            for hand in M.S['legacy'].S.get('hands',{}).values():
                if M.valid(hand):hand.static_mesh_component.set_visibility(False,True)
            if S['index']<len(S['steps']):
                name,t=S['steps'][S['index']]
                if not S['posed']:
                    M.S['manual_time']=t;M.update_action();S.update(posed=True,next=real+(.035 if name.startswith('Motion/') else .55));return
                a=angle()
                active=M.S.get('active')
                if active and phase=='transfer':
                    pose=sample(t,M.S['action'].cfg)
                    if pose.phase=='motion':
                        hips=CP.S['avatar'].skeletal_mesh_component.get_socket_location(u.Name('Hips'))
                        S.setdefault('pelvis',[]).append(hips.to_tuple())
                        S.setdefault('feed',[]).append(pose.approach)
                    if pose and pose.phase=='motion' and pose.approach>.95:
                        S.setdefault('palm_gaps',[]).append(palm_gap())
                        wrist=CP.S['avatar'].skeletal_mesh_component.get_socket_location(u.Name('LeftHand'))
                        palm=wrist+u.MathLibrary.get_right_vector(active['target'].get_actor_rotation())*4+u.Vector(0,0,-2.5)
                        hips=active['target'].skeletal_mesh_component.get_socket_location(u.Name('Hips'))
                        point=hips+u.MathLibrary.get_forward_vector(active['target'].get_actor_rotation())*14-u.MathLibrary.get_right_vector(active['target'].get_actor_rotation())*10+u.Vector(0,0,4)
                        S.setdefault('support_gaps',[]).append((palm-point).length())
                if name in ['03_Push1','08_FinalPush','13_Pull']:check(name+' grounded bend',35<a<55,angle_degrees=a)
                if name in ['10_Upright','15_HeldAgain']:check(name+' upright restored',a<8,angle_degrees=a)
                if name=='11_Reach':check('Retrieval starts with item still hidden',G.S['actors'][M.S['demo_item']].get_editor_property('hidden'))
                if name=='13_Pull':check('Visible pull precedes handoff',not G.S['actors'][M.S['demo_item']].get_editor_property('hidden') and G.S.get('held') is None)
                capture(name,real);return
            if phase=='transfer':
                if S.get('pelvis'):
                    span=max(max(p[i] for p in S['pelvis'])-min(p[i] for p in S['pelvis']) for i in range(3))
                    check('Pelvis remains planted throughout the resisted feed',span<.5,maximum_span_cm=span)
                    check('Feed advances without repeated withdrawal',all(b>=a-.00001 for a,b in zip(S['feed'],S['feed'][1:])))
                if S.get('palm_gaps'):check('Contact hand stays on the handle',max(S['palm_gaps'])<6.,max_palm_gap_cm=max(S['palm_gaps']))
                if S.get('support_gaps'):check('Supporting hand reaches its contact point',max(S['support_gaps'])<8.,max_support_gap_cm=max(S['support_gaps']))
                check('One pop per transfer',sum(e['event']=='pop' for e in M.S['events'])==1)
                check('Stored item is hidden once',M.S['concealed']['review_friend']==[M.S['demo_item']] and G.S['actors'][M.S['demo_item']].get_editor_property('hidden'))
                check('No hidden pickup target',not any(t.get('actor')==M.S['demo_item'] for t in G.S['targets']))
                M.S['manual_time']=10.;check('Animated retrieval starts',M.recover('review_friend') and bool(M.S.get('active')) and G.S.get('held') is None)
                begin_steps('retrieve',[('11_Reach',10.65),('12_Reveal',10.9),('13_Pull',11.2),('14_Handoff',11.75),('15_HeldAgain',12.45)],real);return
            check('Same actor returned to hand',G.S['held']==M.S['demo_item'] and not G.S['actors'][M.S['demo_item']].get_editor_property('hidden'))
            check('One recovery event and empty stored inventory',sum(e['event']=='item_recovered' for e in M.S['events'])==1 and not M.S['concealed']['review_friend'])
            check('Pairing releases movement and pose',not M.S.get('active') and not CP.S.get('external_pose'))
            M.S['manual_time']=20.;check('Second transfer starts',M.request('review_friend')[0]);M.S['manual_time']=20.+M.S['action'].cfg.duration+.1;M.update_action()
            M.S['manual_time']=30.;check('Recovery for cancel test starts',M.recover('review_friend'));M.S['manual_time']=31.;M.update_action();M.cancel('review_before_commit')
            check('Early cancellation keeps stored item',M.S['concealed']['review_friend']==[M.S['demo_item']] and G.S.get('held') is None)
            M.S['manual_time']=40.;check('Second recovery starts',M.recover('review_friend'));M.S['manual_time']=41.6;M.update_action();M.cancel('review_after_commit')
            check('Late cancellation hands back same item once',G.S['held']==M.S['demo_item'] and not M.S['concealed']['review_friend'])
            M.S['manual_time']=None;CP.S['force_visible']=False
            S['input_saved']=ctrl.process_input
            # Keep native UI animation running while the harness substitutes
            # for physically holding Z. Otherwise the authored zero-opacity
            # startup state never advances even though the wheel is open.
            ctrl.process_input=lambda dt,now:ctrl.ui.animate(dt,ctrl.opened_at,now) if CP.S['wheel_open'] else None
            CP.open_wheel();check('Native emote wheel opens',CP.S['wheel_open'] and ctrl.view.phase=='orbit')
            ctrl.selection.update(0,-180);ctrl.ui.refresh();S.update(phase='wheel',index=0,next=real+.8);return
        if phase=='wheel':
            if S['index']==0:
                check('Native wheel uses orbit camera',pc.get_view_target()==ctrl.camera)
                panel=ctrl.ui.get('WheelPanel')
                check('Native wheel animates fully visible',panel.get_render_opacity()>.95,opacity=panel.get_render_opacity())
                check('Native widget is attached to viewport',CP.S['widget'].is_in_viewport())
                S['widget_layout']={'panel_visibility':str(panel.get_visibility()),'root_visibility':str(CP.S['widget'].get_visibility()),'geometry':list(ctrl.ui.measure())}
                capture('16_NativeEmoteWheel',real);return
            CP.choose_slot(2);ctrl.process_input=S.pop('input_saved')
            check('Native emote starts and wheel closes',CP.S.get('emote',{}).get('name')=='HipHopDancing' and not CP.S['wheel_open'] and not ctrl.input_locked)
            S['body_yaw']=CP.S['avatar'].get_actor_rotation().yaw
            rotation=pc.get_control_rotation();pc.set_control_rotation(u.Rotator(pitch=rotation.pitch,yaw=rotation.yaw+75,roll=0.));S.update(phase='orbit',index=0,next=real+.65);return
        if phase=='orbit':
            if S['index']==0:
                check('Orbit camera leaves character facing fixed',abs(CP.S['avatar'].get_actor_rotation().yaw-S['body_yaw'])<1.)
                capture('17_NativeEmoteOrbit',real);return
            G.P.STATE['pawn'].add_movement_input(u.Vector(1,0,0),1.,False);S.update(phase='return',next=real+.8);return
        if phase=='return':
            check('Movement smoothly returns first person',not ctrl.view.active and pc.get_view_target()==G.P.STATE['pawn'])
            check('Character runtime remains installed',CP.S['installed'])
            check('Review uses temporary F8 only',M.S['key_name']=='F8' and json.loads((M.R/'config.json').read_text())['hotkey'] is None)
            finish('SUCCESS',events=M.S['events'],widget_layout=S.get('widget_layout'),scope='Native local game: pickup, animation timing, retrieval, cancellation, real UMG, camera orbit and movement return. Emote selection uses public controller methods; physical hold-Z dragging and networking are not validated.');return
    except Exception:finish('FAILED',error=traceback.format_exc())

def start(module):
    global M;M=module
    only='-FriendEmoteOnlyReview' in M.S['game'].CMD;fp='-FriendFirstPersonReview' in M.S['game'].CMD
    S.update(started=time.monotonic(),checks=[],captures=[],only_fp=fp,film='-FriendMotionFilm06' in M.S['game'].CMD,phase='emote_setup' if only else 'setup',report='FirstPersonReview06.json' if fp else 'EmoteNativeReview06.json' if only else 'NativeReview.json',next=time.monotonic()+1.)
    S['handle']=u.register_slate_post_tick_callback(tick);save()
