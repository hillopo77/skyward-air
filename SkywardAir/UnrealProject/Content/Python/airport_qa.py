"""Native airport acceptance run. Walks the route through collision; props use Chaos forces."""
import unreal as u,time,json,traceback,math,hashlib
from pathlib import Path
G=None;S={}
def check(name,passed,**detail):S['checks'].append(dict(name=name,passed=bool(passed),**detail));u.log('AIRPORT QA '+name+' '+str(bool(passed)));save()
def save(status='RUNNING'):
 d=dict(status=status,checks=S['checks'],runtime_sha256=G.MODULE_SHA,qa_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),phase=S.get('phase'),elapsed=time.monotonic()-S['start']);(G.R/'ArtBible/Revision11_QA.json').write_text(json.dumps(d,indent=2))
def advance(phase):S.update(phase=phase,since=time.monotonic())
def reset(p):
 pawn=G.P.STATE['pawn'];pawn.get_component_by_class(u.FloatingPawnMovement).stop_movement_immediately();pawn.set_actor_location(G.v(p),False,True)
def face(point):G.P.STATE['pc'].set_control_rotation(u.MathLibrary.find_look_at_rotation(G.P.STATE['pawn'].get_actor_location(),G.v(point)))
def target(kind,**kw):return next(q for q in G.S['targets'] if q['kind']==kind and all(q.get(k)==v for k,v in kw.items()))
def bounds(a):o,e=a.get_actor_bounds(False);return o.z-e.z

def tick(dt):
 try:
  now=time.monotonic();t=now-S['since'];pawn=G.P.STATE['pawn'];phase=S['phase']
  if phase=='warmup' and t>3:
   check('All authored native physics bodies initialized',len(G.S['physics'])==sum(q.get('physics',False) and q['stage']<=G.STAGE for q in G.D['instances']),count=len(G.S['physics']));check('Two native articulated tow couplings',len(G.S.get('tow_joints',[]))==2)
   reset((-78,-55,1.62));S['waypoint']=0;advance('walk')
  elif phase=='walk':
   i=S['waypoint'];point,action=S['path'][i];p=pawn.get_actor_location();delta=G.v(point)-p;delta.z=0
   if delta.length()<55:
    pawn.get_component_by_class(u.FloatingPawnMovement).stop_movement_immediately()
    if action:
     q=target(action,**({'gate':'A07'} if action=='boarding' else {'actor':'Check-in desk 04'}));face(q['point']);check(action+' action has line of sight',G.visible(q));G.act(q)
    S['waypoint']+=1;S['since']=now
    if S['waypoint']==len(S['path']):
     check('Continuous entrance to aircraft walk',True,waypoints=len(S['path']),position=list(G.source(pawn.get_actor_location())));check('Security cleared by crossing portal',G.S['security']);check('Boarding gate opened after clearance',G.S['boarding']);S['walk_end']=now;advance('boarded')
   else:
    pawn.add_movement_input(delta/delta.length(),1);face((point[0],point[1],point[2]))
    if t>20:
     hit=u.SystemLibrary.line_trace_single(G.P.STATE['world'],p,p+delta/delta.length()*150,u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[pawn],u.DrawDebugTrace.NONE,True);h=hit.to_tuple() if hit else None
     check('Continuous entrance to aircraft walk',False,stuck_waypoint=i,position=list(G.source(p)),blocker=h[9].get_actor_label() if h and h[9] else None);advance('boarded')
  elif phase=='boarded' and t>1:
   check('Aircraft boarding event detected',bool(G.S.get('aboard')));check('Sliding leaves occupy their modeled pockets',all(d['fraction']>.98 for n,d in G.S['doors'].items() if n.startswith('A07 boarding')))
   S['cubicle']=next(q for q in G.S['targets'] if q.get('fixed_release') and not q.get('inside_release'));q=S['cubicle'];reset((q['point'][0],1.6,1.62));face(q['point']);check('Cubicle outside release visible',G.visible(q));G.act(q);advance('cubicle_open')
  elif phase=='cubicle_open' and t>1.2:
   q=S['cubicle'];check('Cubicle slides into modeled pocket',G.S['doors'][q['actor']]['fraction']>.98);inside=next(t for t in G.S['targets'] if t['actor']==q['actor'] and t.get('inside_release'));reset((inside['point'][0],4.2,1.62));face(inside['point']);check('Cubicle inside release remains accessible',G.visible(inside));G.act(inside);advance('cubicle_close')
  elif phase=='cubicle_close' and t>1.2:
   check('Cubicle closes from inside pocket enclosure',G.S['doors'][S['cubicle']['actor']]['fraction']<.02)
   reset((-49,-34,1.62));q=dict(kind='checkin',actor='Check-in desk 01',point=[-47,-34,1.62]);check('Opaque wall blocks interaction',not G.visible(q))
   S['extra_index']=0;S['extra_wp']=0;reset(S['extra'][0]['start']);advance('extra_walk')
  elif phase=='extra_walk':
   route=S['extra'][S['extra_index']];point=route['path'][S['extra_wp']];p=pawn.get_actor_location();delta=G.v(point)-p;delta.z=0
   if delta.length()<30:
    S['extra_wp']+=1;S['since']=now
    if S['extra_wp']==len(route['path']):
     z=pawn.get_actor_location().z/100;check(route['name'],abs(z-point[2])<.22,height_m=z,expected_m=point[2]);S['extra_index']+=1;S['extra_wp']=0
     if S['extra_index']==len(S['extra']):advance('prepare_drop')
     else:reset(S['extra'][S['extra_index']]['start'])
   elif t>15:
    check(route['name'],False,stuck_waypoint=S['extra_wp'],position=list(G.source(p)));S['extra_index']+=1;S['extra_wp']=0
    if S['extra_index']==len(S['extra']):advance('prepare_drop')
    else:reset(S['extra'][S['extra_index']]['start']);S['since']=now
   else:pawn.add_movement_input(delta/delta.length(),1);face(point)
  elif phase=='prepare_drop':
   reset((-33,16,1.62));bag=G.S['actors']['Physical luggage 12'];bag.set_actor_location(G.v((-31,16,2.8)),False,True);c=bag.static_mesh_component;c.set_physics_linear_velocity(u.Vector(),False,G.NONE);c.set_physics_angular_velocity_in_radians(u.Vector(),False,G.NONE);bag.set_actor_rotation(u.Rotator(),False);S['bag']=bag;advance('drop')
  elif phase=='drop' and t>4:
   bag=S['bag'];bottom=bounds(bag);speed=bag.static_mesh_component.get_physics_linear_velocity().length();check('Suitcase settles on actual terminal floor',abs(bottom)<8 and speed<30,bottom_cm=bottom,speed_cm_s=speed)
   q=target('pickup',actor='Physical luggage 12');face(G.source(bag.static_mesh_component.get_center_of_mass()));G.act(q);G.P.STATE['pc'].set_control_rotation(u.Rotator(pitch=0,yaw=0));advance('hold')
  elif phase=='hold' and t>2:
   bag=S['bag'];distance=(bag.static_mesh_component.get_center_of_mass()-pawn.get_actor_location()).length();check('Spring-force luggage pickup',G.S['held']=='Physical luggage 12' and distance<180,distance_cm=distance);G.release(True);S['throw_start']=bag.get_actor_location();advance('throw')
  elif phase=='throw' and t>.6:
   distance=(S['bag'].get_actor_location()-S['throw_start']).length();check('Luggage throw uses physical impulse',distance>100,travel_cm=distance)
   bag=S['bag'];bag.set_actor_rotation(u.Rotator(),False);bag.set_actor_location(G.v((-71.5,-8.1,.90)),False,True);bag.static_mesh_component.set_physics_linear_velocity(u.Vector(),False,G.NONE);bag.static_mesh_component.set_physics_angular_velocity_in_radians(u.Vector(),False,G.NONE);S['belt_start']=bag.get_actor_location();advance('belt')
  elif phase=='belt' and t>1.8:
   p=S['bag'].get_actor_location();distance=-(p.y-S['belt_start'].y);check('Scanner conveyor moves supported physical luggage',distance>20,forward_cm=distance,position=list(G.source(p)))
   S['tug_start']=G.S['actors']['Driveable electric baggage tug'].get_actor_location();S['dolly_start']=G.S['actors']['Tow dolly 1'].get_actor_location();G.S['qa_drive']=(1,0);G.drive(target('drive'));advance('tow')
  elif phase=='tow' and t>2:
   tug=G.S['actors']['Driveable electric baggage tug'];dolly=G.S['actors']['Tow dolly 1'];d1=(tug.get_actor_location()-S['tug_start']).length();d2=(dolly.get_actor_location()-S['dolly_start']).length();check('Powered tug pulls constrained baggage dollies',d1>60 and d2>30,tug_travel_cm=d1,dolly_travel_cm=d2);G.S['qa_drive']=(0,0);G.exit_drive();S['profile_start']=len(G.S['frames']);advance('profile')
  elif phase=='profile' and t>6:
   f=sorted(G.S['frames'][S['profile_start']:]);check('Rendered idle performance sample',len(f)>60,samples=len(f),average_fps=len(f)/sum(f),p95_ms=f[int((len(f)-1)*.95)]*1000,max_ms=max(f)*1000)
   if G.D.get('revision',10)>=11:
    S['tray']=next(q for q in G.P.STATE['items'] if q.get('revision')==17);moving=G.P.STATE['movables'][S['tray']['actor']];moving['target']=1.;advance('tray17_open')
   else:finish()
  elif phase=='tray17_open' and t>1:
   m=G.P.STATE['movables'][S['tray']['actor']];o,e=m['actor'].get_actor_bounds(False);check('Meal tray opens flat and lifts in captive guides',m['progress']>.98 and e.z<4,half_height_cm=e.z);m['target']=0.;advance('tray17_close')
  elif phase=='tray17_close' and t>1:
   check('Meal tray returns to fitted seat-back recess',G.P.STATE['movables'][S['tray']['actor']]['progress']<.02);pilot=next(q for q in G.P.STATE['items'] if q.get('title')=='Pilot seat');G.P.sit(pilot);lever=next(q for q in G.P.STATE['items'] if q.get('title')=='Engine 1 throttle');p=pilot['location'];d=math.hypot(p[0]-lever['point'][0],p[1]-lever['point'][1]);check('Pilot throttle is within seated horizontal reach',d<.75,reach_m=d);G.P.stand();q=next(q for q in G.S['targets'] if q['kind']=='extinguisher');S['ext']=q;reset((q['point'][0],q['point'][1]+2,1.62));face(q['point']);check('Extinguisher has an unobstructed pickup target',G.visible(q));G.act(q);advance('ext_pickup')
  elif phase=='ext_pickup' and t>1.5:
   import airport_ext11_runtime as ext;body=G.S['actors'][G.S['held']];travel=(body.get_actor_location()-ext.HOMES[G.S['held']].translation).length();check('Extinguisher detaches as a physical held object',G.S['held']==S['ext']['actor'] and body.static_mesh_component.is_simulating_physics() and travel>20,travel_cm=travel);S['ext_charge']=ext.CHARGE[G.S['held']];G.P.STATE['pc'].set_control_rotation(u.Rotator(pitch=-5,yaw=-35));G.S['manual_spray']=True;advance('ext_spray')
  elif phase=='ext_spray' and t>.65 and not S.get('spray_photo'):
   S['spray_photo']=G.R/'Screenshots/Revision11_23_ExtinguisherUse.png';S['spray_requested']=time.time();u.SystemLibrary.execute_console_command(G.P.STATE['world'],'HighResShot 1600x1000 filename="'+S['spray_photo'].as_posix()+'"',G.P.STATE['pc'])
  elif phase=='ext_spray' and t>1.2 and S.get('spray_photo') and S['spray_photo'].exists() and S['spray_photo'].stat().st_mtime>=S['spray_requested']:
   import airport_ext11_runtime as ext;check('Powder discharge consumes charge and renders a jet',ext.CHARGE[G.S['held']]<S['ext_charge']-.5 and not ext.FX.get_editor_property('hidden') and ext.FX.get_actor_scale3d().y>.35 and u.MathLibrary.get_up_vector(G.S['actors'][G.S['held']].get_actor_rotation()).z>.8,reach_scale=ext.FX.get_actor_scale3d().y,upright_z=u.MathLibrary.get_up_vector(G.S['actors'][G.S['held']].get_actor_rotation()).z);G.S['manual_spray']=False;ext.stow();advance('ext_stow')
  elif phase=='ext_stow' and t>.5 and (not S.get('spray_photo') or S['spray_photo'].exists()):
   import airport_ext11_runtime as ext;check('Extinguisher returns to its physical bracket',G.S['held'] is None and not G.S['actors'][S['ext']['actor']].static_mesh_component.is_simulating_physics());finish()
 except Exception:
  (G.R/'ArtBible/AirportQA_Error.txt').write_text(traceback.format_exc(),encoding='utf-8');save('ERROR');stop()
def finish():
 status='SUCCESS' if all(q['passed'] for q in S['checks']) else 'FAILED';save(status);stop()
def stop():
 for h in (S.get('handle'),G.S.get('handle'),G.P.STATE.get('handle')):
  if h:
   try:u.unregister_slate_post_tick_callback(h)
   except Exception:pass
 u.SystemLibrary.quit_game(G.P.STATE['world'],G.P.STATE['pc'],u.QuitPreference.QUIT,False)
def start(game):
 global G;G=game;S.update(start=time.monotonic(),checks=[],path=[([-78,-40,1.62],None),([-76,-35,1.62],None),([-74,-29,1.62],'checkin'),([-78,-22,1.62],None),([-74,-19,1.62],None),([-74,-12,1.62],None),([-74,-6,1.62],None),([-74,3,1.62],None),([-74,6,1.62],None),([-54,6,1.62],None),([-50,5,1.62],None),([-33,5,1.62],None),([-30,-3.325,1.62],'boarding'),([-27,.675,1.62],None),([-20,.675,1.62],None),([-8,.675,1.62],None),([-3,.675,1.62],None),([-.9,.675,1.62],None)]);S['extra']=[dict(name='Stairs and upper landing reach mezzanine',start=[-94.5,2.4,1.62],path=[[-94.5,6.7,3.65],[-94.5,7.2,3.72],[-90.5,7.2,3.72],[-90.5,3,5.82],[-87,3,5.82],[-87,8.5,5.82],[-90,11,5.82]]),dict(name='Service ramp reaches apron continuously',start=[-25.5,38,1.62],path=[[-25.5,45,.757],[-25.5,60,-1.093],[-25.5,69,-2.08],[-22,69,-2.08]])];advance('warmup');S['handle']=u.register_slate_post_tick_callback(tick);save()
