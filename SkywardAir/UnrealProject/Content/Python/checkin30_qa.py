"""One focused room walk and four actual viewport captures, no airport-wide replay."""
import unreal as u,time,json,traceback,hashlib
G=None;S={}
def save(status='RUNNING',**kw):
 (G.R/'ArtBible/CheckinQA30.json').write_text(json.dumps(dict(status=status,checks=S['checks'],captures=S['captures'],step=S['i'],continuous_walk=True,teleports=0,elapsed_s=time.monotonic()-S['start'],viewport=list(G.P.STATE['pc'].get_viewport_size()),journey={k:G.S.get(k,False) for k in ['checked_in','bag_accepted','security','aboard']},**kw),indent=2),encoding='utf-8')
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
   check('One queue with three waiting passengers',len([q for q in G.D['character_placements'] if q['name'].startswith('Queue passenger ')])==3)
   check('Two staffed counters',len([q for q in G.D['instances'] if q['name'].startswith('Check-in desk ')])==2)
   check('Queue width is1.9m',G.D['checkin29']['single_queue_width_m']>=1.9)
   advance()
  elif op=='walk':
   d=G.v(step[1])-pawn.get_actor_location();d.z=0
   if d.length()<18:pawn.get_component_by_class(u.FloatingPawnMovement).stop_movement_immediately();check('Walk reaches '+str(step[1][:2]),True);advance()
   elif t>14:check('Walk remains clear',False,goal=step[1],position=list(G.source(pawn.get_actor_location())));stop('FAILED')
   else:face(step[1]);pawn.add_movement_input(d/max(d.length(),.001),1)
  elif op=='back':
   x,y,z=G.source(pawn.get_actor_location());last=G.S['actors']['CH12 Queue passenger 0'].get_actor_location();q=G.source(last);check('Entry arrives behind the last queue passenger',x<q[0]-.60 and abs(y-q[1])<.3,player=[x,y],last_passenger=list(q[:2]));advance()
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
   if Q.S['called']:check('Live queue advances all three passengers',len(Q.S['departures'])==3);check('Player is called to the desk',Q.S['called']);advance()
   elif t>18:check('Queue calls the player',False);stop('FAILED')
  elif op=='crowd':
   import airport_checkin30 as Q
   ps=[G.S['actors'][n].get_actor_location() for n in G.D['checkin30']['npc_order']];spacing=min((a-b).length()/100 for i,a in enumerate(ps) for b in ps[i+1:]);check('Departing passengers remain separated in corridor',spacing>=1.5,minimum_spacing_m=spacing);advance()
  elif op=='ticket':check('Rotated counter issues boarding pass',G.S.get('checked_in') and not G.S.get('security'));advance()
  elif op=='bag':
   if G.S.get('bag_accepted'):check('Rotated conveyor accepts the physical suitcase',True);advance()
   elif t>10:check('Physical suitcase accepted',False);stop('FAILED')
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
 global G;G=game;steps=[('wait',2),('initial',)]
 def path(points):
  for p in points:steps.append(('walk',[*p,1.62]))
 # A single engine session: quality view first, then live queue and baggage check.
 path([[-48.3,-12.5],[-46,-15],[-42,-15],[-42,-13]]);steps += [('view','01_Arrival'),('photo','01_Arrival'),('return',)]
 path([[-40.8,-13],[-39.4,-13]]);steps += [('back',),('guard',),('act','information','Queue entry marker29'),('queue',)]
 path([[-32.1,-13],[-32.1,-10.6],[-31.8,-10.6]]);steps += [('act','checkin','Check-in desk 01'),('ticket',)]
 path([[-33.0,-10.6],[-33.0,-15.7],[-35.7,-15.8]]);steps.append(('act','pickup','Physical luggage 02'))
 path([[-32.1,-15.7],[-31.8,-12.6],[-30.7,-12.6]]);steps += [('act','bagdrop','Bag drop belt 01'),('bag',)]
 path([[-32.1,-12.6],[-32.1,-8.8],[-30,-8.8],[-30,-6]]);steps.append(('exit',))
 for n in ['02_ServiceHall','03_DeskCraft','04_SelfService','05_WaitingLounge','06_Overview']:steps += [('view',n),('photo',n)]
 steps.append(('crowd',))
 S.update(i=0,checks=[],captures=[],steps=steps,start=time.monotonic(),since=time.monotonic());S['handle']=u.register_slate_post_tick_callback(tick);save()
