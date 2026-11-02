"""Native terminal/exterior photographs and a focused real seating check."""
import unreal as u,time,json,hashlib,traceback
G=None;S={}
def save(status='RUNNING',**kw):
 (G.R/'ArtBible/FinalPhotos34.json').write_text(json.dumps(dict(status=status,checks=S['checks'],captures=S['captures'],step=S['i'],elapsed_s=time.monotonic()-S['start'],viewport=list(G.P.STATE['pc'].get_viewport_size()),setup_player_teleports=1,route_proof='RouteProof34.json',**kw),indent=2))
def check(n,b,**kw):S['checks'].append(dict(name=n,passed=bool(b),**kw))
def stop(status,**kw):
 save(status,**kw)
 for h in [S.get('handle'),G.S.get('handle'),G.P.STATE.get('handle')]:
  if h:
   try:u.unregister_slate_post_tick_callback(h)
   except Exception:pass
 u.SystemLibrary.quit_game(G.P.STATE['world'],G.P.STATE['pc'],u.QuitPreference.QUIT,False)
def tick(dt):
 try:
  t=time.monotonic()-S['since'];pc=G.P.STATE['pc'];world=G.P.STATE['world']
  if S.get('waiting'):
   p=S['waiting']
   if p.exists() and p.stat().st_mtime>=S['requested']:S['captures'].append(dict(file=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),view=S['name']));S.pop('waiting');S['i']+=1;S['since']=time.monotonic();save()
   elif t>20:raise RuntimeError('Screenshot timeout')
   return
  if S['i']>=len(S['steps']):stop('SUCCESS' if all(q['passed'] for q in S['checks']) else 'FAILED');return
  q=S['steps'][S['i']];op=q[0]
  if op=='wait':
   if t<q[1]:return
  elif op=='check':
   check('Native viewport1920x1080',tuple(pc.get_viewport_size())==(1920,1080));check('Remodeled benches offer unoccupied seats',any(q['kind']=='seat' and q.get('asset')=='SM_AP_Bench34' for q in G.S['targets']));check('GateA08 has its own display identity',G.S['actor_specs']['Gate A08 flight display'].get('ui')=='GateA08')
  elif op=='seat_setup':
   people=[q['location'] for q in G.D['character_placements']];candidates=[q for q in G.S['targets'] if q['kind']=='seat' and q.get('mesh_actor','').startswith('A07 lounge bench24')];q=max(candidates,key=lambda q:min((q['point'][0]-p[0])**2+(q['point'][1]-p[1])**2 for p in people));S['seat']=q;eye=q['eye'];pos=[eye[0]+q['facing'][0]*1.25,eye[1]+q['facing'][1]*1.25,1.62];G.P.STATE['pawn'].set_actor_location(G.v(pos),False,True);pc.set_control_rotation(u.MathLibrary.find_look_at_rotation(G.v(pos),G.v(q['point'])))
  elif op=='seat_use':
   q=G.nearest();ok=q and q['kind']=='seat';check('Crosshair reaches a remodeled empty seat',ok,selected=q['actor'] if q else None)
   if ok:G.use_nearest()
   check('Player actually sits in remodeled seating',bool(G.P.STATE.get('seated')))
  elif op=='stand':
   G.P.stand();check('Standing restores full eye height',not G.P.STATE.get('seated') and abs(G.P.STATE['pawn'].get_actor_location().z/100-1.62)<.05)
  elif op=='view':
   view=next(v for v in json.loads((G.R/'Exports/Changes34.json').read_text())['views'] if v['name']==q[1]);cam=G.S['cameras'].get(q[1]) or G.S['cameras']['16_Runway'];cam.set_actor_location(G.v(view['eye']),False,True);cam.set_actor_rotation(u.MathLibrary.find_look_at_rotation(G.v(view['eye']),G.v(view['target'])),False);cam.camera_component.set_field_of_view(view['fov']);G.CAPTURE=True;pc.set_view_target_with_blend(cam,0)
  elif op=='lamps':
   if q[1]==False:
    S['off']=[(a,a.light_component.get_editor_property('intensity')) for a in u.GameplayStatics.get_all_actors_of_class(world,u.RectLight) if -4300<a.get_actor_location().x<-2600 and 800<a.get_actor_location().y<1800]
    for a,n in S['off']:a.light_component.set_intensity(0.)
    check('Matched diagnostic disables physical check-in emitters',len(S['off'])>=11)
   else:
    for a,n in S['off']:a.light_component.set_intensity(n)
    check('Lamp intensities restored',all(abs(a.light_component.get_editor_property('intensity')-n)<.01 for a,n in S['off']))
  elif op=='photo':
   if t<1.2:return
   p=G.R/'Screenshots'/(q[1]+'.png');S.update(waiting=p,requested=time.time(),name=q[1]);u.SystemLibrary.execute_console_command(world,'Shot -nosuffix filename="'+p.as_posix()+'"',pc);return
  S['i']+=1;S['since']=time.monotonic();save()
 except Exception:stop('ERROR',error=traceback.format_exc())
def start(game):
 global G;G=game;steps=[('wait',3),('check',),('seat_setup',),('wait',.5),('seat_use',),('wait',.5),('stand',)]
 for q in json.loads((G.R/'Exports/Changes34.json').read_text())['views']:steps += [('view',q['name']),('photo',q['name'])]
 S.update(i=0,checks=[],captures=[],steps=steps,start=time.monotonic(),since=time.monotonic());S['handle']=u.register_slate_post_tick_callback(tick);save()
