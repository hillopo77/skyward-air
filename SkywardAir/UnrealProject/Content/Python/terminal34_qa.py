"""One focused room walk and four actual viewport captures, no airport-wide replay."""
import unreal as u,time,json,traceback,hashlib
G=None;S={}
def save(status='RUNNING',**kw):
 (G.R/'ArtBible/TerminalQA34.json').write_text(json.dumps(dict(status=status,checks=S['checks'],captures=S['captures'],step=S['i'],continuous_walk=True,teleports=0,elapsed_s=time.monotonic()-S['start'],viewport=list(G.P.STATE['pc'].get_viewport_size()),journey={k:G.S.get(k,False) for k in ['checked_in','bag_accepted','security','aboard']},**kw),indent=2),encoding='utf-8')
def check(n,b,**kw):S['checks'].append(dict(name=n,passed=bool(b),**kw));save()
def advance():S['i']+=1;S['since']=time.monotonic();S.pop('begun',None)
def face(p):G.P.STATE['pc'].set_control_rotation(u.MathLibrary.find_look_at_rotation(G.P.STATE['pawn'].get_actor_location(),G.v(p)))
def stop(status,**kw):
 save(status,**kw)
 for h in [S.get('handle'),G.S.get('handle'),G.P.STATE.get('handle')]:
  if h:
   try:u.unregister_slate_post_tick_callback(h)
   except Exception:pass
 u.SystemLibrary.quit_game(G.P.STATE['world'],G.P.STATE['pc'],u.QuitPreference.QUIT,False)
def tick(dt):
 try:
  t=time.monotonic()-S['since'];pawn=G.P.STATE['pawn'];pc=G.P.STATE['pc']
  if S.get('waiting'):
   p=S['waiting']
   if p.exists() and p.stat().st_mtime>=S['requested']:S['captures'].append(dict(file=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),view=S['photo_name']));S.pop('waiting');advance()
   elif t>20:raise RuntimeError('Screenshot timeout')
   return
  if S['i']>=len(S['steps']):stop('SUCCESS' if all(q['passed'] for q in S['checks']) else 'FAILED');return
  step=S['steps'][S['i']];op=step[0]
  if op=='wait':
   if t>step[1]:advance()
  elif op=='initial':
   import airport_clarity26 as C
   check('Starts with check-in objective',C.phase()=='CheckIn');check('Native viewport1920x1080',tuple(pc.get_viewport_size())==(1920,1080))
   for i in range(2):
    n='Check-in desk %02d'%(i+1);a=G.S['actors'][n];q=G.S['actor_specs'][n];check(n+' quarter-turn matches layout',abs(u.MathLibrary.normalized_delta_rotator(a.get_actor_rotation(),u.Rotator(yaw=90)).yaw)<.1);check(n+' placed correctly',(a.get_actor_location()-G.v(q['location'])).length()<1)
   for c in G.D['conveyors']:
    if c['kind']=='bagdrop':check(c['name']+' travels along rotated belt',c['direction']==[1,0] and 'load_point' in c)
   check('Set-back queue has two waiting passengers',len([q for q in G.D['character_placements'] if q['name'].startswith('Queue passenger ')])==2)
   check('Two staffed counters',len([q for q in G.D['instances'] if q['name'].startswith('Check-in desk ')])==2)
   check('Queue width is1.9m',G.D['checkin29']['single_queue_width_m']>=1.9)
   advance()
  elif op=='walk':
   d=G.v(step[1])-pawn.get_actor_location();d.z=0
   if d.length()<18:pawn.get_component_by_class(u.FloatingPawnMovement).stop_movement_immediately();check('Walk reaches '+str(step[1][:2]),True);advance()
   elif t>14:check('Walk remains clear',False,goal=step[1],position=list(G.source(pawn.get_actor_location())));stop('FAILED')
   else:face(step[1]);pawn.add_movement_input(d/max(d.length(),.001),1)
  elif op=='arrival':
   import airport_checkin30 as Q
   import airport_arrival31 as A
   face(next(q['point'] for q in G.S['targets'] if q['actor']=='Queue entry marker29'));q=G.nearest();check('Entrance does not offer immediate queue interaction',not q or q['actor']!='Queue entry marker29');check('Arrival is separate from process',not Q.S['joined']);check('Queue moved more than4m beyond pocket',G.D['arrival31']['clear_buffer_from_pocket_m']>=4);advance()
  elif op=='right':
   import airport_checkin30 as Q
   check('Right-side waiting route accessible before joining',not Q.S['joined']);advance()
  elif op=='back':
   x,y,z=G.source(pawn.get_actor_location());last=G.S['actors']['CH12 Queue passenger 3'].get_actor_location();q=G.source(last);check('Entry arrives behind the last queue passenger',x<q[0]-.60 and abs(y-q[1])<.3,player=[x,y],last_passenger=list(q[:2]));advance()
  elif op=='act':
   q=next(q for q in G.S['targets'] if q['kind']==step[1] and q['actor']==step[2])
   if not S.get('begun'):face(G.source(G.point(q)));S['begun']=True;S['since']=time.monotonic();return
   if t<.25:return
   nearest=G.nearest();ok=nearest and nearest['actor']==q['actor'] and nearest['kind']==q['kind'];check('Aim reaches '+q['actor'],ok,selected=nearest['actor'] if nearest else None)
   if ok:G.use_nearest()
   advance()
  elif op=='return':G.CAPTURE=False;pc.set_view_target_with_blend(pawn,0);advance()
  elif op=='guard':
   q=next(q for q in G.S['targets'] if q['kind']=='checkin' and q['actor']=='Check-in desk 01');G.act(q);check('Counter rejects queue jumping',not G.S['checked_in']);advance()
  elif op=='queue':
   import airport_checkin30 as Q
   if Q.S['called']:check('Live queue advances both passengers',len(Q.S['departures'])==2);check('Player is called to the desk',Q.S['called']);advance()
   elif t>18:check('Queue calls the player',False);stop('FAILED')
  elif op=='crowd':
   import airport_checkin30 as Q
   ps=[G.S['actors'][n].get_actor_location() for n in G.D['checkin30']['npc_order']];spacing=min((a-b).length()/100 for i,a in enumerate(ps) for b in ps[i+1:]);check('Departing passengers remain separated in corridor',spacing>=1.5,minimum_spacing_m=spacing);advance()
  elif op=='ticket':check('Rotated counter issues boarding pass',G.S.get('checked_in') and not G.S.get('security'));advance()
  elif op=='bag':
   if G.S.get('bag_accepted'):check('Rotated conveyor accepts the physical suitcase',True);advance()
   elif t>10:check('Physical suitcase accepted',False);stop('FAILED')
  elif op=='access':
   if t>1.2:check(step[1]+' access opens',all(d['fraction']>.98 for n,d in G.S['doors'].items() if n.startswith(step[1])));advance()
  elif op=='security':
   import airport_journey22 as J
   check('Security actually clears the boarding pass',G.S['security'] and J.S['ticket']['security_cleared']);advance()
  elif op=='gate':
   import airport_journey22 as J
   check('A07 actually validates the boarding pass',G.S['boarding'] and J.S['ticket']['gate_scanned']);advance()
  elif op=='aboard':
   import airport_journey22 as J
   check('Jetbridge reaches the real aircraft',G.S['aboard'] and J.S['ticket']['aboard']);check('Eye height retained after whole journey',abs(pawn.get_actor_location().z/100-1.62)<.05);advance()
  elif op=='exit':check('Room exit connects to the unchanged landside corridor',abs(G.source(pawn.get_actor_location())[1]+6)<.25);advance()
  elif op=='photo':
   if not S.get('begun'):
    if len(step)>2:face(step[2])
    S['begun']=True;S['since']=time.monotonic();return
   if t<.8:return
   p=G.R/'Screenshots'/(step[1]+'.png');S.update(waiting=p,requested=time.time(),photo_name=step[1]);u.SystemLibrary.execute_console_command(G.P.STATE['world'],'Shot -nosuffix filename="'+p.as_posix()+'"',pc)
  elif op=='view':G.CAPTURE=True;pc.set_view_target_with_blend(G.S['cameras'][step[1]],0);advance()
  elif op=='overview':
   cam=G.S['cameras']['06_RoomOverview'];pc.set_view_target_with_blend(cam,0);advance()
 except Exception:stop('ERROR',error=traceback.format_exc())
def start(game):
 global G;G=game;steps=[('wait',3),('initial',)]
 def path(points):
  for p in points:steps.append(('walk',[*p,1.62]))
 def act(kind,name):steps.append(('act',kind,name))
 # Show the first completed section immediately, then capture the other destinations.
 for view in [q['name'] for q in G.D['cameras'] if q['name'].startswith(tuple('%02d_'%i for i in range(1,19))) and q['name'] in [q['name'] for q in json.loads((G.R/'Exports/Changes34.json').read_text())['views']]]:steps += [('view',view),('photo',view),('return',)]
 # Public arrivals loop is physically separate from screened departures.
 path([[-51,-12.5],[-51,-20],[-49,-20],[-26,-20],[-24,-20],[-20,-20.4],[-24,-20],[-26,-20],[-49,-20],[-51,-20],[-51,-12.5]])
 # Existing staffed check-in, live queue and physical suitcase acceptance.
 path([[-48.3,-12.5],[-46,-15],[-42,-15],[-42,-13]]);steps += [('arrival',)]
 path([[-40.4,-13],[-40.4,-16],[-37.6,-16]]);steps += [('right',)]
 path([[-40.4,-16],[-40.4,-13],[-37.4,-13]]);steps += [('back',),('guard',)];act('information','Queue entry marker29');steps += [('queue',)]
 path([[-32.1,-13],[-32.1,-10.6],[-31.8,-10.6]]);act('checkin','Check-in desk 01');steps += [('ticket',)]
 path([[-33,-10.6],[-33,-15.7],[-35.7,-15.8]]);act('pickup','Physical luggage 02')
 path([[-32.1,-15.7],[-31.8,-12.6],[-30.7,-12.6]]);act('bagdrop','Bag drop belt 01');steps += [('bag',)]
 path([[-32.1,-12.6],[-32.1,-8.8],[-30,-8.8],[-30,-6]]);steps += [('exit',)]
 path([[-42,-6],[-42,-5.3]]);steps += [('access','Screening entry24')]
 path([[-42,-3],[-45.5,-2],[-45.5,-1.3]]);act('security','Security portal 01');path([[-45.5,1.2]]);steps += [('security',)]
 path([[-45.5,3.5],[-38,3.5]]);steps += [('access','Screening exit24')]
 path([[-34,3.5],[-34,1.5],[-30.5,1.5]])
 # Walk into the cafe, the other gate lounge and the lavatory lobby.
 path([[-30.5,8.5],[-34,8.5],[-34,10.8],[-35.1,10.8],[-34,10.8],[-34,8.5],[-29,8.5],[-29,11.5],[-24.5,11.5],[-24.5,15],[-22.5,15],[-19,14.3],[-22.5,15],[-24.5,15],[-24.5,11.5],[-29,11.5],[-29,-3],[-24.5,-3],[-24.5,-8.5],[-22,-8.5],[-19,-8.5],[-22,-8.5],[-24.5,-8.5],[-24.5,-3],[-29,-3]])
 # A07 boarding pass, controlled boarding doors and real aircraft threshold.
 path([[-29,4.5],[-24.5,4.5],[-24.5,.5],[-22.5,.5],[-19,.5],[-18.9,-2]]);act('boarding','Gate A07 boarding desk');steps += [('gate',),('access','A07 boarding')]
 path([[-19,.3],[-15.4,.3],[-15.2,.675],[-13,.675],[-7,.675],[-.9,.675]]);steps += [('aboard',)]
 S.update(i=0,checks=[],captures=[],steps=steps,start=time.monotonic(),since=time.monotonic());S['handle']=u.register_slate_post_tick_callback(tick);save()
