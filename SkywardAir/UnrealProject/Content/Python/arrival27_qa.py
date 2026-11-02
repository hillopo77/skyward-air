"""Continuous first-arrival route through check-in, bag drop, screening and boarding."""
import unreal as u,time,json,traceback,hashlib
G=None;C=None;J=None;S={}
def save(status='RUNNING',**kw):
 (G.R/'ArtBible/ArrivalQA27.json').write_text(json.dumps(dict(status=status,checks=S['checks'],captures=S['captures'],step=S['i'],elapsed_s=time.monotonic()-S['start'],continuous_walk=True,teleports=0,journey={k:G.S.get(k,False) for k in ['checked_in','bag_accepted','security','boarding','aboard']},phase=C.phase(),**kw),indent=2),encoding='utf-8')
def check(n,b,**kw):S['checks'].append(dict(name=n,passed=bool(b),**kw));save()
def stop(status,**kw):
 save(status,**kw)
 for h in [S.get('handle'),G.S.get('handle'),G.P.STATE.get('handle')]:
  if h:
   try:u.unregister_slate_post_tick_callback(h)
   except Exception:pass
 u.SystemLibrary.quit_game(G.P.STATE['world'],G.P.STATE['pc'],u.QuitPreference.QUIT,False)
def face(p):G.P.STATE['pc'].set_control_rotation(u.MathLibrary.find_look_at_rotation(G.P.STATE['pawn'].get_actor_location(),G.v(p)))
def advance():S['i']+=1;S['since']=time.monotonic();S.pop('begun',None);save()
def tick(dt):
 try:
  t=time.monotonic()-S['since'];pawn=G.P.STATE['pawn']
  if S.get('waiting'):
   p=S['waiting']
   if p.exists() and p.stat().st_mtime>=S['requested']:S['captures'].append(dict(file=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),phase=C.phase(),position=list(G.source(pawn.get_actor_location()))));S.pop('waiting');advance()
   elif t>20:raise RuntimeError('Gameplay screenshot timed out')
   return
  if S['i']>=len(S['steps']):stop('SUCCESS' if all(q['passed'] for q in S['checks']) else 'FAILED');return
  step=S['steps'][S['i']];op=step[0]
  if op=='wait':
   if t>step[1]:advance()
  elif op=='initial':
   check('Initial next-step prompt says CHECK IN',C.phase()=='CheckIn' and 'CHECK IN' in C.objective())
   check('Foyer has one departure exit',[(q['to_zone']) for q in G.D['portals'] if q['from_zone']=='entrancefoyer']==['checkin'])
   hit=u.SystemLibrary.line_trace_single(G.P.STATE['world'],G.v([-46,-10,1.62]),G.v([-46,-6,1.62]),u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[pawn],u.DrawDebugTrace.NONE,True);h=hit.to_tuple() if hit else None;check('Premature left-hand security shortcut is physically closed',bool(h and h[0] and h[9].get_actor_label()=='Clear arrival route26'))
   check('High-DPI rendering is enabled',u.SystemLibrary.get_console_variable_int_value('EnableHighDPIAwareness')==1)
   check('Short-history clarity profile is active',u.SystemLibrary.get_console_variable_int_value('r.AntiAliasingMethod')==2 and u.SystemLibrary.get_console_variable_int_value('r.TemporalAASamples')==4 and u.SystemLibrary.get_console_variable_float_value('r.TemporalAACurrentFrameWeight')>=.29)
   vp=G.P.STATE['pc'].get_viewport_size();check('Actual viewport is at least 1600x1000',vp[0]>=1600 and vp[1]>=1000,viewport=list(vp))
   check('No motion blur or depth-of-field blur',u.SystemLibrary.get_console_variable_int_value('r.MotionBlurQuality')==0 and u.SystemLibrary.get_console_variable_int_value('r.DepthOfFieldQuality')==0)
   check('Journey overlay is a native screen-space material',bool(C.S['mid'] and C.S['volume']))
   checks=[('Entrance architecture is the new modeled family','Foyer warm envelope25','SM_AP_Envelope27'),('Information cabinet is the modeled family','Foyer information and departures25','SM_AP_Information27'),('Waiting seats are the spline-modeled family','Foyer two-seat waiting bench25','SM_AP_Bench27')]
   for title,name,mesh in checks:check(title,G.S['actors'][name].static_mesh_component.static_mesh.get_name()==mesh)
   for n in ['SignStart','SignHeader','SignWelcome','FlightBoard']:
    tex=u.load_asset('/Game/Airport27/Textures/T27_'+n);check(n+' retains print detail at distance',bool(tex and tex.get_editor_property('never_stream') and tex.get_editor_property('mip_gen_settings')==u.TextureMipGenSettings.TMGS_NO_MIPMAPS))
   check('Anisotropic filtering uses sixteen samples',u.SystemLibrary.get_console_variable_int_value('r.MaxAnisotropy')==16)
   advance()
  elif op=='walk':
   point=step[1];delta=G.v(point)-pawn.get_actor_location();delta.z=0
   if delta.length()<20:pawn.get_component_by_class(u.FloatingPawnMovement).stop_movement_immediately();advance()
   elif t>16:
    check('Route remains walkable',False,goal=point,position=list(G.source(pawn.get_actor_location())));stop('FAILED');return
   else:face(point);pawn.add_movement_input(delta/max(delta.length(),.001),1.)
  elif op=='phase':
   if t<.25:return
   check('Next step updates to '+step[1],C.phase()==step[1] and C.S.get('phase')==step[1],actual=C.phase(),hud=C.S.get('phase'));advance()
  elif op=='act':
   q=next(q for q in G.S['targets'] if q['kind']==step[1] and q['actor']==step[2])
   if not S.get('begun'):face(G.source(G.point(q)));S['begun']=True;S['since']=time.monotonic();return
   if t<.25:return
   nearest=G.nearest();check('Aim selects '+q['title'],bool(nearest and nearest['actor']==q['actor'] and nearest['kind']==q['kind']),selected=nearest['actor'] if nearest else None)
   desired={'checkin':'CheckIn','pickup':'Pickup','bagdrop':'BagDrop','security':'Security','boarding':'Boarding','information':'Information','seat':'Seat'}.get(q['kind'])
   if desired:check('Interaction prompt matches '+q['kind'],C.S.get('hint')==desired,hint=C.S.get('hint'))
   if nearest and nearest['actor']==q['actor']:G.use_nearest()
   advance()
  elif op=='seated':check('Rebuilt foyer seat remains usable',bool(G.P.STATE.get('seated')));advance()
  elif op=='stand':G.P.stand();check('Standing restores eye height after rebuilt seat',not G.P.STATE.get('seated') and abs(pawn.get_actor_location().z/100-1.62)<.05);advance()
  elif op=='ticket':check('Check-in issues boarding pass before security',bool(J.S.get('ticket')) and G.S['checked_in'] and not G.S['security']);advance()
  elif op=='bag':
   if G.S.get('bag_accepted'):check('Suitcase is accepted using native belt physics',bool(J.S.get('registered_bags')) and G.S.get('held') is None);advance()
   elif t>10:check('Suitcase accepted',False,held=G.S.get('held'));stop('FAILED')
  elif op=='access':
   if t>1.2:check(step[1]+' opens after its required clearance',all(d['fraction']>.98 for n,d in G.S['doors'].items() if n.startswith(step[1])));advance()
  elif op=='security':check('Blue route reaches and clears screening',G.S['security'] and J.S['ticket']['security_cleared']);advance()
  elif op=='gate':check('Boarding pass is validated at A07',G.S['boarding'] and J.S['ticket']['gate_scanned']);advance()
  elif op=='aboard':check('Gate and bridge lead into the real aircraft',G.S['aboard'] and J.S['ticket']['aboard']);check('Standing eye height remains 1.62m',abs(pawn.get_actor_location().z/100-1.62)<.05);advance()
  elif op=='photo':
   if len(step)>2:face(step[2])
   p=G.R/'Screenshots'/(step[1]+'.png');S.update(waiting=p,requested=time.time());u.SystemLibrary.execute_console_command(G.P.STATE['world'],'Shot -nosuffix filename="'+p.as_posix()+'"',G.P.STATE['pc'])
 except Exception:stop('ERROR',error=traceback.format_exc())
def start(game,clarity):
 global G,C,J;G=game;C=clarity;import airport_journey22 as journey;J=journey
 steps=[('wait',2),('initial',)]
 def walk(*p):steps.append(('walk',[p[0],p[1],1.62]))
 def path(points):
  for p in points:walk(*p)
 def act(k,n):steps.append(('act',k,n))
 path([[-48.3,-12.5]]);steps.append(('photo','QA27_01_FirstStep',[-43.3,-14.2,1.6]))
 path([[-46,-12.5],[-46,-10.75]]);act('information','Foyer information and departures25');path([[-46,-15.9],[-47.25,-16.0]]);act('seat','Foyer two-seat waiting bench25');steps += [('seated',),('stand',)]
 path([[-46,-15],[-42,-15],[-42,-13],[-39,-13]]);act('checkin','Check-in desk 01');steps += [('ticket',),('phase','Security')]
 path([[-42,-13],[-42,-15],[-46,-15],[-45.7,-16]]);act('pickup','Physical luggage 01');steps.append(('phase','BagDrop'))
 path([[-46,-15],[-42,-15],[-42,-13],[-39,-13.4],[-37,-13.4]]);act('bagdrop','Bag drop belt 01');steps += [('bag',),('phase','Security')]
 path([[-30.6,-13.4],[-30.6,-9],[-30.6,-7.3]]);steps.append(('photo','QA27_02_NextSecurity',[-30.6,-7.8,2.8]))
 path([[-30.6,-6],[-42,-6]]);steps.append(('access','Screening entry24'));path([[-42,-3],[-45.5,-2.4],[-45.5,-1.3]]);act('security','Security portal 01');walk(-45.5,1.2);steps += [('security',),('phase','Gate')]
 path([[-45.5,3.5],[-38,3.5]]);steps.append(('access','Screening exit24'));path([[-34,3.5],[-34,1.5],[-30.5,1.5],[-30.5,4.5],[-24.5,4.5],[-24.5,.5],[-22.5,.5],[-19,.5],[-18.9,-2]])
 act('boarding','Gate A07 boarding desk');steps += [('gate',),('phase','Board'),('access','A07 boarding')]
 path([[-19,.3],[-15.4,.3],[-15.2,.675],[-13,.675],[-7,.675],[-.9,.675]]);steps += [('aboard',),('phase','Seat'),('photo','QA27_03_Aboard',[0,3,1.62])]
 S.update(start=time.monotonic(),since=time.monotonic(),i=0,checks=[],captures=[],steps=steps);S['handle']=u.register_slate_post_tick_callback(tick);save()
