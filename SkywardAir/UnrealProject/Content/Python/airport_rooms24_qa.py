"""Rendered passenger process test using the actual pawn and interaction entry points."""
import unreal as u,time,json,traceback,hashlib,copy
from pathlib import Path
G=None;J=None;S={};R=Path(__file__).resolve().parents[4]/'Airport/Rooms24'

def report(status='RUNNING'):
 data=dict(status=status,phase=S.get('phase'),step=S.get('index'),elapsed_s=time.monotonic()-S['started'],checks=S['checks'],captures=S['captures'],continuous_walk=S.get('continuous',False),main_route_resets=S.get('main_resets',0),ticket=copy.deepcopy(J.S.get('ticket')),journey={k:G.S.get(k,False) for k in ['checked_in','bag_accepted','security','boarding','aboard']},seat=J.S.get('seat'),events=copy.deepcopy(J.S['events']),dependencies={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),Path(J.__file__),Path(G.__file__),Path(G.__file__).with_name('characters12_runtime.py')]});(R/'ArtBible/JourneyQA24.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
def check(name,passed,**details):S['checks'].append(dict(name=name,passed=bool(passed),**details));u.log('ROOMS24 '+name+' '+str(bool(passed)));report()
def stop():
 for handle in [S.get('handle'),G.S.get('handle'),G.P.STATE.get('handle')]:
  if handle:
   try:u.unregister_slate_post_tick_callback(handle)
   except Exception:pass
 u.SystemLibrary.quit_game(G.P.STATE['world'],G.P.STATE['pc'],u.QuitPreference.QUIT,False)
def reset(point):
 pawn=G.P.STATE['pawn'];pawn.get_component_by_class(u.FloatingPawnMovement).stop_movement_immediately();pawn.set_actor_location(G.v(point),False,True);J.S['previous']=point
 if S.get('continuous'):S['main_resets']+=1
def face(point):G.P.STATE['pc'].set_control_rotation(u.MathLibrary.find_look_at_rotation(G.P.STATE['pawn'].get_actor_location(),G.v(point)))
def target(kind,actor=None,**kw):return next(q for q in G.S['targets'] if q['kind']==kind and (actor is None or q['actor']==actor) and all(q.get(k)==v for k,v in kw.items()))
def go_next():S['index']+=1;S['since']=time.monotonic();S.pop('begun',None);report()
def invoke(kind,actor):
 q=target(kind,actor);face(G.source(G.point(q)));nearest=G.nearest();check('Usable '+kind+' target '+actor,bool(nearest and nearest['kind']==kind and nearest['actor']==actor),selected=nearest['actor'] if nearest else None,visible=G.visible(q));G.use_nearest();return q

def prelude():
 for name,start,end in [('Solid security boundary blocks a direct shortcut',[-39,-6,1.62],[-39,0,1.62]),('Gate enclosure blocks direct passage outside its approach',[-29,2.8,1.62],[-18,2.8,1.62])]:
  hit=u.SystemLibrary.line_trace_single(G.P.STATE['world'],G.v(start),G.v(end),u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[G.P.STATE['pawn']],u.DrawDebugTrace.NONE,True);h=hit.to_tuple() if hit else None;check(name,bool(h and h[0] and h[9] and h[9].get_actor_label()=='Walls24 modeled architecture'))
 reset((-42,-6,1.62));door=target('slide',access24='checked_in');G.act(door);check('Security entrance refuses entry before check-in',all(d['target']==0 for n,d in G.S['doors'].items() if n.startswith('Screening entry24')))
 reset((-18.5,-2,1.62));q=target('boarding',gate='A07');face(q['point']);G.act(q);check('Gate rejects boarding without check-in',not G.S['boarding'] and all(d['target']==0 for n,d in G.S['doors'].items() if n.startswith('A07 boarding')))
 reset((-37,-13.4,1.62));G.act(target('bagdrop','Bag drop belt 01'));check('Bag drop requires check-in',not G.S.get('bag_drop_armed'))
 # Isolated invalid-position fixtures exercise the old false-positive case.
 G.S.update(checked_in=True,security=True,boarding=True,aboard=False,spectator=True);reset((-.9,.675,1.62));S['phase']='negative_flight';S['since']=time.monotonic()

def begin_main():
 G.S.update(checked_in=False,security=False,boarding=False,aboard=False,spectator=False,bag_accepted=False,bag_drop_armed=False);J.S.update(ticket=None,seat=None,registered_bags=[],lane=None);G.S.pop('deposit_goal',None)
 for n in G.S['doors']:
  if n.startswith('A07 boarding'):G.open_door(n,0)
 reset((-53,-12.5,1.62));face(G.D['look_at']);S.update(phase='steps',index=0,since=time.monotonic(),continuous=True,main_resets=0);J.emit('Continuous passenger journey started')

def tick(dt):
 try:
  now=time.monotonic();t=now-S['since'];pawn=G.P.STATE['pawn']
  if S['phase']=='warmup':
   if t>3:prelude()
   return
  if S['phase']=='negative_flight':
   if t>.4:check('Spectator inside aircraft does not count as boarding',not G.S['aboard']);G.S['spectator']=False;reset((30,.675,1.62));S['phase']='negative_outside';S['since']=now
   return
  if S['phase']=='negative_outside':
   if t>.4:check('Airfield position cannot count as cabin boarding',not G.S['aboard']);begin_main()
   return
  if S.get('waiting_capture'):
   path=Path(S['waiting_capture'])
   if path.exists() and path.stat().st_mtime>=S['capture_requested']:
    S['captures'].append(dict(file=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),name=S['capture_name'],player=list(G.source(pawn.get_actor_location())),stage=J.stage()));S.pop('waiting_capture');go_next()
   elif t>20:raise RuntimeError('Screenshot did not complete: '+str(path))
   return
  if S['index']>=len(S['steps']):
   check('Main journey used continuous movement without teleports',S['main_resets']==0,resets=S['main_resets']);check('Player is seated aboard the aircraft',G.S['aboard'] and bool(G.P.STATE.get('seated')) and bool(J.S.get('seat')));report('SUCCESS' if all(q['passed'] for q in S['checks']) else 'FAILED');stop();return
  step=S['steps'][S['index']];kind=step[0]
  if kind=='walk':
   point=step[1];delta=G.v(point)-pawn.get_actor_location();delta.z=0
   if delta.length()<22:pawn.get_component_by_class(u.FloatingPawnMovement).stop_movement_immediately();go_next()
   elif t>15:
    hit=u.SystemLibrary.line_trace_single(G.P.STATE['world'],pawn.get_actor_location(),pawn.get_actor_location()+(delta/max(delta.length(),.001))*130,u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[pawn],u.DrawDebugTrace.NONE,True);h=hit.to_tuple() if hit else None;check('Route is walkable',False,goal=point,position=list(G.source(pawn.get_actor_location())),blocker=h[9].get_actor_label() if h and h[9] else None);report('FAILED');stop()
   else:face(point);pawn.add_movement_input((delta/max(delta.length(),.001)),1)
  elif kind=='act':invoke(step[1],step[2]);go_next()
  elif kind=='assert':
   name=step[1]
   if name=='held':check('Suitcase picked up through interaction',G.S['held']=='Physical luggage 01')
   elif name=='ticket':check('Check-in issued a real journey ticket',bool(J.S.get('ticket')) and G.S['checked_in'] and J.S['ticket']['seat']=='03E');J.S['pass_visible']=True
   elif name=='security':check('Full security traversal cleared the ticket',G.S['security'] and J.S['ticket']['security_cleared'])
   elif name=='wronggate':check('Gate A08 rejects an A07 boarding pass',not G.S['boarding'])
   elif name=='gate':check('Gate opens after validated boarding pass',G.S['boarding'] and J.S['ticket']['gate_scanned'])
   elif name=='aboard':check('Real bridge and door traversal registers boarding',G.S['aboard'] and J.S['ticket']['aboard'])
   elif name=='seat':check('Economy 03E can be entered and occupied',bool(G.P.STATE.get('seated')) and G.P.STATE['seated'].get('title')=='Economy 03E' and J.S['seat']=='Economy seat 03E12')
   go_next()
  elif kind=='wait_bag':
   if G.S['bag_accepted']:
    check('Checked bag is a native physical body on the belt','Physical luggage 01' in J.S['registered_bags'] and G.S['held'] is None and G.S['actors']['Physical luggage 01'].static_mesh_component.is_simulating_physics());S['bag_y']=G.source(G.S['actors']['Physical luggage 01'].get_actor_location())[1];go_next()
   elif t>9:check('Native bag placement and belt acceptance',False,held=G.S.get('held'),bag=G.source(G.S['actors']['Physical luggage 01'].static_mesh_component.get_center_of_mass()),goal=G.S.get('deposit_goal').to_tuple() if G.S.get('deposit_goal') else None);report('FAILED');stop()
  elif kind=='belt_motion':
   if t>1.3:
    moved=G.source(G.S['actors']['Physical luggage 01'].get_actor_location())[1]-S['bag_y'];check('Accepted suitcase is transported by conveyor forces',moved>.05,travel_m=moved);go_next()
  elif kind=='wait_access':
   if t>1.2:check(step[1]+' controlled door opens only after clearance',all(d['fraction']>.98 for n,d in G.S['doors'].items() if n.startswith(step[1])));go_next()
  elif kind=='zone':
   x,y,z=G.source(pawn.get_actor_location());room=next(q for q in G.D['zones'] if q['id']==step[1]);x0,x1,y0,y1=room['rect'];check('Walked into '+step[1],x0<x<x1 and y0<y<y1,position=[x,y,z]);go_next()
  elif kind=='height':
   z=pawn.get_actor_location().z/100;check(step[1],abs(z-step[2])<.16,height=z);go_next()
  elif kind=='wait_gate':
   if t>1.2:check('Both boarding door leaves actually open',all(d['fraction']>.98 for n,d in G.S['doors'].items() if n.startswith('A07 boarding')));go_next()
  elif kind=='seat':
   q=next(q for q in G.P.STATE['items'] if q['actor']=='Economy seat 03E12');face(q['point']);check('Assigned economy seat is visible from the aisle',G.P.interaction_visible(q));result=G.use_nearest();go_next()
  elif kind=='stand':G.P.stand();check('Standing restores normal camera height',G.P.STATE.get('seated') is None and abs(pawn.get_actor_location().z/100-1.62)<.12);go_next()
  elif kind=='photo':
   name=step[1];path=R/'ArtBible/RouteScreenshots'/(name+'.png');path.parent.mkdir(parents=True,exist_ok=True);S.update(waiting_capture=str(path),capture_name=name,capture_requested=time.time());u.SystemLibrary.execute_console_command(G.P.STATE['world'],'HighResShot 1600x1000 filename="'+path.as_posix()+'"',G.P.STATE['pc'])
 except Exception:
  (R/'ArtBible/JourneyQA24_Error.txt').write_text(traceback.format_exc(),encoding='utf-8');report('ERROR');stop()

def start(game):
 global G,J;G=game;import airport_journey22 as journey;J=journey
 steps=[]
 def walk(x,y,z=1.62):steps.append(('walk',[x,y,z]))
 def path(points):
  for p in points:walk(*p)
 def act(kind,actor):steps.append(('act',kind,actor))
 def zone(name):steps.append(('zone',name))
 def photo(name):steps.append(('photo',name))
 path([(-50,-12.5),(-46,-12.5)]);zone('entrancefoyer')
 walk(-46,-14.9);act('pickup','Physical luggage 01');steps.append(('assert','held'))
 path([(-45,-14),(-42,-14),(-41,-13),(-39,-13)]);zone('checkin')
 act('checkin','Check-in desk 01');steps.append(('assert','ticket'))
 path([(-39,-13.4),(-37,-13.4)]);act('bagdrop','Bag drop belt 01');steps.extend([('wait_bag',),('belt_motion',)])
 path([(-37,-13.4),(-30.6,-13.4),(-30.6,-9),(-30,-7.3),(-30,-6)]);zone('landsidecorridor')
 walk(-42,-6);steps.append(('wait_access','Screening entry24'))
 path([(-42,-3.0),(-45.5,-2.4),(-45.5,-1.3)]);zone('security')
 act('security','Security portal 01');walk(-45.5,1.2);steps.append(('assert','security'))
 path([(-45.5,3.5),(-38,3.5)]);steps.append(('wait_access','Screening exit24'))
 walk(-34,3.5);zone('recovery');path([(-34,1.5),(-30.5,1.5)]);zone('concourse');photo('01_NewConcourseRoute')
 path([(-30.5,8.5),(-34,8.5)]);zone('cafefoyer');walk(-34,10.65);zone('cafe')
 path([(-42.5,10.65),(-47.7,10.4),(-47.7,12.8),(-47.7,13.4),(-45.5,13.4),(-45.5,11.5),(-45.5,10.7),(-43.4,10.7),(-43.4,15.0)])
 steps.append(('height','Gallery reached on supported stairs',4.77));photo('02_GalleryReached')
 path([(-43.4,10.7),(-45.5,10.7),(-45.5,13.4),(-47.7,13.4),(-47.7,10.4),(-42.5,10.65),(-34,10.65),(-34,8.5),(-30.5,8.5)])
 steps.append(('height','Gallery descent restores normal eye height',1.62))
 path([(-30.5,-3),(-24.5,-3)]);zone('amenitylobby')
 path([(-24.5,-8.5),(-22.2,-8.5),(-22.2,-9.2),(-19,-9.2)]);zone('amenities')
 path([(-22.2,-9.2),(-22.2,-8.5),(-24.5,-8.5),(-24.5,-3),(-30.5,-3),(-30.5,11.5),(-24.5,11.5)]);zone('gate08foyer')
 path([(-24.5,15),(-22.7,15),(-22.7,14.0),(-18.9,14.0),(-18.9,10.1)]);zone('gate08')
 act('boarding','Gate A08 boarding desk');steps.append(('assert','wronggate'))
 path([(-18.9,14),(-22.7,14),(-22.7,15),(-24.5,15),(-24.5,11.5),(-30.5,11.5),(-30.5,4.5),(-24.5,4.5)]);zone('gate07foyer')
 path([(-24.5,.5),(-22.5,.5)]);zone('gate07')
 path([(-19,.5),(-18.9,-2)]);act('boarding','Gate A07 boarding desk');steps.extend([('assert','gate'),('wait_gate',)])
 path([(-19,.3),(-15.4,.3),(-15.2,.675),(-13,.675),(-7,.675)]);photo('03_JetbridgeReached')
 walk(-.9,.675);steps.append(('assert','aboard'))
 path([(.55,.675),(.55,3),(.55,8.65),(.55,9.2),(1.35,9.2),(1.35,12.8),(1.12,13),(1.12,13.655)])
 steps.extend([('seat',),('assert','seat')]);photo('04_SeatedAboard');steps.extend([('stand',),('seat',),('assert','seat')])
 S.update(started=time.monotonic(),since=time.monotonic(),phase='warmup',checks=[],captures=[],steps=steps,index=0,main_resets=0);S['handle']=u.register_slate_post_tick_callback(tick);report()

