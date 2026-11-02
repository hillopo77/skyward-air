"""Airport journey, bounded native prop physics, conveyor forces and tug controls.
Extends the preserved aircraft walkthrough in memory only; no aircraft source edits.
"""
import unreal as u,json,math,time,traceback,hashlib,copy
from pathlib import Path
CMD=u.SystemLibrary.get_command_line();AP_BASE='/Game/Airport12' if '-AirportCompact12' in CMD else '/Game/Airport10'
R=Path(__file__).resolve().parents[4]/'Airport';R=R/'Airport38' if '-AirportRepair38' in CMD else R/'Clarity37' if '-AirportClarity37' in CMD else R/'Detail36' if '-AirportDetail36' in CMD else R/'Flow35' if '-AirportFlow35' in CMD else R/'Terminal34' if '-AirportTerminal34' in CMD else R/'Warm33' if '-AirportWarm33' in CMD else R/'Lighting32' if '-AirportLighting32' in CMD else R/'Arrival31' if '-AirportArrival31' in CMD else R/'Checkin30' if '-AirportCheckin30' in CMD else R/'Checkin29' if '-AirportCheckin29' in CMD else R/'Checkin28' if '-AirportCheckin28' in CMD else R/'Prototype27' if '-AirportPrototype27' in CMD else R/'Clarity26' if '-AirportClarity26' in CMD else R/'Foyer25' if '-AirportFoyer25' in CMD else R/'Rooms24' if '-AirportRooms24' in CMD else R/'Compact12' if '-AirportCompact12' in CMD else R;D=json.loads((R/'Exports/airport_layout.json').read_text(encoding='utf-8'));S=dict(ready=False,busy=False,checked_in=False,bag_accepted=False,security=False,boarding=False,aboard=False,held=None,driving=None,spectator=False,events=[],frames=[],doors={},physics={},actor_specs={q['name']:q for q in D['instances']},ticks=0)
CMD=u.SystemLibrary.get_command_line();STAGE=int(next((q.split('=')[1] for q in CMD.split() if q.startswith('-AirportPass=')),'10'));CAPTURE='-AirportCapture' in CMD;QA='-AirportQA' in CMD;P=None
MODULE_SHA=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
NONE=u.Name('None');IGNORE=next(getattr(u.CollisionResponseType,n) for n in dir(u.CollisionResponseType) if n.lower().endswith('ignore'));BLOCK=next(getattr(u.CollisionResponseType,n) for n in dir(u.CollisionResponseType) if n.lower().endswith('block'))
def key(n):k=u.Key();k.import_text(n);return k
KEY={n:key(n) for n in ('Tab','E','SpaceBar','LeftControl','LeftShift','LeftMouseButton','W','A','S','D','R')}
def v(p):return u.Vector(p[0]*100,-p[1]*100,p[2]*100)
def source(p):return (p.x/100,-p.y/100,p.z/100)
def valid(a):return bool(a and u.SystemLibrary.is_valid(a))
def event(n,**kw):S['events'].append(dict(event=n,time_s=time.monotonic()-S['started'],**kw));write()
def write():
 f=sorted(S['frames'][-2400:]);n=len(f);stats=dict(frames=len(S['frames']),average_fps=n/sum(f) if n and sum(f)>0 else None,p95_ms=f[int((n-1)*.95)]*1000 if n else None,maximum_ms=max(f)*1000 if n else None)
 d=dict(status='READY' if S['ready'] else 'STARTING',pass_id=STAGE,revision=D.get('revision',10),runtime_sha256=MODULE_SHA,journey={q:S[q] for q in ('checked_in','bag_accepted','security','boarding','aboard')},held=S['held'],driving=S['driving'],spectator=S['spectator'],native_physics_bodies=len(S['physics']),events=S['events'],frame_statistics=stats)
 if S['ready']:d['player_source']=source(P.STATE['pawn'].get_actor_location())
 (R/'ArtBible'/('AirportCaptureSession%02d.json'%STAGE if CAPTURE else 'AirportSession.json')).write_text(json.dumps(d,indent=2))
def say(s):
 S['message']=s;S['message_until']=time.monotonic()+3
def cue(n,point):
 sound=u.load_asset(AP_BASE+'/Audio/'+n)
 if sound:u.GameplayStatics.play_sound_at_location(P.STATE['world'],sound,v(point),u.Rotator())
def screen(actor,keyname):
 if not valid(actor):return
 c=actor.static_mesh_component;m=u.load_asset(AP_BASE+'/Materials/Instances/MI_AP_UI_'+keyname)
 if m:
  for j,slot in enumerate(c.static_mesh.static_materials):
   if str(slot.material_slot_name)=='MI_AP_Screen':c.set_material(j,m)
def point(q):
 a=S['actors'].get(q['actor'])
 if q['kind']=='npc' and valid(a):return a.get_actor_location()+u.MathLibrary.get_right_vector(a.get_actor_rotation())*25+u.Vector(0,0,130)
 if q['kind'] in ('pickup','extinguisher') and valid(a):return a.static_mesh_component.get_center_of_mass()
 if q['kind'] in ('slide','boardingdoor') and q['actor'] in S['doors'] and not q.get('fixed_release'):return S['doors'][q['actor']]['actor'].get_actor_location()+v((0,-.10,1.2))
 return v(q['point'])
def visible(q):
 p=P.STATE['pawn'];start=p.get_actor_location();end=point(q);h=u.SystemLibrary.line_trace_single(P.STATE['world'],start,end,u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[p]+([S['actors'][S['held']]] if S['held'] else []),u.DrawDebugTrace.NONE,True)
 if h is None:return True
 h=h.to_tuple()
 if not h[0]:return True
 a=h[9]
 if not a:return True
 if a==S['actors'].get(q['actor']) or q.get('release_actor') and a==S['actors'].get(q['release_actor']):return True
 if q['kind']=='seat' and a==S['actors'].get(q.get('mesh_actor')):return True
 if q['kind']=='seat' and len(h)>10 and h[10] and isinstance(h[10],u.InstancedStaticMeshComponent):return h[10].static_mesh and h[10].static_mesh.get_name()==q['asset']
 if q['kind']=='scanner' and a.get_actor_label().startswith('X-ray scanner'):return True
 return (h[5]-end).length()<12
def nearest():
 if not S['ready'] or S['spectator'] or S['driving']:return None
 pos=P.STATE['pawn'].get_actor_location();f=u.MathLibrary.get_forward_vector(P.STATE['pc'].get_control_rotation());choices=[]
 for q in S['targets']:
  if '-AirportJourney22' in CMD and q.get('actor')==S.get('held'):continue
  pt=point(q);d=pt-pos;n=d.length()
  if n>340 or n<1:continue
  dot=sum(a*b for a,b in zip(d.to_tuple(),f.to_tuple()))/n
  if dot<.92:continue
  lateral=n*math.sqrt(max(0,1-dot*dot))
  if lateral>60 or not visible(q):continue
  choices.append((math.acos(min(1,dot))*180/math.pi,n,q))
 return min(choices,key=lambda q:(q[0],q[1]))[2] if choices else None
def open_door(name,value=1):
 if name in S['doors']:S['doors'][name]['target']=value
def release(throw=False):
 n=S['held']
 if not n:return
 a=S['actors'][n];c=a.static_mesh_component
 if throw:f=u.MathLibrary.get_forward_vector(P.STATE['pc'].get_control_rotation());c.add_impulse(f*c.get_mass()*900,NONE,False)
 c.set_collision_response_to_channel(u.CollisionChannel.ECC_PAWN,BLOCK);S['held']=None;event('Prop thrown' if throw else 'Prop dropped',actor=n)
def act(q):
 kind=q['kind'];a=S['actors'].get(q['actor']);p=q['point']
 if kind=='checkin':
  S['checked_in']=True;screen(a,'CheckedIn');cue('Ticket',p);say('Boarding pass issued Â· SA107 Â· Gate A07');event('Checked in',desk=q['actor'])
 elif kind=='bagdrop':
  if not S['checked_in']:say('Check in first, then place your suitcase on the belt');return
  S['bag_drop_armed']=True;cue('ScannerReady',p);say('Place your suitcase on the moving bag-drop belt');event('Bag drop running',belt=q['actor'])
 elif kind in ('scanner','security'):
  if not S['checked_in']:say('Collect a boarding pass at check-in');cue('Denied',p);return
  S['screening_armed']=True;screen(a,'Scanned');cue('ScannerReady',p);say('Baggage screening active Â· walk through a security portal');event('Screening requested',lane=q.get('lane'))
 elif kind in ('boarding','boardingdoor'):
  if q.get('gate','A07')!='A07':say('SA107 boards at Gate A07');return
  if not S['checked_in'] or not S['security']:say('Complete check-in and walk through security first');cue('Denied',p);return
  S['boarding']=True
  for n in S['doors']:
   if n.startswith('A07 boarding'):open_door(n)
  screen(a,'Boarding');cue('GateOpen',p);say('Boarding open Â· follow the jetbridge to the aircraft');event('Gate A07 boarding opened')
 elif kind=='slide':
  value=1-S['doors'][q['actor']]['target'];open_door(q['actor'],value)
  if q.get('fixed_release'):
   occupied=not value and q.get('inside_release',False);material=u.load_asset(AP_BASE+'/Materials/Instances/MI_AP_'+('RedLED' if occupied else 'GreenLED'))
   for control in S['targets']:
    if control['actor']==q['actor'] and control.get('release_actor'):
     c=S['actors'][control['release_actor']].static_mesh_component
     for j,slot in enumerate(c.static_mesh.static_materials):
      if str(slot.material_slot_name)=='MI_AP_GreenLED':c.set_material(j,material)
  event('Sliding door operated',door=q['actor'])
 elif kind in ('pickup','extinguisher'):
  if not valid(a):return
  c=a.static_mesh_component;c.set_simulate_physics(True);c.set_collision_response_to_channel(u.CollisionChannel.ECC_PAWN,IGNORE);c.wake_all_rigid_bodies();S['held']=q['actor'];event('Prop picked up',actor=q['actor'])
 elif kind=='npc':
  import characters12_runtime;characters12_runtime.greet(q)
 elif kind=='seat':
  P.sit(dict(q,kind='seat',title='Airport waiting seat',location=q['eye'],facing=q['facing']));event('Airport seat occupied')
 elif kind=='information':say('SA107 Â· Azure Bay Â· Gate A07 Â· Boarding 10:40');event('Information display consulted')
 elif kind=='vending':cue('GateOpen',p);say('Refreshments ready Â· coffee is available at Cloud Nine');event('Refreshment selected')
 elif kind=='drive':drive(q)
def use_nearest(stand_on_miss=True):
 if S['driving']:exit_drive();return
 if S['spectator']:return
 if S['held']:
  if D.get('revision',10)>=11:
   import airport_ext11_runtime as ext
   if ext.is_ext(S['held']) and P.STATE['pc'].was_input_key_just_pressed(KEY['LeftMouseButton']):return True
  release(P.STATE['pc'].was_input_key_just_pressed(KEY['LeftMouseButton']));return
 q=nearest()
 if q:act(q);return True
 return S['original_use'](stand_on_miss)
def drive(q):
 a=S['actors'][q['actor']];p=P.STATE['pawn'];m=p.get_component_by_class(u.FloatingPawnMovement);m.stop_movement_immediately();m.deactivate();p.set_actor_enable_collision(False);P.STATE['pc'].set_ignore_move_input(True)
 cam=(S['cameras'].get('09_Apron') or S['cameras']['09_Airside']);S['drive_camera_restore']=(cam.get_actor_transform(),cam.get_attach_parent_actor());cam.attach_to_actor(a,NONE,u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,False);cam.set_actor_relative_location(v(q.get('seat',[0,-.15,1.35])),False,True);cam.set_actor_relative_rotation(u.Rotator(yaw=90),False,True);P.STATE['pc'].set_view_target_with_blend(cam,.15);S.update(driving=q['actor'],drive_look=[0,0]);event('Baggage tug entered')
def exit_drive():
 a=S['actors'][S['driving']];p=P.STATE['pawn'];pos=a.get_actor_location()+u.MathLibrary.get_forward_vector(a.get_actor_rotation())*175+u.Vector(0,0,162);p.set_actor_location(pos,False,True);p.set_actor_enable_collision(True);p.get_component_by_class(u.FloatingPawnMovement).activate(True);P.STATE['pc'].reset_ignore_move_input();cam=(S['cameras'].get('09_Apron') or S['cameras']['09_Airside']);cam.detach_from_actor(u.DetachmentRule.KEEP_WORLD,u.DetachmentRule.KEEP_WORLD,u.DetachmentRule.KEEP_WORLD);cam.set_actor_transform(S['drive_camera_restore'][0],False,True);P.STATE['pc'].set_view_target_with_blend(p,.15);S['driving']=None;event('Baggage tug exited')
def toggle_spectator():
 if S['driving']:return
 if P.STATE['seated']:P.stand()
 S['spectator']=not S['spectator'];m=P.STATE['pawn'].get_component_by_class(u.FloatingPawnMovement);m.set_plane_constraint_enabled(not S['spectator']);P.STATE['pawn'].set_actor_enable_collision(not S['spectator']);say('Spectator Â· WASD + mouse Â· Space/Ctrl vertical Â· Shift boost' if S['spectator'] else 'Walking mode');event('Spectator toggled',enabled=S['spectator'])
def initialize():
 S.update(started=time.monotonic(),actors={a.get_actor_label():a for a in u.GameplayStatics.get_all_actors_of_class(P.STATE['world'],u.StaticMeshActor)},cameras={a.get_actor_label().removeprefix('AP CAM '):a for a in u.GameplayStatics.get_all_actors_of_class(P.STATE['world'],u.CameraActor) if a.get_actor_label().startswith('AP CAM ')},targets=[q for q in D['interactions'] if S['actor_specs'][q['actor']]['stage']<=STAGE],last_frame=time.perf_counter())
 for q in D['instances']:
  if q['stage']>STAGE:continue
  n=q['name'];a=S['actors'].get(n)
  if q.get('physics') and valid(a):
   c=a.static_mesh_component;c.set_collision_profile_name('PhysicsActor');c.set_enable_gravity(True);c.set_simulate_physics(True);c.set_physics_linear_velocity(u.Vector(),False,NONE);c.set_physics_angular_velocity_in_radians(u.Vector(),False,NONE);c.set_mass_override_in_kg(NONE,q['mass'],True);c.set_linear_damping(.18);c.set_angular_damping(.6);c.set_use_ccd(True);S['physics'][n]=a
   if q.get('rack_stowed25'):c.set_simulate_physics(False)
   if q['asset'] in ('SM_AP_Tug','SM_AP_Dolly','SM_AP_Tug34','SM_AP_Dolly34'):c.set_phys_material_override(u.load_asset(AP_BASE+'/Physics/PM_AP_GroundVehicle'))
  if q['asset'] in ('SM_AP_Bench3','SM_AP_CafeChair','SM_AP_Bench34','SM_AP_CafeChair34','SM_AP_Sofa36'):
   r=math.radians(q['rotation_degrees'])
   for j,x in enumerate((-.52,.52) if q['asset']=='SM_AP_Sofa36' else (-.74,0,.74) if q['asset'] in ('SM_AP_Bench3','SM_AP_Bench34') else (0,)):
    eye=[q['location'][0]+x*math.cos(r)+.10*math.sin(r),q['location'][1]+x*math.sin(r)-.10*math.cos(r),q['location'][2]+1.2];pt=[eye[0],eye[1],eye[2]-.25];S['targets'].append(dict(kind='seat',actor=q['name']+' seat '+str(j),asset=q['asset'],mesh_actor=q['name'],point=pt,eye=eye,facing=[math.sin(r),-math.cos(r),0],title='Sit'))
 for q in S['targets']:
  if q['kind'] in ('slide','boardingdoor'):
   a=S['actors'][q['actor']];S['doors'][q['actor']]=dict(actor=a,closed=a.get_actor_location(),delta=v(q['delta']),fraction=0,target=0,automatic=q.get('automatic',False))
 # Existing fully modeled door and hinges open together; the cabin remains editable.
 if STAGE>=7 and D['aircraft_door'] in P.STATE['movables']:
  q=P.STATE['movables'][D['aircraft_door']];q['target']=q['progress']=1.;P._apply_movable(q)
 P.STATE['pc'].player_camera_manager.set_editor_property('default_fov',88);u.SystemLibrary.execute_console_command(P.STATE['world'],'r.ScreenPercentage 100',P.STATE['pc']);u.SystemLibrary.execute_console_command(P.STATE['world'],'t.MaxFPS 60',P.STATE['pc']);S['ready']=True
 if D.get('revision',10)>=11:
  import airport_ext11_runtime;airport_ext11_runtime.initialize(__import__(__name__))
 if D.get('revision',10)>=12:
  import characters12_runtime;characters12_runtime.initialize(__import__(__name__))
 if '-AirportStartAboard' in CMD:
  P.STATE['pawn'].set_actor_location(v((-.8,.675,1.62)),False,True);P.STATE['pc'].set_control_rotation(u.Rotator(yaw=90));S.update(checked_in=True,security=True,boarding=True,aboard=True)
 if '-AirportJourney22' in CMD and '-AirportRepair38' not in CMD:
  import airport_journey22;airport_journey22.initialize(__import__(__name__))
 if '-AirportVisual23' in CMD:
  import airport_visual23;airport_visual23.initialize(__import__(__name__))
 if '-AirportRooms24' in CMD:
  import airport_rooms24;airport_rooms24.initialize(__import__(__name__))
 if '-AirportClarity26' in CMD:
  import airport_clarity26;airport_clarity26.initialize(__import__(__name__))
 if '-AirportPrototype27' in CMD:
  import airport_prototype27;airport_prototype27.initialize(__import__(__name__))
 if '-AirportCheckin28' in CMD:
  import airport_checkin28;airport_checkin28.initialize(__import__(__name__))
 if '-AirportCheckin29' in CMD:
  import airport_checkin29;airport_checkin29.initialize(__import__(__name__))
 if '-AirportCheckin30' in CMD:
  import airport_checkin30;airport_checkin30.initialize(__import__(__name__))
 if '-AirportArrival31' in CMD:
  import airport_arrival31;airport_arrival31.initialize(__import__(__name__))
 if '-AirportLighting32' in CMD:
  import airport_lighting32;airport_lighting32.initialize(__import__(__name__))
 if '-AirportWarm33' in CMD:
  import airport_warm33;airport_warm33.initialize(__import__(__name__))
 if '-AirportTerminal34' in CMD:
  import airport_terminal34;airport_terminal34.initialize(__import__(__name__))
 if '-AirportFlow35' in CMD:
  import airport_flow35;airport_flow35.initialize(__import__(__name__))
 if '-AirportDetail36' in CMD:
  import airport_detail36;airport_detail36.initialize(__import__(__name__))
 if '-AirportClarity37' in CMD:
  import airport_clarity37;airport_clarity37.initialize(__import__(__name__))
 if '-AirportRepair38' in CMD:
  import airport_repair38;airport_repair38.initialize(__import__(__name__))
 if '-AirportFoyer25QA' in CMD:
  import airport_foyer25_qa;airport_foyer25_qa.start(__import__(__name__))
 write()
 if CAPTURE and '-AirportRepair38' not in CMD:
  import airport_capture;airport_capture.start(__import__(__name__))
 if QA and '-AirportRepair38' not in CMD:
  import importlib;importlib.import_module('airport_rooms24_qa' if '-AirportRooms24' in CMD else 'airport_journey22_qa' if '-AirportJourney22' in CMD else 'characters13_qa' if '-Characters13' in CMD else 'compact12_qa' if D.get('revision',10)>=12 else 'airport_qa').start(__import__(__name__))
def floor_update(dt):
 if S.get('driving') or S.get('spectator'):return
 return S['original_floor'](dt)
def bind_tow():
 joints={a.get_actor_label():a for a in u.GameplayStatics.get_all_actors_of_class(P.STATE['world'],u.PhysicsConstraintActor)};S['tow_joints']=[]
 for i,spec in enumerate(sorted([q for q in D['instances'] if q.get('tow_to')],key=lambda q:q['name'])):
  n=spec['name'];a=S['actors'][n];b=S['actors'][S['actor_specs'][n]['tow_to']];actor=joints['AP Tow joint '+str(i)];actor.set_actor_location(a.get_actor_location()+v((0,-2.24,.42)),False,True);c=actor.get_component_by_class(u.PhysicsConstraintComponent);c.set_linear_x_limit(u.LinearConstraintMotion.LCM_LOCKED,0);c.set_linear_y_limit(u.LinearConstraintMotion.LCM_LOCKED,0);c.set_linear_z_limit(u.LinearConstraintMotion.LCM_LOCKED,0);c.set_angular_swing1_limit(u.AngularConstraintMotion.ACM_LIMITED,65);c.set_angular_swing2_limit(u.AngularConstraintMotion.ACM_LIMITED,12);c.set_angular_twist_limit(u.AngularConstraintMotion.ACM_LIMITED,12);c.set_disable_collision(True);c.set_projection_enabled(False);c.set_constrained_components(a.static_mesh_component,NONE,b.static_mesh_component,NONE);S['tow_joints'].append(c)
 event('Native tow couplings bound',count=2)
def supported_on_belt(c,belt):
 com=c.get_center_of_mass();hit=u.SystemLibrary.line_trace_single(P.STATE['world'],com,com-u.Vector(0,0,170),u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[c.get_owner(),P.STATE['pawn']],u.DrawDebugTrace.NONE,True)
 if not hit:return False
 h=hit.to_tuple();component=h[10] if len(h)>10 else None
 return bool(h[0] and component and isinstance(component,(u.StaticMeshComponent,u.InstancedStaticMeshComponent)) and component.static_mesh and component.static_mesh.get_name() in ('SM_AP_Carousel','SM_AP_Belt') and h[2]<100)
def physics(dt):
 if S['ticks']==4:bind_tow()
 pc=P.STATE['pc'];pawn=P.STATE['pawn'];now=time.monotonic()
 if S['held']:
  c=S['actors'][S['held']].static_mesh_component;spec=S['actor_specs'].get(S['held'],{});f=u.MathLibrary.get_forward_vector(pc.get_control_rotation());right=u.MathLibrary.get_right_vector(pc.get_control_rotation());goal=pawn.get_actor_location()+f*spec.get('hold_distance_cm',125)+right*spec.get('hold_side_cm',0)+u.Vector(0,0,spec.get('hold_z_cm',-14))+(right*42+u.Vector(0,0,-10) if spec.get('asset')=='SM_AP_Extinguisher11' else u.Vector());goal=S.get('deposit_goal',goal);acc=(goal-c.get_center_of_mass())*22-(c.get_physics_linear_velocity()-S.get('carrier_velocity39',u.Vector()))*9+u.Vector(0,0,980);n=acc.length();acc=acc*(min(n,3000)/max(n,1));c.add_force(acc*c.get_mass(),NONE,False);c.add_torque_in_radians(c.get_physics_angular_velocity_in_radians()*-4,NONE,True)
 if S['driving']:
  a=S['actors'][S['driving']];c=a.static_mesh_component;f=u.MathLibrary.get_right_vector(a.get_actor_rotation());throttle=float(pc.is_input_key_down(KEY['W']))-float(pc.is_input_key_down(KEY['S']));steer=float(pc.is_input_key_down(KEY['A']))-float(pc.is_input_key_down(KEY['D']));
  if QA and 'qa_drive' in S:throttle,steer=S['qa_drive']
  vel=c.get_physics_linear_velocity();desired=f*throttle*550;acc=(desired-u.Vector(vel.x,vel.y,0))*1.5;c.add_force(acc*c.get_mass(),NONE,False);omega=c.get_physics_angular_velocity_in_radians();c.add_torque_in_radians(u.Vector(-omega.x*3,-omega.y*3,steer*.9-omega.z*1.8),NONE,True)
 for n,a in S['physics'].items():
  if n==S['held'] or 'Tug' in n or 'dolly' in n:continue
  c=a.static_mesh_component;p=c.get_center_of_mass();x,y,z=source(p)
  for belt in D['conveyors']:
   if belt['stage']>STAGE or not belt['height']+.015<z<belt['height']+1.3:continue
   if belt['kind']=='carousel':
    cx,cy=belt['centre'];dx=x-cx;dy=y-cy
    if abs(dx)>5.1 or abs(dy)>2.0:continue
    if abs(dx)<=3:tx=dx;ty=math.copysign(1.25,dy);nx,ny=0,math.copysign(1,dy)
    else:ex=math.copysign(3,dx);ddx=dx-ex;l=math.hypot(ddx,dy);nx,ny=ddx/max(l,.01),dy/max(l,.01);tx=ex+nx*1.25;ty=ny*1.25
    sx,sy=-ny,nx;restore=v(((cx+tx-x)*2,(cy+ty-y)*2,0))
   else:
    x0,x1,y0,y1=belt['rect']
    if not x0<x<x1 or not y0<y<y1:continue
    sx,sy=belt['direction'];restore=u.Vector()
   if not supported_on_belt(c,belt):continue
   # Force transfer acts on real bodies; there is no frame-by-frame position assignment.
   want=u.Vector(sx*belt['speed']*100,-sy*belt['speed']*100,0);vel=c.get_physics_linear_velocity();acc=(want-u.Vector(vel.x,vel.y,0))*12+u.Vector(sx*500,-sy*500,0)+restore;mag=acc.length();c.add_force(acc*(min(mag,1400)/max(mag,1))*c.get_mass(),NONE,False)
   if '-AirportJourney22' not in CMD and belt['kind']=='bagdrop' and S.get('bag_drop_armed') and S['checked_in'] and not S['bag_accepted']:S['bag_accepted']=True;cue('ScannerReady',source(p));event('Physical bag accepted',actor=n)
   break
 for n,d in S['doors'].items():
  if d['automatic']:d['target']=1 if (pawn.get_actor_location()-d['closed']).length()<480 else 0
  f=d['fraction'];to=d['target'];d['fraction']=max(0,min(1,f+max(-dt,min(dt,to-f))*1.25));t=d['fraction'];t=t*t*(3-2*t);d['actor'].set_actor_location(d['closed']+d['delta']*t,False,False)
 x,y,z=source(pawn.get_actor_location())
 crossed=any(r[0]<x<r[1] and r[2]<y<r[3] for r in D.get('security_crossings',[])) if D.get('security_crossings') else -7.2<y<-5.8 and any(abs(x-px)<.52 for px in (-96,-85,-74,-63))
 if '-AirportJourney22' not in CMD and S['checked_in'] and not S['security'] and crossed and not (S['spectator'] or S['driving']):
  S['security']=True;cue('ScannerReady',(x,y,z));say('Security cleared Â· follow signs to Gate A07');event('Security portal crossed',x=x,y=y)
 if '-AirportJourney22' not in CMD and S['boarding'] and not S.get('aboard') and x>-1.9 and -.3<y<2.0:S['aboard']=True;say('Welcome aboard Skyward Air');event('Aircraft boarded by walking')
def tick(dt):
 if S['busy']:return
 S['busy']=True
 try:
  if not P.STATE.get('configured'):return
  if not S['ready']:initialize();return
  if not valid(P.STATE['pc']) or not valid(P.STATE['pawn']):u.unregister_slate_post_tick_callback(S['handle']);return
  now=time.perf_counter();S['frames'].append(now-S['last_frame']);S['last_frame']=now;S['ticks']+=1;pc=P.STATE['pc'];pawn=P.STATE['pawn'];m=pawn.get_component_by_class(u.FloatingPawnMovement)
  if pc.was_input_key_just_pressed(KEY['Tab']):toggle_spectator()
  if S['spectator']:
   m.set_editor_property('max_speed',1800 if pc.is_input_key_down(KEY['LeftShift']) else 600);pawn.add_movement_input(u.Vector(0,0,1),float(pc.is_input_key_down(KEY['SpaceBar']))-float(pc.is_input_key_down(KEY['LeftControl'])))
  elif not S['driving']:m.set_editor_property('max_speed',600 if pc.is_input_key_down(KEY['LeftShift']) else 360 if pawn.get_actor_location().x<-220 else 230)
  if STAGE>=7:physics(min(dt,.05))
  if D.get('revision',10)>=11:
   import airport_ext11_runtime;airport_ext11_runtime.tick(min(dt,.05),manual=S.get('manual_spray',False))
  if D.get('revision',10)>=12:
   import characters12_runtime;characters12_runtime.tick(min(dt,.05))
  if '-AirportRepair38' in CMD:
   import cabin68;cabin68.tick(__import__(__name__),min(dt,.05))
   import fixes70;fixes70.tick(__import__(__name__),min(dt,.05))
   import gameplay66;gameplay66.tick(min(dt,.05))
  if not CAPTURE and not QA and '-AirportClarity26' not in CMD:
   q=nearest();msg=S.get('message','') if time.monotonic()<S.get('message_until',0) else ''
   if S['held']:hint='Hold click: spray Â· E drop Â· R stow' if D.get('revision',10)>=11 and 'extinguisher' in S['held'].lower() else 'E drop  /  Click throw'+('  /  F equip' if '-AirportRepair38' in CMD and __import__('gameplay66').active() else '')
   elif S['driving']:hint='W/S drive Â· A/D steer Â· E exit'
   elif q:hint='E / Click Â· '+q['title']
   elif '-AirportRepair38' in CMD and __import__('gameplay66').active():hint=''
   else:hint='WASD move Â· Shift run Â· Tab spectator'+(' Â· V view Â· F7 pilot colour' if D.get('revision',10)>=12 else '')
   objective=__import__('airport_journey22').objective() if '-AirportJourney22' in CMD else ('Collect boarding pass' if not S['checked_in'] else 'Bag drop / security' if not S['security'] else 'Gate A07 Â· Flight SA107' if not S['boarding'] else 'Follow the jetbridge to the aircraft');(None if ('-AirportRepair38' in CMD and __import__('gameplay66').active()) else u.SystemLibrary.print_string(P.STATE['world'],objective+'\n'+(msg or hint),True,False,u.LinearColor(.85,.93,1,1),.12,u.Name('AirportJourney')))
  if S['ticks']%60==0:write()
 except Exception:
  error=traceback.format_exc();u.log_error(error);(R/'ArtBible/AirportRuntimeError.txt').write_text(error,encoding='utf-8');u.unregister_slate_post_tick_callback(S['handle'])
 finally:S['busy']=False
def start():
 global P
 import skyward_runtime as plane;P=plane
 if D.get('revision',10)>=11:
  if D.get('aircraft_revision',17)>=18:
   import plane18_runtime;plane18_runtime.install(P)
  else:
   import plane17_runtime;plane17_runtime.install(P)
 P.DATA=copy.deepcopy(P.DATA)
 if '-AirportRepair38' in CMD:
  import airport_airside38;airport_airside38.prepare_plane(P,D)
  if D.get('repair38',{}).get('exterior39'):
   import exterior39;exterior39.prepare_plane(P,D)
  if D.get('repair38',{}).get('window40'):
   import window40;window40.prepare_plane(P,D)
  if D.get('repair38',{}).get('window41'):
   import window41;window41.prepare_plane(P,D)
  if D.get('repair38',{}).get('posture39'):
   import chair_runtime39;chair_runtime39.prepare_plane(P,D)
  if D.get('repair38',{}).get('business_belt40'):
   import business_belt40;business_belt40.prepare_plane(P,D)
  if D.get('repair38',{}).get('business_belt41'):
   import business_belt41;business_belt41.prepare_plane(P,D)
  if D.get('repair38',{}).get('window42'):
   import window42;window42.prepare_plane(P,D)
  if D.get('repair38',{}).get('aircraft_finish42'):
   import aircraft_finish42;aircraft_finish42.prepare_plane(P,D)
  if D.get('repair38',{}).get('console_surface43'):
   import console_surface43;console_surface43.prepare_plane(P,D)
  if D.get('flight39'):
   import airport_flight39;airport_flight39.prepare_plane(P,D)
 P.DATA.setdefault('layout',{}).setdefault('navigation_floors',[]).extend(D['floors']);S['original_floor']=P.update_floor;S['original_use']=P.use_nearest;P.update_floor=floor_update;P.use_nearest=use_nearest;original_nearest=P.nearest
 def aircraft_nearest(kind=None):
  if P.STATE.get('pawn') and P.STATE['pawn'].get_actor_location().x<(1200 if '-AirportRepair38' in CMD else -600):return None
  return original_nearest(kind)
 P.nearest=aircraft_nearest
 if '-AirportRepair38' in CMD:
  import gameplay66;gameplay66.install(__import__(__name__))
 P.start();S['handle']=u.register_slate_post_tick_callback(tick);u.log('AIRPORT RUNTIME STARTED')
