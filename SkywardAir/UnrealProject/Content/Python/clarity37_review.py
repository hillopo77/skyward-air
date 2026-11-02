"""Real native photographs plus continuous walking through the changed rooms and stair."""
import unreal as u,time,json,hashlib,traceback,math
G=None;S={}
def save(status='RUNNING',**kw):
 (G.R/'ArtBible'/('QA37.json' if S['qa'] else 'Photos37.json')).write_text(json.dumps(dict(status=status,checks=S['checks'],captures=S['captures'],step=S['i'],setup_player_teleports=1 if S['qa'] else 0,walk_teleports=0,elapsed_s=time.monotonic()-S['start'],**kw),indent=2))
def check(n,b,**kw):S['checks'].append(dict(name=n,passed=bool(b),**kw));save()
def advance():S['i']+=1;S['since']=time.monotonic();S.pop('begun',None)
def stop(status,**kw):
 save(status,**kw)
 for h in [S.get('handle'),G.S.get('handle'),G.P.STATE.get('handle')]:
  if h:
   try:u.unregister_slate_post_tick_callback(h)
   except Exception:pass
 u.SystemLibrary.quit_game(G.P.STATE['world'],G.P.STATE['pc'],u.QuitPreference.QUIT,False)
def face(p):G.P.STATE['pc'].set_control_rotation(u.MathLibrary.find_look_at_rotation(G.P.STATE['pawn'].get_actor_location(),G.v(p)))
def tick(dt):
 try:
  t=time.monotonic()-S['since'];pawn=G.P.STATE['pawn'];pc=G.P.STATE['pc']
  if S.get('waiting'):
   p=S['waiting']
   if p.exists() and p.stat().st_mtime>=S['requested']:S['captures'].append(dict(file=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()));S.pop('waiting');advance()
   elif t>20:raise RuntimeError('Photo timeout')
   return
  if S['i']==len(S['steps']):stop('SUCCESS' if all(q['passed'] for q in S['checks']) else 'FAILED');return
  q=S['steps'][S['i']];op=q[0]
  if op=='wait':
   if t<q[1]:return
  elif op=='view':
   spec=next(v for v in json.loads((G.R/'Exports/Changes37.json').read_text())['views'] if v['name']==q[1]);cam=G.S['cameras'][q[1]];cam.set_actor_location(G.v(spec['eye']),False,True);cam.set_actor_rotation(u.MathLibrary.find_look_at_rotation(G.v(spec['eye']),G.v(spec['target'])),False);G.CAPTURE=True;pc.set_view_target_with_blend(cam,0)
  elif op=='photo':
   if t<.85:return
   p=G.R/'Screenshots'/(q[1]+'.png');S.update(waiting=p,requested=time.time());u.SystemLibrary.execute_console_command(G.P.STATE['world'],'Shot -nosuffix filename="'+p.as_posix()+'"',pc);return
  elif op=='setup':
   import airport_journey22 as J
   G.CAPTURE=False;pc.set_view_target_with_blend(pawn,0);G.S['checked_in']=True;G.S['bag_accepted']=True;J.ticket();pawn.set_actor_location(G.v([-42,-5.3,1.62]),False,True)
   check('Viewport is native1920x1080',tuple(pc.get_viewport_size())==(1920,1080));check('Security has7m preparation setback',G.D['flow35']['arrival_buffer_before_detectors_m']>=7)
   specs=G.S['actor_specs']
   for j in range(4):
    chair=specs['CafeChair24_'+str(1783+j*3)];table=specs[['CafeTable24_1782','CafeTable24_1785','CafeTable24_1788','CafeTable24_1791'][j]];r=math.radians(chair['rotation_degrees']);d=[table['location'][i]-chair['location'][i] for i in range(2)];check('Cafe chair faces table '+str(j),d[0]*math.sin(r)-d[1]*math.cos(r)>.7)
  elif op=='walk':
   d=G.v(q[1])-pawn.get_actor_location();d.z=0
   if d.length()<15:pawn.get_component_by_class(u.FloatingPawnMovement).stop_movement_immediately();check('Walk reaches '+str(q[1][:2]),True,eye_height=G.source(pawn.get_actor_location())[2])
   elif t>14:check('Unobstructed walk',False,goal=q[1],position=list(G.source(pawn.get_actor_location())));stop('FAILED');return
   else:face(q[1]);pawn.add_movement_input(d/max(d.length(),.001),1);return
  elif op=='furniture':
   check('Three sorting bins are available in cafe and gallery',len([t for t in G.D['instances'] if t['asset']=='SM_AP_Bins36'])>=3)
   p=next(p for p in G.D['portals'] if p['from_zone']=='recovery' and p['to_zone']=='concourse');check('Exit and next opening are aligned',p['point']==[-32,6.5] and p['width_m']>=3.2)
   plant=next(t for t in G.D['instances'] if t['name']=='Plant1224_1772');check('Plant canopy is outside the main gold route',abs(plant['location'][1]-6.5)>1.35)
   leaves=[t for t in G.D['instances'] if t['name'].startswith('Screening exit24 leaf')];check('Screening exit has two framed safety-glass leaves',len(leaves)==2 and all(t['asset']=='SM_AP_ScreeningGlass36' for t in leaves))
   for j,(start,end) in enumerate([([-31,6.5,1.6],[-18,6.5,1.6]),([-33,25,1.6],[-27,25,1.6])]):
    hit=u.SystemLibrary.line_trace_single(G.P.STATE['world'],G.v(start),G.v(end),u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[pawn],u.DrawDebugTrace.NONE,True);h=hit.to_tuple() if hit else [];component=h[10] if len(h)>10 else None;check('Solid partition blocks layered room sightline '+str(j),bool(h and h[0] and component and component.static_mesh and component.static_mesh.get_name()=='SM_AP_Walls37'))
  elif op=='seated':check('New sofa can actually be occupied',bool(G.P.STATE.get('seated')))
  elif op=='stand':G.P.stand();check('Standing from sofa restores height',not G.P.STATE.get('seated') and abs(G.source(pawn.get_actor_location())[2]-1.62)<.05)
  elif op=='height':check(q[1],abs(G.source(pawn.get_actor_location())[2]-q[2])<.10,actual=G.source(pawn.get_actor_location())[2])
  elif op=='security':check('Actual northbound screening traversal clears security',G.S['security'])
  elif op=='act':
   target=next(t for t in G.S['targets'] if t['kind']==q[1] and t['actor']==q[2])
   if not S.get('begun'):face(G.source(G.point(target)));S['begun']=True;S['since']=time.monotonic();return
   if t<.25:return
   near=G.nearest();ok=near and near['kind']==target['kind'] and near['actor']==target['actor'];check('Reach '+q[2],ok,selected=near['actor'] if near else None)
   if ok:G.use_nearest()
  elif op=='boarding':check('Boarding pass opens A07',G.S['boarding'])
  elif op=='aboard':check('Player reaches actual aircraft across bridge',G.S.get('aboard'));check('Final standing eye height preserved',abs(G.source(pawn.get_actor_location())[2]-1.62)<.05)
  advance()
 except Exception:stop('ERROR',error=traceback.format_exc())
def start(game,qa):
 global G;G=game;steps=[('wait',3)]
 for q in json.loads((G.R/'Exports/Changes37.json').read_text())['views']:steps += [('view',q['name']),('photo',q['name'])]
 if qa:
  steps += [('setup',),('furniture',),('wait',2)]
  def path(ps):steps.extend(('walk',[x,y,1.62]) for x,y in ps)
  path([[-42,-2.8],[-42,-.8],[-39.75,.5],[-39.75,1.8],[-39.75,4.5]]);steps += [('security',)]
  path([[-39.75,7.5],[-43.5,7.3],[-45.5,7.3],[-45.5,4.5],[-45.5,1.4],[-45.5,4.5],[-45.5,7.3],[-38,6.5]]);steps += [('wait',1.6)]
  path([[-34,6.5],[-29,6.5],[-29,9],[-29,12.5],[-33.5,12.5],[-34.5,15],[-34.5,18.3],[-34.5,19.4],[-40.4,19.4],[-40.4,24.2],[-40.4,28.6],[-40.4,29.8],[-46.8,29.8],[-43.2,29.8],[-43.2,18.3],[-43.2,17],[-46.5,17],[-46.5,20.5],[-46.5,21.3],[-46.5,23.6],[-46.5,25.7]])
  steps += [('height','Gallery reached by continuous walking',4.77)]
  path([[-44.3,26.5],[-44.3,29.5],[-44.3,26],[-46.5,25.7],[-46.5,23.6],[-46.5,21.3],[-46.5,20.5],[-46.5,17]])
  steps += [('height','Normal height after stair descent',1.62)]
  path([[-43.2,17],[-43.2,18.3],[-34.5,18.3],[-34.5,15],[-33.5,12.5],[-29,12.5],[-28,15.5],[-28,19.5],[-27.7,24],[-27.7,29.8],[-28,19.5],[-29,12.5],[-29,6.5],[-24.5,6.5],[-24.5,4],[-21,4],[-19.6,6],[-17.1,6],[-17.1,8]])
  steps += [('act','seat','A07 upholstered sofa36 seat 1'),('seated',),('wait',.6),('stand',)]
  path([[-17.1,6],[-19,4],[-19,.5],[-18.9,-2]])
  steps += [('act','boarding','Gate A07 boarding desk'),('boarding',),('wait',2)]
  path([[-19,.3],[-15.4,.3],[-15.2,.675],[-13,.675],[-7,.675],[-.9,.675]]);steps += [('aboard',)]
 S.update(qa=qa,i=0,checks=[],captures=[],steps=steps,start=time.monotonic(),since=time.monotonic());S['handle']=u.register_slate_post_tick_callback(tick);save()
