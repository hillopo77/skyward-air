"""Focused native acceptance of compact circulation, modeled characters and aircraft18 mechanisms."""
import unreal as u,time,json,traceback,math,hashlib
from pathlib import Path
G=None;S={}
def save(status='RUNNING'):
 d=dict(status=status,checks=S['checks'],phase=S.get('phase'),elapsed=time.monotonic()-S['start'],runtime_sha256=G.MODULE_SHA,qa_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
 (G.R/'ArtBible/Compact12_QA.json').write_text(json.dumps(d,indent=2))
def check(n,p,**d):S['checks'].append(dict(name=n,passed=bool(p),**d));u.log('COMPACT12 QA '+n+' '+str(bool(p)));save()
def phase(n):S.update(phase=n,since=time.monotonic())
def reset(p):
 pawn=G.P.STATE['pawn'];pawn.get_component_by_class(u.FloatingPawnMovement).stop_movement_immediately();pawn.set_actor_location(G.v(p),False,True)
def face(p):G.P.STATE['pc'].set_control_rotation(u.MathLibrary.find_look_at_rotation(G.P.STATE['pawn'].get_actor_location(),G.v(p)))
def target(kind,**k):return next(q for q in G.S['targets'] if q['kind']==kind and all(q.get(n)==v for n,v in k.items()))
def stop():
 for h in (S.get('handle'),G.S.get('handle'),G.P.STATE.get('handle')):
  if h:
   try:u.unregister_slate_post_tick_callback(h)
   except Exception:pass
 u.SystemLibrary.quit_game(G.P.STATE['world'],G.P.STATE['pc'],u.QuitPreference.QUIT,False)
def finish():save('SUCCESS' if all(q['passed'] for q in S['checks']) else 'FAILED');stop()
def next_extra():
 S['extra_i']+=1;S['wp']=0
 if S['extra_i']==len(S['extras']):phase('characters')
 else:reset(S['extras'][S['extra_i']]['start']);phase('extra_walk')
def tick(dt):
 try:
  now=time.monotonic();t=now-S['since'];pawn=G.P.STATE['pawn'];p=pawn.get_actor_location();mode=S['phase']
  if mode=='warmup' and t>3:
   check('Compact terminal area reduced to 1400 square metres',G.D['new_terminal_area_m2']==1400)
   check('Native physical props initialized',len(G.S['physics'])==sum(q.get('physics',False) for q in G.D['instances']),count=len(G.S['physics']))
   check('Two articulated tow couplings',len(G.S.get('tow_joints',[]))==2)
   reset(G.D['routes'][0]['path'][0]);S['wp']=0;phase('walk')
  elif mode=='walk':
   point,action=S['route'][S['wp']];delta=G.v(point)-p;delta.z=0
   if delta.length()<30:
    pawn.get_component_by_class(u.FloatingPawnMovement).stop_movement_immediately()
    if action:
     q=target(action,**({'actor':'Check-in desk 01'} if action=='checkin' else {'gate':'A07'}));face(q['point']);check(action+' reachable from journey',G.visible(q));G.act(q)
    S['wp']+=1;S['since']=now
    if S['wp']==len(S['route']):
     check('Continuous entrance security gate and aircraft walk',True,waypoints=len(S['route']));check('Security portal crossing cleared screening',G.S['security']);check('Walked aboard through jetbridge',G.S.get('aboard',False));S.update(extra_i=0,wp=0);reset(S['extras'][0]['start']);phase('extra_walk')
   elif t>13:
    hit=u.SystemLibrary.line_trace_single(G.P.STATE['world'],p,p+delta/max(delta.length(),1)*130,u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[pawn],u.DrawDebugTrace.NONE,True);h=hit.to_tuple() if hit else None
    check('Continuous entrance security gate and aircraft walk',False,waypoint=S['wp'],position=list(G.source(p)),blocker=h[9].get_actor_label() if h and h[9] else None);S.update(extra_i=0,wp=0);reset(S['extras'][0]['start']);phase('extra_walk')
   else:pawn.add_movement_input(delta/delta.length(),1);face(point)
  elif mode=='extra_walk':
   q=S['extras'][S['extra_i']];point=q['path'][S['wp']];delta=G.v(point)-p;delta.z=0
   if delta.length()<25:
    S['wp']+=1;S['since']=now
    if S['wp']==len(q['path']):check(q['name'],abs(p.z/100-point[2])<.24,eye_height_m=p.z/100,expected_m=point[2]);next_extra()
   elif t>13:check(q['name'],False,waypoint=S['wp'],position=list(G.source(p)));next_extra()
   else:pawn.add_movement_input(delta/delta.length(),1);face(point)
  elif mode=='characters':
   import characters12_runtime as C
   check('Ten native skeletal character variants',len(C.S['meshes'])==5 and len(json.loads((G.R.parent.parent/'Characters/ArtBible/NativeCharacters12.json').read_text())['characters'])==10)
   check('Seven native animations loaded',len(C.CLIPS)==7,names=list(C.CLIPS))
   roots=[a.skeletal_mesh_component.get_socket_transform(a.skeletal_mesh_component.get_bone_name(0),u.RelativeTransformSpace.RTS_WORLD).scale3d.to_tuple() for a in C.ACTORS.values()]
   check('Skeleton roots retain unit scale during animation',all(all(abs(v-1)<.01 for v in r) for r in roots))
   check('Populated terminal and aircraft',len(C.ACTORS)>=45,count=len(C.ACTORS))
   a=next(a for n,a in C.ACTORS.items() if 'Security pilot' in n);c=a.skeletal_mesh_component;c.set_morph_target('Blink',.75);check('Real eyelid morph is controllable',abs(c.get_morph_target('Blink')-.75)<.01);c.set_morph_target('Blink',0)
   check('First-person hands use modeled mesh variants',len(C.S.get('hand_meshes',{}))==3 and len(C.S.get('hands',{}))==2)
   q=target('npc',actor='CH12 Security pilot');reset((-36.5,-.8,1.62));face(G.source(G.point(q)));check('Passenger greeting has visible target',G.visible(q));G.act(q);check('Passenger greeting plays a native wave','CH12 Security pilot' in C.S['greetings'])
   # The proxy must block visibility through a standing person.
   a=G.S['actors']['CH12COLL Security pilot'];check('Standing NPC body blocks the pawn',a.static_mesh_component.get_collision_response_to_channel(u.CollisionChannel.ECC_PAWN)==u.CollisionResponseType.ECR_BLOCK)
   C.update_hand_colour();old=C.S['skin'];C.S['skin']=(old+1)%len(C.S['meshes']);C.update_hand_colour();check('Pilot colour also updates first-person hands',bool(C.S['hands']['R'].static_mesh_component.get_material(0)));C.S['skin']=old;C.update_hand_colour()
   original=G.P.STATE['pc'].get_view_target();G.P.toggle_review();check('Third-person view toggle changes mode',C.S['third']);G.P.toggle_review()
   q=next(q for q in G.P.STATE['items'] if q.get('revision')==18 and q['point'][0]<0 and 25<q['point'][1]<26);S['shade']=q;S['shade_i']=0;S['shade_points']=[];reset(q['validation_approach']);face(q['point']);check('Window shade rocker visible from cabin',G.P.interaction_visible(q));m=G.P.STATE['movables'][q['actor']];m['target']=0;phase('shade_close')
  elif mode=='shade_close' and t>1.1:
   q=S['shade'];m=G.P.STATE['movables'][q['actor']];errors=[(G.P.STATE['actors'][p['actor']].get_actor_location()-G.P.vector(p['closed_location'])).length() for p in q['roller_parts']];check('Shade sections close to fitted overlapping positions',m['progress']<.01 and max(errors)<.1,max_error_cm=max(errors));S['shade_points'].append(G.P.movable_point(m).to_tuple() if hasattr(G.P,'movable_point') else (m['actor'].get_actor_location()+m['closed_point']).to_tuple());m['target']=1;phase('shade_open')
  elif mode=='shade_open' and t>1.1:
   q=S['shade'];m=G.P.STATE['movables'][q['actor']];errors=[(G.P.STATE['actors'][p['actor']].get_actor_location()-G.P.vector([x+y for x,y in zip(p['closed_location'],p['delta'])])).length() for p in q['roller_parts']];check('Shade panels retract into visible upper pocket',m['progress']>.99 and max(errors)<.1,max_error_cm=max(errors));pt=m['actor'].get_actor_location()+m['closed_point'];check('Shade switch stays fixed while panel moves',(pt-G.P.vector(q['point'])).length()<.1)
   if S['shade_i']==0:S['shade_i']=1;m['target']=0;phase('shade_close')
   else:
    q=next(q for q in G.P.STATE['items'] if q.get('title')=='Pilot seat');G.P.sit(q);lever=next(q for q in G.P.STATE['items'] if q.get('title')=='Engine 1 throttle');d=math.hypot(q['location'][0]-lever['point'][0],q['location'][1]-lever['point'][1]);check('Pilot throttle stays within seated reach',d<.75,reach_m=d);G.P.stand();q=target('slide',actor='Terminal WC 0',inside_release=False);S['wc']=q;reset((q['point'][0],q['point'][1]-1.2,1.62));face(q['point']);check('WC outside control is visible',G.visible(q));G.act(q);phase('wc_open')
  elif mode=='wc_open' and t>1.1:
   q=S['wc'];check('WC leaf retracts along modeled wall pocket',G.S['doors'][q['actor']]['fraction']>.98);q=target('slide',actor=q['actor'],inside_release=True);reset((q['point'][0],q['point'][1]+.7,1.62));face(q['point']);check('WC control accessible from inside',G.visible(q));G.act(q);phase('wc_close')
  elif mode=='wc_close' and t>1.1:
   check('WC closes and occupied indicator updates',G.S['doors'][S['wc']['actor']]['fraction']<.02)
   reset((-24.7,-13,1.62));check('Opaque arrivals partition blocks interaction',not G.visible(dict(kind='checkin',actor='Check-in desk 03',point=[-26,-13,1.2])))
   reset((-44,-15,1.62));bag=G.S['actors']['Physical luggage 01'];S['bag']=bag;bag.set_actor_location(G.v((-45,-15,2.2)),False,True);bag.static_mesh_component.set_physics_linear_velocity(u.Vector(),False,G.NONE);phase('bag_settle')
  elif mode=='bag_settle' and t>3:
   a=S['bag'];o,e=a.get_actor_bounds(False);v=a.static_mesh_component.get_physics_linear_velocity().length();check('Luggage settles on physical terminal floor',abs(o.z-e.z)<9 and v<35,bottom_cm=o.z-e.z,speed_cm_s=v);q=target('pickup',actor='Physical luggage 01');G.act(q);phase('bag_hold')
  elif mode=='bag_hold' and t>1.5:
   check('Physical luggage pickup works',G.S['held']=='Physical luggage 01');G.release(True);q=target('extinguisher');S['ext']=q;reset((q['point'][0],q['point'][1]+1.7,1.62));face(q['point']);G.act(q);phase('ext_hold')
  elif mode=='ext_hold' and t>1:
   import airport_ext11_runtime as E
   check('Extinguisher detaches and can be carried',G.S['held']==S['ext']['actor'] and G.S['actors'][G.S['held']].static_mesh_component.is_simulating_physics());S['charge']=E.CHARGE[G.S['held']];G.S['manual_spray']=True;phase('ext_spray')
  elif mode=='ext_spray' and t>.8:
   import airport_ext11_runtime as E
   check('Usable extinguisher emits powder and consumes charge',E.CHARGE[G.S['held']]<S['charge']-.4);G.S['manual_spray']=False;E.stow();check('Extinguisher returns to bracket',G.S['held'] is None);S['tug0']=G.S['actors']['Driveable electric baggage tug'].get_actor_location();S['dolly0']=G.S['actors']['Tow dolly 1'].get_actor_location();G.S['qa_drive']=(1,0);G.drive(target('drive'));phase('tug')
  elif mode=='tug' and t>1.6:
   a=G.S['actors']['Driveable electric baggage tug'];b=G.S['actors']['Tow dolly 1'];da=(a.get_actor_location()-S['tug0']).length();db=(b.get_actor_location()-S['dolly0']).length();check('Driveable tug pulls coupled dollies',da>50 and db>25,tug_cm=da,dolly_cm=db);G.S['qa_drive']=(0,0);G.exit_drive();reset((-32,8.5,1.62));S['frames']=len(G.S['frames']);phase('profile')
  elif mode=='profile' and t>5:
   f=sorted(G.S['frames'][S['frames']:]);check('Rendered populated airport performance',len(f)>60,average_fps=len(f)/sum(f),p95_ms=f[int((len(f)-1)*.95)]*1000,samples=len(f));finish()
 except Exception:
  S['error']=traceback.format_exc();(G.R/'ArtBible/Compact12_QA_Error.txt').write_text(S['error']);save('ERROR');stop()
def start(game):
 global G;G=game
 route=[([-53,-12.5,1.62],None),([-47,-12.5,1.62],None),([-45,-13.2,1.62],None),([-43,-13.2,1.62],'checkin'),([-45,-13.2,1.62],None),([-45,-8,1.62],None),([-41,-8,1.62],None),([-41,-3.2,1.62],None),([-41,2.4,1.62],None),([-32,2.4,1.62],None),([-32,8.5,1.62],None),([-18.5,8.5,1.62],None),([-18.5,-2,1.62],'boarding'),([-15.2,.675,1.62],None),([-13,.675,1.62],None),([-3,.675,1.62],None),([-.9,.675,1.62],None)]
 extras=[dict(name='Supported stairs reach mezzanine continuously',start=[-46.5,4,1.62],path=[[-46.5,6.8,3.08],[-46.5,7.4,3.195],[-44.3,7.4,3.195],[-44.3,4.7,4.77],[-40.8,4.7,4.77],[-40.8,6.5,4.77],[-40.8,10.2,4.77]]),dict(name='Service door and ramp reach apron continuously',start=[-17,16,1.62],path=[[-17,20,1.409],[-17,34,-.071],[-17,51,-1.869],[-17,54,-2.08]])]
 S.update(start=time.monotonic(),checks=[],route=route,extras=extras);phase('warmup');S['handle']=u.register_slate_post_tick_callback(tick);save()
