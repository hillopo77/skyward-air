"""Held-object paired cartoon interaction for the existing local Unreal runtime.

No network replication is claimed. Register an actual friend actor explicitly;
the review launcher provides a local companion using the installed coat avatar.
"""
import unreal as u
import json,time,math,traceback
from pathlib import Path
from friend_action03_model import Action,Recovery,Config,center_distance,smooth,pressure_tremor,prop_visibility
R=Path(__file__).resolve().parents[4]/'Animations/FriendAction03'
S={'installed':False,'friends':{},'concealed':{},'events':[]}

def valid(o):return bool(o and u.SystemLibrary.is_valid(o))
def key(n):k=u.Key();k.import_text(n);return k
def emit(name,**kw):
    S['events'].append({'event':name,'time':time.monotonic(),**kw})
    (R/'RuntimeSession.json').write_text(json.dumps({'status':'READY','hotkey':S.get('key_name'),'local_only':True,'active':bool(S.get('active')),'concealed':S.get('concealed',{}),'events':S['events'][-100:]},indent=2))
def register_friend(friend_id,actor):
    if not valid(actor):raise ValueError('Invalid friend actor')
    S['friends'][friend_id]=actor;return friend_id
def now():return S.get('manual_time') if S.get('manual_time') is not None else time.monotonic()
def set_binding(name):
    S['key_name']=name or None;S['key']=key(name) if name else None
def closest_friend():
    G=S['game'];pawn=G.P.STATE['pawn'];p=pawn.get_actor_location();front=u.MathLibrary.get_forward_vector(G.P.STATE['pc'].get_control_rotation());candidates=[]
    for name,a in S['friends'].items():
        if not valid(a):continue
        d=a.get_actor_location()+u.Vector(0,0,90)-p;n=d.length()
        if n<1 or n>250:continue
        dot=sum(x*y for x,y in zip(d.to_tuple(),front.to_tuple()))/n
        if dot>.72:candidates.append((dot,-n,name))
    return max(candidates)[2] if candidates else None
def restore_pose(actor):
    if valid(actor):actor.skeletal_mesh_component.set_play_rate(1.);actor.skeletal_mesh_component.play_animation(S['idle'],True)
def play_at(actor,clip,t):
    c=actor.skeletal_mesh_component;c.set_animation_mode(u.AnimationMode.ANIMATION_SINGLE_NODE)
    c.play_animation(clip,False);c.set_play_rate(0.);c.set_position(max(0,float(t)),False)
def target_surface(actor):
    rear=u.MathLibrary.get_right_vector(actor.get_actor_rotation())*-1
    hips=actor.skeletal_mesh_component.get_socket_location(u.Name('Hips'))
    side=u.MathLibrary.get_forward_vector(actor.get_actor_rotation());cfg=S['config']['hand_pop']
    # An external chest-height gesture in the holder's hands. No body contact.
    point=hips+rear*cfg['back_cm']+side*cfg['side_cm']+u.Vector(0,0,cfg['height_cm'])
    return point,rear

def unobstructed(target,item):
    G=S['game'];p=G.P.STATE['pawn'];end=target.get_actor_location()+u.Vector(0,0,95)
    hit=u.SystemLibrary.line_trace_single(G.P.STATE['world'],p.get_actor_location(),end,u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[p,item,target],u.DrawDebugTrace.NONE,True)
    h=hit.to_tuple() if hit else []
    return not(h and h[0])

def hold_goal():
    G=S['game'];pc=G.P.STATE['pc'];rotation=pc.get_control_rotation()
    prop=S['config'].get('demo_prop',{})
    return G.P.STATE['pawn'].get_actor_location()+u.MathLibrary.get_forward_vector(rotation)*prop.get('hold_distance_cm',55)+u.MathLibrary.get_right_vector(rotation)*prop.get('hold_side_cm',18)+u.Vector(0,0,prop.get('hold_z_cm',-28))

def blend_rotation(a,b,weight):
    def angle(x,y):return x+((y-x+180)%360-180)*weight
    return u.Rotator(pitch=angle(a.pitch,b.pitch),yaw=angle(a.yaw,b.yaw),roll=angle(a.roll,b.roll))

def reserve_pair(item,target,fid,mode):
    G=S['game'];CP=S['pack'];pawn=G.P.STATE['pawn'];name=item.get_actor_label();component=item.static_mesh_component
    lo,hi=component.get_local_bounds();extent=(hi-lo)*.5;axis=max(range(3),key=lambda i:extent.to_tuple()[i]);scale=item.get_actor_scale3d();spec=G.S['actor_specs'].get(name,{})
    targets=[dict(q) for q in G.S['targets'] if q.get('actor')==name] if mode=='insert' else S.setdefault('stored_specs',{}).get(name,[])
    snap={'transform':item.get_actor_transform(),'rotation':item.get_actor_rotation(),'collision':item.get_actor_enable_collision(),'simulating':component.is_simulating_physics(),'hidden':mode=='extract','pickup_targets':targets,'view':G.P.STATE['pc'].get_control_rotation()}
    rear=u.MathLibrary.get_right_vector(target.get_actor_rotation())*-1;align_from=pawn.get_actor_location();align_goal=target.get_actor_location()+rear*S['config'].get('demo_prop',{}).get('alignment_cm',55)+u.Vector(0,0,align_from.z-target.get_actor_location().z)
    S['active']={'mode':mode,'target':target,'friend_id':fid,'item':item,'name':name,'snapshot':snap,'axis':axis,'axis_sign':spec.get('action_axis_sign',1),'grip_local':u.Vector(*spec['action_grip_local_cm']) if spec.get('action_grip_local_cm') else None,'local_center':(lo+hi)*.5,'half_length':extent.to_tuple()[axis]*abs(scale.to_tuple()[axis]),'scale':scale,'start_location':item.get_actor_location(),'align_from':align_from,'align_goal':align_goal,'committed':False}
    pose_ticks=[]
    for actor in [target,CP.S['avatar']]:
        comp=actor.skeletal_mesh_component;pose_ticks.append((comp,comp.get_editor_property('visibility_based_anim_tick_option')))
        comp.set_editor_property('visibility_based_anim_tick_option',u.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
    S['active']['pose_ticks']=pose_ticks
    S['active']['prior_hand_owner']=S['legacy'].S.get('paired_hand_owner')
    S['legacy'].S['paired_hand_owner']='friend_action03'
    if CP.S.get('emotes') and CP.S['emotes'].view.active:CP.S['emotes'].abort_camera()
    G.S['held']=None;component.set_simulate_physics(False);item.set_actor_enable_collision(False);G.P.STATE['pc'].set_ignore_move_input(True)
    movement=pawn.get_component_by_class(u.FloatingPawnMovement)
    if movement:movement.stop_movement_immediately()
    CP.S['emote']=None;CP.S['external_pose']=True
    emit('action_started' if mode=='insert' else 'recovery_started',item=name,target=fid,mode=mode)
def request(friend_id=None):
    G=S['game'];CP=S['pack'];pc=G.P.STATE['pc'];pawn=G.P.STATE['pawn']
    if S.get('active'):return False,'busy'
    if CP.S.get('wheel_open') or G.P.STATE.get('seated') or G.S.get('driving') or G.S.get('spectator'):return False,'player_unavailable'
    name=G.S.get('held');item=G.S['actors'].get(name) if name else None
    if not valid(item):G.say('Hold an object first');return False,'no_held_item'
    fid=friend_id or closest_friend();target=S['friends'].get(fid)
    if not valid(target):G.say('Aim at a nearby friend');return False,'no_friend'
    delta=pawn.get_actor_location()-target.get_actor_location();delta.z=0;dist=delta.length();rear=u.MathLibrary.get_right_vector(target.get_actor_rotation())*-1
    dot=sum(x*y for x,y in zip(delta.to_tuple(),rear.to_tuple()))/max(dist,.001)
    if not unobstructed(target,item):return False,'blocked'
    ok,why=S['action'].begin('local_player',fid,name,now(),held_item=name,distance_cm=dist,rear_dot=dot)
    if not ok:G.say('Stand close behind your friend' if why in ['too_far','approach_from_behind'] else why.replace('_',' '));return ok,why
    reserve_pair(item,target,fid,'insert');return True,'started'

def return_to_hand(a):
    G=S['game'];item=a['item'];item.set_actor_scale3d(a['scale']);item.set_actor_hidden_in_game(False);item.set_actor_enable_collision(True)
    component=item.static_mesh_component;component.set_simulate_physics(True);component.set_physics_linear_velocity(u.Vector(),False,u.Name('None'));G.S['held']=a['name']
    existing={q.get('actor') for q in G.S['targets']}
    if a['name'] not in existing:G.S['targets'].extend(a['snapshot']['pickup_targets'])
    S.setdefault('stored_specs',{}).pop(a['name'],None)
def finish():
    G=S['game'];a=S.pop('active',None)
    if not a:return
    if a['mode']=='extract' and a['committed'] and valid(a['item']):return_to_hand(a)
    for component,previous in a.get('pose_ticks',[]):
        if valid(component):component.set_editor_property('visibility_based_anim_tick_option',previous)
    if a.get('prior_hand_owner'):S['legacy'].S['paired_hand_owner']=a['prior_hand_owner']
    else:S['legacy'].S.pop('paired_hand_owner',None)
    restore_pose(a['target']);restore_pose(S['pack'].S.get('avatar'));S['pack'].S['last_clip']=None;S['pack'].S.pop('external_pose',None)
    G.P.STATE['pc'].set_ignore_move_input(False)
    S['legacy'].S.get('hand_current',{}).pop('R',None)
    emit('action_finished',item=a['name'],target=a['friend_id'],mode=a['mode'])
def cancel(reason='cancelled'):
    a=S.get('active');outcome=(S['recovery'] if a and a['mode']=='extract' else S['action']).cancel(reason)
    if not a:return
    if outcome and outcome['restore_held_item'] and valid(a['item']):
        item=a['item'];component=item.static_mesh_component;item.set_actor_hidden_in_game(a['snapshot']['hidden']);item.set_actor_transform(a['snapshot']['transform'],False,True);item.set_actor_enable_collision(a['snapshot']['collision']);component.set_simulate_physics(a['snapshot']['simulating']);S['game'].S['held']=a['name']
    if outcome and outcome.get('restore_stored_item') and valid(a['item']):
        a['item'].set_actor_hidden_in_game(True);a['item'].set_actor_scale3d(a['scale']);a['item'].set_actor_enable_collision(False);a['item'].static_mesh_component.set_simulate_physics(False)
    emit('action_cancelled',reason=reason,committed=a['committed']);finish()
def recover(friend_id):
    """Animate a stored item outward and back to the held position."""
    G=S['game'];items=S['concealed'].get(friend_id,[])
    if S.get('active') or G.S.get('held') or not items:return False
    if S['pack'].S.get('wheel_open') or G.P.STATE.get('seated') or G.S.get('driving') or G.S.get('spectator'):return False
    name=items[-1];actor=G.S['actors'].get(name);target=S['friends'].get(friend_id)
    if not valid(actor) or not valid(target) or not unobstructed(target,actor):return False
    delta=G.P.STATE['pawn'].get_actor_location()-target.get_actor_location();delta.z=0;distance=delta.length();rear=u.MathLibrary.get_right_vector(target.get_actor_rotation())*-1;dot=sum(x*y for x,y in zip(delta.to_tuple(),rear.to_tuple()))/max(distance,.001)
    ok,_=S['recovery'].begin('local_player',friend_id,name,now(),stored_item=name,distance_cm=distance,rear_dot=dot)
    if not ok:return False
    reserve_pair(actor,target,friend_id,'extract');return True
def update_action():
    a=S.get('active')
    if not a:return
    G=S['game'];CP=S['pack'];item=a['item'];target=a['target']
    if not valid(item) or not valid(target):cancel('actor_removed');return
    if (G.P.STATE['pawn'].get_actor_location()-target.get_actor_location()-u.Vector(0,0,162)).length()>300:cancel('separated');return
    extracting=a['mode']=='extract';pose,events=(S['recovery'] if extracting else S['action']).update(now())
    if not pose:return
    if not extracting and pose.phase=='motion' and pose.approach >= .38 and not a.get('reaction_shown'):
        a['reaction_shown']=True
        G.say('Friend: AHH! STOP! NOT THAT DEEP!')
        if S.get('reaction_voice'):
            u.GameplayStatics.play_sound_at_location(G.P.STATE['world'],S['reaction_voice'],target.get_actor_location()+u.Vector(0,0,150),u.Rotator(),1.4,1.0)
        emit('friend_reaction',line='AHH! STOP! NOT THAT DEEP!',target=a['friend_id'])
    visibility=prop_visibility(pose.elapsed,S['action'].cfg,extracting)
    pawn=G.P.STATE['pawn'];goal=a['align_from']+(a['align_goal']-a['align_from'])*smooth(pose.elapsed/S['action'].cfg.bend_seconds);pawn.set_actor_location(goal,True,False)
    camera_time=.6 if extracting else S['action'].cfg.bend_seconds
    if pose.elapsed<=camera_time or not a.get('view_aligned'):
        look=u.MathLibrary.find_look_at_rotation(pawn.get_actor_location(),target.get_actor_location()+u.Vector(0,0,90))
        G.P.STATE['pc'].set_control_rotation(blend_rotation(a['snapshot']['view'],look,smooth(pose.elapsed/camera_time)))
        a['view_aligned']=pose.elapsed>=camera_time
    if pose.elapsed>=S['action'].cfg.bend_seconds and (pawn.get_actor_location()-a['align_goal']).length()>15:cancel('alignment_blocked');return
    CP.S['avatar'].set_actor_rotation(target.get_actor_rotation(),False)
    play_at(target,S['extract_receiver_clip'] if extracting else S['receiver_clip'],pose.elapsed);play_at(CP.S['avatar'],S['extract_initiator_clip'] if extracting else S['initiator_clip'],pose.elapsed)
    if extracting or not a['committed']:
        point,rear=target_surface(target);distance=center_distance(a['half_length'],pose.approach,S['action'].cfg);center=point+rear*distance
        rot=[u.MathLibrary.make_rot_from_x,u.MathLibrary.make_rot_from_y,u.MathLibrary.make_rot_from_z][a['axis']](rear*a['axis_sign'])
        if not extracting and pose.phase=='bend':rot=blend_rotation(a['snapshot']['rotation'],rot,smooth(pose.elapsed/S['action'].cfg.bend_seconds))
        if extracting and pose.handoff:rot=blend_rotation(rot,u.Rotator(yaw=G.P.STATE['pc'].get_control_rotation().yaw+90),pose.handoff)
        off=a['local_center'];scale=a['scale']*max(.001,visibility);item.set_actor_scale3d(scale);shift=u.MathLibrary.get_forward_vector(rot)*(off.x*scale.x)+u.MathLibrary.get_right_vector(rot)*(off.y*scale.y)+u.MathLibrary.get_up_vector(rot)*(off.z*scale.z)
        position=center-shift
        if extracting and pose.handoff:
            center=center+(hold_goal()-center)*pose.handoff;position=center-shift
        if pose.phase=='bend':position=a['start_location']+(position-a['start_location'])*smooth(pose.elapsed/S['action'].cfg.bend_seconds)
        item.set_actor_rotation(rot,False);item.set_actor_location(position,False,True)
        def rotate_local(v):return u.MathLibrary.get_forward_vector(rot)*v.x+u.MathLibrary.get_right_vector(rot)*v.y+u.MathLibrary.get_up_vector(rot)*v.z
        grip_point=position+rotate_local(u.Vector(a['grip_local'].x*scale.x,a['grip_local'].y*scale.y,a['grip_local'].z*scale.z)) if a['grip_local'] is not None else center+rear*a['half_length']*.45*visibility
        if a['grip_local'] is not None and pose.phase!='bend' and not(extracting and pose.handoff):
            wrist=CP.S['avatar'].skeletal_mesh_component.get_socket_location(u.Name('RightHand'));palm=wrist+u.MathLibrary.get_right_vector(target.get_actor_rotation())*4+u.Vector(0,0,-2.5);correction=palm-grip_point;correction=correction*(min(4.,correction.length())/max(.001,correction.length()));position+=correction;grip_point+=correction;item.set_actor_location(position,False,True)
        tremor=pressure_tremor(pose.elapsed,getattr(pose,'effort',0.)*visibility) if not extracting and pose.phase=='motion' else pressure_tremor(0.,0.)
        if tremor.weight:
            # Translation comes from the newly authored wrist tremor through
            # the grip correction above. Rock the hammer around that same
            # grip, preserving contact instead of rotating about its centre.
            delta=grip_point-position
            def dot(v,w):return sum(x*y for x,y in zip(v.to_tuple(),w.to_tuple()))
            local_grip=u.Vector(dot(delta,u.MathLibrary.get_forward_vector(rot)),dot(delta,u.MathLibrary.get_right_vector(rot)),dot(delta,u.MathLibrary.get_up_vector(rot)))
            rot=u.Rotator(pitch=rot.pitch+tremor.pitch_degrees,yaw=rot.yaw,roll=rot.roll+tremor.roll_degrees)
            position=grip_point-(u.MathLibrary.get_forward_vector(rot)*local_grip.x+u.MathLibrary.get_right_vector(rot)*local_grip.y+u.MathLibrary.get_up_vector(rot)*local_grip.z)
            item.set_actor_rotation(rot,False);item.set_actor_location(position,False,True)
        # Keep the first-person grip with the actual prop instead of at idle.
        hand=S['legacy'].S.get('hands',{}).get('R')
        if valid(hand):
            grip=S['legacy'].S.get('hand_meshes',{}).get('SM_CH12_ViewHand_RGrip')
            if grip:hand.static_mesh_component.set_static_mesh(grip)
            hand.set_actor_location(grip_point,False,True)
            view=G.P.STATE['pc'].get_control_rotation()
            hand.set_actor_rotation(u.Rotator(pitch=view.pitch+tremor.pitch_degrees,yaw=view.yaw-90,roll=view.roll+tremor.roll_degrees),False)
    left=S['legacy'].S.get('hands',{}).get('L')
    def idle_hand(side):
        rotation=G.P.STATE['pc'].get_control_rotation()
        return pawn.get_actor_location()+u.MathLibrary.get_forward_vector(rotation)*48+u.MathLibrary.get_right_vector(rotation)*(-28 if side=='L' else 28)+u.MathLibrary.get_up_vector(rotation)*-31
    if not extracting and a['committed']:
        right=S['legacy'].S.get('hands',{}).get('R')
        if valid(right):
            mesh=S['legacy'].S.get('hand_meshes',{}).get('SM_CH12_ViewHand_R')
            if mesh:right.static_mesh_component.set_static_mesh(mesh)
            wrist=CP.S['avatar'].skeletal_mesh_component.get_socket_location(u.Name('RightHand'))
            palm=wrist+u.MathLibrary.get_right_vector(target.get_actor_rotation())*4+u.Vector(0,0,-2.5)
            weight=smooth(pose.bend_degrees/max(.001,S['action'].cfg.bend_degrees))
            home=idle_hand('R');right.set_actor_location(home+(palm-home)*weight,False,True)
            view=G.P.STATE['pc'].get_control_rotation();right.set_actor_rotation(u.Rotator(pitch=view.pitch,yaw=view.yaw-90,roll=view.roll),False)
    if valid(left):
        wrist=CP.S['avatar'].skeletal_mesh_component.get_socket_location(u.Name('LeftHand'))
        palm=wrist+u.MathLibrary.get_right_vector(target.get_actor_rotation())*4+u.Vector(0,0,-2.5)
        weight=smooth(pose.bend_degrees/max(.001,S['action'].cfg.bend_degrees))
        # Keep the support hand on its own side instead of crossing the grip.
        home=idle_hand('L');left.set_actor_location(home,False,True)
    for event in events:
        if event['event']=='reveal':item.set_actor_hidden_in_game(False)
        elif event['event']=='recovered':
            a['committed']=True;S['concealed'][a['friend_id']].remove(a['name'])
            u.GameplayStatics.play_sound_at_location(G.P.STATE['world'],S['pop'],item.get_actor_location(),u.Rotator(),.55,.85)
            emit('item_recovered',item=a['name'],target=a['friend_id']);G.say('Got it')
        elif event['event']=='pop':
            a['committed']=True;item.set_actor_hidden_in_game(True);item.set_actor_scale3d(a['scale']);item.set_actor_enable_collision(False);S['concealed'].setdefault(a['friend_id'],[]).append(a['name'])
            S.setdefault('stored_specs',{})[a['name']]=a['snapshot']['pickup_targets'];G.S['targets'][:]=[q for q in G.S['targets'] if q.get('actor')!=a['name']]
            u.GameplayStatics.play_sound_at_location(G.P.STATE['world'],S['pop'],target.get_actor_location()+u.Vector(0,0,80),u.Rotator(),float(S['config'].get('sound_volume',.7))*1.8,1.12)
            emit('pop',item=a['name'],target=a['friend_id']);G.say('Friend: TOO DEEP!')
        elif event['event']=='finished':finish()
def new_static(name,mesh,position):
    lib=u.get_default_object(u.GameplayStatics);tr=u.Transform();actor=lib.call_method('BeginDeferredActorSpawnFromClass',(S['world'],u.StaticMeshActor,tr,u.SpawnActorCollisionHandlingMethod.ALWAYS_SPAWN,None,u.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT));actor=lib.call_method('FinishSpawningActor',(actor,tr,u.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT))
    actor.set_actor_label(name);actor.static_mesh_component.set_mobility(u.ComponentMobility.MOVABLE);actor.static_mesh_component.set_static_mesh(mesh);actor.set_actor_location(position,False,True);return actor
def setup_demo():
    G=S['game'];CP=S['pack'];friend=CP.new_actor('Friend03 Companion',S['coat_mesh']);friend.set_actor_location(G.v([-47.,-13.,0]),False,True);friend.set_actor_rotation(u.Rotator(),False);restore_pose(friend);register_friend('review_friend',friend)
    actor=new_static('Friend03 Claw Hammer',S['hammer_mesh'],G.v([-47.,-12.,.8]));c=actor.static_mesh_component;c.set_collision_profile_name('PhysicsActor');c.set_mass_override_in_kg(u.Name('None'),.85,True);c.set_simulate_physics(False)
    prop=S['config'].get('demo_prop',{});name=actor.get_actor_label();G.S['actors'][name]=actor;G.S['physics'][name]=actor;G.S['actor_specs'][name]={'name':name,'asset':'SM_FriendDemoHammer03','hold_distance_cm':prop.get('hold_distance_cm',55),'hold_side_cm':prop.get('hold_side_cm',18),'hold_z_cm':prop.get('hold_z_cm',-28),'action_axis_sign':-1,'action_grip_local_cm':prop.get('grip_local_cm',[0,0,-12.6470588])};G.S['targets'].append({'kind':'pickup','actor':name,'point':[-47.,-12.,.8],'title':'Pick up claw hammer'})
    G.P.STATE['pawn'].set_actor_location(G.v([-47.,-12.1,1.62]),False,True);G.P.STATE['pc'].set_control_rotation(u.MathLibrary.find_look_at_rotation(G.P.STATE['pawn'].get_actor_location(),friend.get_actor_location()+u.Vector(0,0,95)));S['demo_item']=name;S['demo_friend']=friend
    if '-FriendAction03Review' not in G.CMD:G.act({'kind':'pickup','actor':name,'point':[-47.,-12.,.8]})
    G.say('Review: E pick up / F8 paired action / Esc cancel. Final hotkey remains unassigned.')
def install(G,CP):
    import characters12_runtime as legacy
    config=json.loads((R/'config.json').read_text());cfg=Config(**{k:v for k,v in config.items() if k in Config.__dataclass_fields__})
    S.update(installed=True,game=G,pack=CP,legacy=legacy,world=G.P.STATE['world'],config=config,action=Action(cfg),recovery=Recovery(cfg),escape=key('Escape'))
    S['coat_mesh']=u.load_asset('/Game/CharacterPack_Oct30/Meshes/SK_Coat_Character');S['idle']=CP.S['profiles'][3]['animations']['StandingIdle']['obj'];S['receiver_clip']=u.load_asset('/Game/HandPop11/Animations/AN_Friend03_Receiver');S['initiator_clip']=u.load_asset('/Game/HandPop11/Animations/AN_Friend03_Initiator');S['hammer_mesh']=u.load_asset('/Game/FriendAction03/Meshes/SM_FriendDemoHammer03');S['pop']=u.load_asset('/Game/FriendAction03/Audio/Pop03')
    assert all(S[n] for n in ['coat_mesh','idle','receiver_clip','initiator_clip','hammer_mesh','pop']),'Import FriendAction03 assets first'
    S['reaction_voice']=u.load_asset('/Game/FriendAction03/Audio/FriendReactionUrgentFast')
    S['extract_receiver_clip']=u.load_asset('/Game/HandPop11/Animations/AN_Friend03_ExtractReceiver');S['extract_initiator_clip']=u.load_asset('/Game/HandPop11/Animations/AN_Friend03_ExtractHelper');assert S['extract_receiver_clip'] and S['extract_initiator_clip'],'Import extraction clips first'
    CP.select_profile(3)
    S['old_open']=CP.open_wheel;S['old_select']=CP.select_profile;S['old_use']=G.use_nearest
    S['old_hand_colour']=legacy.update_hand_colour
    def open_wheel():
        if not S.get('active'):return S['old_open']()
    def select_profile(i):
        if not S.get('active'):return S['old_select'](i)
    def use(*args,**kw):
        if S.get('active'):return True
        return S['old_use'](*args,**kw)
    CP.open_wheel=open_wheel;CP.select_profile=select_profile;G.use_nearest=use;G.P.use_nearest=use
    S['wrappers']=(open_wheel,select_profile,use)
    # Native hand geometry is retained; give it human skin for the civilian avatar.
    skin=u.load_asset('/Game/Characters39/Materials/CH39_Peach')
    def hand_colour():
        if skin and CP.S.get('profile')==3:
            for hand in legacy.S.get('hands',{}).values():
                if valid(hand):hand.static_mesh_component.set_material(0,skin)
        else:S['old_hand_colour']()
    legacy.update_hand_colour=hand_colour;S['hand_wrapper']=hand_colour;hand_colour()
    override=next((w.split('=',1)[1] for w in G.CMD.split() if w.startswith('-FriendAction03Key=')),None);set_binding(override or config.get('hotkey'))
    if '-FriendAction03Demo' in G.CMD:setup_demo()
    if '-FriendAction03Review' in G.CMD:
        import friend_action03_review;friend_action03_review.start(__import__(__name__))
    emit('installed',profile='Coat_Character',hotkey=S['key_name'],networked=False,revision='handpop11')
def tick(dt):
    try:
        if not S['installed']:
            import airport_runtime as G,character_pack_runtime as CP
            if not G.S.get('ready') or not CP.S.get('installed'):return
            if not json.loads((R/'config.json').read_text()).get('enabled',True):return
            install(G,CP)
        pc=S['game'].P.STATE['pc']
        if S.get('active') and pc.was_input_key_just_pressed(S['escape']):cancel('escape')
        if S.get('key') and pc.was_input_key_just_pressed(S['key']):
            fid=closest_friend()
            if not S.get('active') and not S['game'].S.get('held') and fid and S['concealed'].get(fid):recover(fid)
            else:request(fid)
        update_action()
        G=S['game']
        if S.get('active'):
            action=S['recovery'] if S['active']['mode']=='extract' else S['action'];state=action.state;elapsed=now()-state['started'] if state else S['action'].cfg.duration
            count=min(5,max(0,int((elapsed-S['action'].cfg.bend_seconds)/S['action'].cfg.cycle_seconds)+1))
            text='Bringing item back  |  Esc cancel' if S['active']['mode']=='extract' else 'Vanish held item  |  Esc cancel'
        elif closest_friend() and (G.S.get('held') or S['concealed'].get(closest_friend())):
            title='Vanish held item' if G.S.get('held') else 'Bring item back'
            text=(S['key_name']+' / '+title) if S.get('key_name') else title+' / key unassigned'
        else:text=''
        if text:u.SystemLibrary.print_string(S['world'],text,True,False,u.LinearColor(.95,.86,.64,1),.12,u.Name('FriendAction03Hint'))
    except Exception:
        error=traceback.format_exc();(R/'RuntimeError.txt').write_text(error);u.log_error(error)
        if S.get('active'):
            try:cancel('runtime_error')
            except Exception:pass
        review=bool(S.get('game') and '-FriendAction03Review' in S['game'].CMD)
        if review:
            (R/'NativeReview.json').write_text(json.dumps({'status':'FAILED','error':error,'phase':'runtime_start_or_tick'},indent=2))
            u.SystemLibrary.quit_game(S['world'],S['game'].P.STATE['pc'],u.QuitPreference.QUIT,False)
        stop()
def stop():
    if S.get('active'):cancel('shutdown')
    if S.get('handle'):u.unregister_slate_post_tick_callback(S['handle']);S['handle']=None
    if S.get('installed'):
        CP=S.get('pack');G=S.get('game')
        if CP and S.get('wrappers'):
            if CP.open_wheel is S['wrappers'][0]:CP.open_wheel=S['old_open']
            if CP.select_profile is S['wrappers'][1]:CP.select_profile=S['old_select']
            if G and G.use_nearest is S['wrappers'][2]:G.use_nearest=S['old_use'];G.P.use_nearest=S['old_use']
            if S.get('legacy') and S.get('hand_wrapper') and S['legacy'].update_hand_colour is S['hand_wrapper']:S['legacy'].update_hand_colour=S['old_hand_colour']
    S['installed']=False
def start():
    if S.get('handle'):return
    S['handle']=u.register_slate_post_tick_callback(tick)
