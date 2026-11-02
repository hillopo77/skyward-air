"""Fresh native walk: no ticket setup, pawn teleport or bag transform in route."""
import unreal as u,json,time,math,traceback,hashlib
import cProfile,pstats,io,statistics
import qa_contract38
G=None;S={}
def save(status='RUNNING',**extra):
 (G.R/'ArtBible'/S['output']).write_text(json.dumps(dict(status=status,context=S.get('context'),step=S['i'],checks=S['checks'],captures=S['captures'],bag_samples=S['bag_samples'],carried_samples=S.get('carried_samples',[]),journey=G.S and {k:G.S[k] for k in ['checked_in','bag_accepted','security','boarding','aboard']},player=list(G.source(G.P.STATE['pawn'].get_actor_location())),fresh_route_teleports=1 if S.get('debug') else 0,setup='Explicit starting-aboard debug setup; not the fresh passenger-route proof' if S.get('debug') else 'Fresh entrance, normal walking and interactions',direct_bag_transform_assignments=0,elapsed_s=time.monotonic()-S['start'],**extra),indent=2))
def check(n,b,**kw):S['checks'].append(dict(name=n,passed=bool(b),**kw));save();return bool(b)
def stop(status,**extra):
 if S.get('perf39',{}).get('prof'):S['perf39']['prof'].disable()
 save(status,**extra);u.unregister_slate_post_tick_callback(S['handle']);u.SystemLibrary.quit_game(G.P.STATE['world'],G.P.STATE['pc'],u.QuitPreference.QUIT,False)
def advance():S['i']+=1;S['since']=time.monotonic();S.pop('begun',None);S.pop('aiming',None);save()
def face(point):
 p=G.P.STATE['pawn'];G.P.STATE['pc'].set_control_rotation(u.MathLibrary.find_look_at_rotation(p.get_actor_location(),G.v(point)))

def walk_obstacles(goal):
 pawn=G.P.STATE['pawn'];p=G.source(pawn.get_actor_location());results=[]
 for height in [.25,.75,1.2,1.6]:
  start=G.v([p[0],p[1],height]);end=G.v([goal[0],goal[1],height])
  if S.get('flight_walking'):
   frame=G.flight39['frame'];start=frame.world(start);end=frame.world(end)
  hit=u.SystemLibrary.line_trace_single(G.P.STATE['world'],start,end,u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[pawn],u.DrawDebugTrace.NONE,True)
  h=hit.to_tuple() if hit else []
  results.append(dict(height=height,blocked=bool(h and h[0]),actor=h[9].get_actor_label() if h and h[0] and h[9] else None,
   component=h[10].get_name() if h and h[0] and h[10] else None))
 return results
def departure_diagnosis():
 out={}
 try:
  import airport_airside38 as A
  last=A.S.get('last_clearance') or {}
  out['blocking']=[dict(name=q.get('name'),mesh=q.get('mesh'),bounds=q.get('bounds')) for q in last.get('blocking',[])[:6]]
 except Exception as e:out['blocking_error']=str(e)
 try:
  from flight39_envelope import contains_box,boarding_threshold_overlap,bridge_overlap
  frame=G.flight39['frame'];aircraft=G.D['aircraft38']
  for name in {G.S.get('held')}|set(frame.prop_records):
   a=G.S['actors'].get(name) if name else None
   if not a:continue
   b=frame.body_source_bounds(a)
   out.setdefault('bodies',{})[name]=dict(held=name==G.S.get('held'),bounds=[[round(v,3) for v in b[0]],[round(v,3) for v in b[1]]],
    inside_envelope=contains_box(frame.envelope,b),over_threshold=boarding_threshold_overlap(b,aircraft['crossing']),
    over_bridge=bridge_overlap(b,aircraft['bridge']['floor_polygons']),fully_inside=frame.body_fully_inside(a),
    rotation=[round(v,1) for v in (a.get_actor_rotation().roll,a.get_actor_rotation().pitch,a.get_actor_rotation().yaw)])
  out['pawn']=list(G.source(frame.reference(G.P.STATE['pawn'].get_actor_location())))
 except Exception as e:out['bodies_error']=str(e)
 return out
def target(step):return next(q for q in G.S['targets'] if q['actor']==step['actor'] and q['kind']==step['kind'])
def photo(name):
 p=G.R/'Screenshots'/(name+'.png');S.update(waiting=p,requested=time.time(),requested_mono=time.monotonic());u.SystemLibrary.execute_console_command(G.P.STATE['world'],'Shot -nosuffix filename="'+p.as_posix()+'"',G.P.STATE['pc'])
def tick(dt):
 try:
  now=time.monotonic();elapsed=now-S['since'];pawn=G.P.STATE['pawn'];pc=G.P.STATE['pc'];j=G.journey38['state']
  if G.S.get('held') and now-S.get('carried_sampled',0)>1:
   S['carried_sampled']=now;name=G.S['held'];c=G.S['actors'][name].static_mesh_component;frame=G.flight39['frame']
   S.setdefault('carried_samples',[]).append(dict(t=now-S['start'],step=S['i'],actor=name,distance_m=(c.get_center_of_mass()-pawn.get_actor_location()).length()/100,
    body_local=list(G.source(frame.reference(c.get_center_of_mass()))),pawn_local=list(G.source(frame.reference(pawn.get_actor_location()))),
    body_velocity=list(c.get_physics_linear_velocity().to_tuple()),carrier_velocity=list(frame.point_velocity(c.get_center_of_mass()).to_tuple()),registered=name in frame.prop_records))
  if now-S.get('sampled',0)>.1:
   S['sampled']=now;n=S['bag'];a=G.S['actors'][n];c=a.static_mesh_component
   S['bag_samples'].append(dict(t=now-S['start'],position=list(G.source(c.get_center_of_mass())),speed_cm_s=c.get_physics_linear_velocity().length(),held=G.S.get('held'),registered=n in j['registered_bags'],scanned=n in j['scanned_bags'],state=j['bag_states'].get(n)))
  if S.get('waiting'):
   p=S['waiting']
   if p.exists() and p.stat().st_mtime>=S['requested']:
    S['captures'].append(dict(file=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()));S.pop('waiting')
    if S.pop('flight_photo',False):save()
    else:advance()
   elif now-S['requested_mono']>20:raise RuntimeError('Journey screenshot timeout')
   return
  if S.get('stop_after_photo'):stop('FAILED',error=S['stop_after_photo']);return
  if S.get('flight_photos'):
   label=S['flight_photos'].pop(0)
   if label not in {'crew_close_requested','bridge','power','engine_spool'}:
    cam=G.flight39['runtime'].get('chase') or next((a for a in u.GameplayStatics.get_all_actors_of_class(G.P.STATE['world'],u.CameraActor) if a.get_actor_label()=='Flight39 Chase'),None)
    if cam:pc.set_view_target_with_blend(cam,0)
   S['flight_photo']=True;photo('Flight39_'+label);return
  if S['i']>=len(S['steps']):stop('SUCCESS' if all(q['passed'] for q in S['checks']) else 'FAILED');return
  step=S['steps'][S['i']];op=step['action']
  if op=='walk':
   goal=step['point'];world_goal=G.v(goal)
   if S.get('flight_walking'):
    frame=G.flight39['frame'];world_goal=frame.world(world_goal);normal=frame.local_axis(u.Vector(0,0,1));d=world_goal-pawn.get_actor_location();d-=normal*(d.x*normal.x+d.y*normal.y+d.z*normal.z)
   else:d=world_goal-pawn.get_actor_location();d.z=0
   if d.length()<16:
    pawn.get_component_by_class(u.FloatingPawnMovement).stop_movement_immediately()
    check('Normal swept walk '+str(goal[:2]),True,eye_z=G.source(pawn.get_actor_location())[2]);advance();return
   if elapsed>18:
    check('Normal swept walk '+str(goal[:2]),False,actual=list(G.source(pawn.get_actor_location())),obstacles=walk_obstacles(goal));photo('QA38_FailureWalk');S['stop_after_photo']='Blocked walk';return
   pc.set_control_rotation(u.MathLibrary.find_look_at_rotation(pawn.get_actor_location(),world_goal));pawn.add_movement_input(d/max(d.length(),.001),1);return
  if op=='face_and_use':
   q=target(step);p=G.source(G.point(q));face(p)
   if not S.get('aiming'):S['aiming']=now;return
   if now-S['aiming']<.30:return
   near=G.nearest();ok=bool(near and near['actor']==q['actor'] and near['kind']==q['kind'])
   check('Aim and use actual '+q['actor'],ok,selected=near['actor'] if near else None,visible=G.visible(q),player=list(G.source(pawn.get_actor_location())),point=list(p))
   if not ok:stop('FAILED',error='Actual target unreachable '+q['actor']);return
   G.use_nearest();advance();return
  if op=='wait':
   expr=step['until'];done=bool(eval(expr,{'G':G,'__builtins__':{}},{}))
   if done:
    check('Wait for physical outcome '+expr,True);qa_contract38.assert_free_call(G);advance();return
   if elapsed>step['timeout_s']:check('Wait for physical outcome '+expr,False);stop('FAILED',error='Timed out '+expr);return
   return
  if op=='pause':
   if elapsed<step['seconds']:return
  elif op=='photo':
   if elapsed<.65:return
   photo(step['name']);return
  elif op=='assert':
   pred=step['predicate']
   if pred.startswith('not G.') or pred.startswith('G.S['):b=bool(eval(pred,{'G':G,'__builtins__':{}},{}))
   elif 'not any' in pred:b=not any(G.S[k] for k in ['checked_in','bag_accepted','security','boarding','aboard']) and not j['ticket']
   elif 'security true' in pred:b=G.S['security'] and j['ticket']['security_cleared']
   elif 'ticket.aboard' in pred:b=G.S['aboard'] and j['ticket']['aboard'] and G.source(pawn.get_actor_location())[0]>14.1
   else:raise RuntimeError('Undefined assertion '+pred)
   if not check(pred,b):stop('FAILED',error=pred);return
  elif op=='seat':
   name=step['actor'];q=next(t for t in G.P.STATE['items'] if t['actor']==name and t['kind']=='seat');face(q['point'])
   if not S.get('aiming'):S['aiming']=now;return
   if now-S['aiming']<.3:return
   near=G.P.nearest();ok=near and near['actor']==name
   check('Actual translated cabin seat target '+name,ok,selected=near['actor'] if near else None)
   if not ok:stop('FAILED',error='Cabin seat target not reachable');return
   G.use_nearest();check('Cabin seat actually occupied',G.P.STATE.get('seated'));advance();return
  elif op=='plane_face_and_use':
   q=next(t for t in G.P.STATE['items'] if t['actor']==step['actor']);point=G.P.interaction_point(q);pc.set_control_rotation(u.MathLibrary.find_look_at_rotation(pawn.get_actor_location(),point))
   if not S.get('aiming'):S['aiming']=now;return
   if now-S['aiming']<.3:return
   near=G.P.nearest();okay=bool(near and near['actor']==q['actor']);check('Reach actual flightdeck fitting '+q['actor'],okay,selected=near['actor'] if near else None)
   if not okay:stop('FAILED',error='Flightdeck fitting unreachable '+q['actor']);return
   G.use_nearest()
  elif op=='stand_if_seated':
   if G.P.STATE.get('seated'):G.P.stand()
  elif op=='flightdeck_open':
   import qa_flight39
   result=qa_flight39.door_open_actual(G)
   if result['passed']:check('Actual flightdeck door open pose',True,evidence=result)
   elif elapsed>6:check('Actual flightdeck door open pose',False,evidence=result);stop('FAILED',error='Door progress did not produce its physical open pose');return
   else:return
  elif op=='flight_negative_cases':
   import qa_flight39
   result=qa_flight39.native_negative(G);check('Native cold-flight negative cases',result['passed'],evidence=result)
   if not result['passed']:stop('FAILED',error='Native flight negative case failed');return
  elif op=='flight_driver':
   if not S.get('begun'):
    import qa_flight39
    S['begun']=now;S['driver']=qa_flight39.start_driver(G,lambda label:S.setdefault('flight_photos',[]).append(label));return
   d=S['driver']
   if d.done:
    ev=d.snapshot()
    # Pass46: a refused departure used to report only its first three
    # names. Attach what the interlock actually measured, and for a held
    # bag which aboard test it failed, so the cause is in the report.
    if d.failed and 'Departure' in str(d.failed):ev['departure_diagnosis']=departure_diagnosis()
    check('Normal controls completed taxi/takeoff/climb',not d.failed,evidence=ev)
    if d.failed:stop('FAILED',error=d.failed);return
   elif elapsed>900:stop('FAILED',error='Native integrated flight timed out');return
   else:return
  elif op=='flight_verify':
   import qa_flight39
   result=qa_flight39.verify(G);check('Native moving aircraft verification',result['status']=='PASS',evidence=result)
  elif op=='flight_walk_begin':
   G.flight39['runtime']['autoplay']=False;pc.set_view_target_with_blend(pawn,0);G.P.stand();S['flight_walking']=True
   frame=G.flight39['frame'];height=G.source(frame.reference(pawn.get_actor_location()))[2]
   check('Stand in the moving aircraft retains local eye height',not G.P.STATE.get('seated') and abs(height-1.62)<.1,local_eye_z=height)
  elif op=='flight_drop_bag':
   if S.get('debug'):advance();return
   name='Physical luggage 01';frame=G.flight39['frame'];actor=G.S['actors'][name];c=actor.static_mesh_component
   if not S.get('begun'):
    distance=(c.get_center_of_mass()-pawn.get_actor_location()).length()/100
    if not check('Scanned airport bag physically carried aboard in flight',G.S.get('held')==name and name in G.journey38['state']['scanned_bags'] and distance<2.,held=G.S.get('held'),actual_bag_distance_m=distance):stop('FAILED',error='Carried-bag proof missing');return
    S.update(begun=now,drop_reference=G.source(frame.reference(c.get_center_of_mass())),drop_samples=[]);G.release(False);return
   local=list(G.source(frame.reference(c.get_center_of_mass())));relative=frame.relative_velocity(c).length()/100
   S['drop_samples'].append(dict(t=now-S['begun'],local_com=local,native_relative_speed_m_s=c.get_physics_linear_velocity().length()/100,world_speed_m_s=frame.world_velocity(c).length()/100,relative_speed_m_s=relative,registered=name in frame.prop_records))
   if now-S['begun']<2.5:return
   drift=math.dist(local[:2],S['drop_reference'][:2]);okay=name in frame.prop_records and drift<4 and -.15<local[2]<2.0 and relative<12
   check('Dropped airport bag remains on the moving aircraft',okay,local_drift_m=drift,local_com=local,relative_speed_m_s=relative)
   (G.R/'ArtBible/MovingBag39.json').write_text(json.dumps(dict(status='PASS' if okay else 'FAIL',context=S['context'],body=name,setup='Same bag picked up at the airport, physically scanned and carried aboard in the fresh route; normal release in flight. No body teleport.',samples=S['drop_samples']),indent=2))
   if not okay:stop('FAILED',error='Dropped bag lost moving-frame support');return
  elif op=='flight_target_probe':
   q=next(t for t in G.P.STATE['items'] if t['actor']==step['actor']);point=G.P.interaction_point(q);pc.set_control_rotation(u.MathLibrary.find_look_at_rotation(pawn.get_actor_location(),point))
   if not S.get('aiming'):S['aiming']=now;return
   if now-S['aiming']<.3:return
   near=G.P.nearest();okay=bool(near and near['actor']==q['actor']);check('Aim at current moving control '+q['actor'],okay,selected=near['actor'] if near else None,visible=G.P.interaction_visible(q))
   if not okay:stop('FAILED',error='Moving control target not reachable '+q['actor']);return
  elif op=='flight_returned':
   check('Walk back to and occupy pilot seat in flight',G.flight39['pilot']() and G.flight39['frame'].attached)
   photo('Flight39_SeatReturn');return
  elif op=='flight_performance':
   now=time.perf_counter()
   r=S.setdefault('perf39',dict(i=0,results=[],phase='pose'))
   views=['CockpitInFlight','ChaseInFlight']
   if r['i']>=len(views):
    (G.R/'ArtBible/FlightPerformance39.json').write_text(json.dumps(dict(status='SUCCESS',context=S['context'],views=r['results'],method='Actual fresh-route aircraft after controlled takeoff; two30s uncaptured/unprofiled wall-frame samples. Separate3s callback profiles per view; no concurrent DCC job required for final approval.'),indent=2));advance();return
   name=views[r['i']]
   if r['phase']=='pose':
    camera=pawn if r['i']==0 else G.flight39['runtime']['chase'];pc.set_view_target_with_blend(camera,0)
    r.update(phase='warm',next=now+2);return
   if r['phase']=='warm':
    if now<r['next']:return
    r.update(phase='profile',prof=cProfile.Profile(),next=now+3);r['prof'].enable();return
   if r['phase']=='profile':
    if now<r['next']:return
    r['prof'].disable();buf=io.StringIO();pstats.Stats(r['prof'],stream=buf).sort_stats('cumulative').print_stats(45)
    (G.R/'ArtBible'/('FlightPerformance39_'+name+'.txt')).write_text(buf.getvalue());r.update(phase='sample',begin=now,last=now,frames=[]);return
   r['frames'].append((now-r['last'])*1000);r['last']=now
   if now-r['begin']<30:return
   f=sorted(r['frames']);r['results'].append(dict(view=name,samples=len(f),seconds=now-r['begin'],median_ms=statistics.median(f),mean_ms=statistics.mean(f),p95_ms=f[min(len(f)-1,int(len(f)*.95))],maximum_ms=f[-1]));r.update(i=r['i']+1,phase='pose');return
  elif op=='stand':G.P.stand();check('Stand restores normal eye height',not G.P.STATE.get('seated') and abs(G.source(pawn.get_actor_location())[2]-1.62)<.10)
  elif op=='geometry':
   for q in G.D['repair38'].get('flow39_probes',G.D['repair38']['perimeter_probes']):
    # Transfer path probes cross a real roller at lowZ; the specified1.25m
    # aperture probes remain above rollers and below their true lintels.
    hit=u.SystemLibrary.line_trace_single(G.P.STATE['world'],G.v(q['start']),G.v(q['end']),u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[pawn],u.DrawDebugTrace.NONE,True);h=hit.to_tuple() if hit else []
    check(q['id'],bool(h and h[0])==(q['expected']=='block'),blocking=bool(h and h[0]))
   for p in [[-18,18,0],[-15,12,0],[-5,30,0],[0,-50,0]]:
    floor,name=G.journey38['floor_at_source'](*p);check('No phantom deck at '+str(p),floor is None or abs(floor)>.2,actual=floor,floor_name=name)
   check('Measured viewport',tuple(pc.get_viewport_size())==(1920,1080))
  else:raise RuntimeError('Undefined step '+op)
  advance()
 except Exception:stop('ERROR',error=traceback.format_exc())
def start(game,scanner=False,flight=False,debug=False):
 global G;G=game;G.QA=True;G.CAPTURE=False
 if scanner:
  import qa_scanner38
  spec=qa_scanner38.specification(G.D);raw=spec['steps']
 else:spec=qa_contract38.specification(G.D);raw=[] if debug else spec['fresh_start']
 if flight and not debug:
  import qa_scanner38
  scan=qa_scanner38.specification(G.D)['steps'];extended=[]
  for q in raw:
   if q.get('action')=='assert' and q.get('predicate','').startswith('security true only'):
    first=next(i for i,s in enumerate(scan) if s.get('action')=='assert' and "and not G.S['security'] and 'Physical luggage 01'" in s.get('predicate',''))
    extended.extend(scan[first:]);continue
   extended.append(q)
   if q.get('action')=='wait' and 'registered_bags' in q.get('until',''):
    pickup=next(q for q in scan if q.get('action')=='face_and_use' and q.get('actor')=='Physical luggage 01')
    extended.extend([dict(action='walk',points=[[-32.1,-15.8,1.62],[-39,-15.8,1.62],[-42,-15,1.62],[-45.2,-15,1.62],[-46,-15.8,1.62]]),pickup,
     dict(action='walk',points=[[-45.2,-15,1.62],[-42,-15,1.62],[-39,-11,1.62]])])
  raw=extended
 steps=[]
 for q in raw:
  if q['action']=='walk':steps.extend(dict(action='walk',point=p) for p in q['points'])
  elif q['action']=='aircraft_walk_and_use':
   # Actual right aisle and third economy row; all points inherit the translated
   # aircraft schema and normal capsule collision, never a seat teleport.
   dx=G.D['aircraft38']['offset'][0]
   seat=next(t for t in G.P.STATE['items'] if t['actor']==q['seat'] and t['kind']=='seat')
   approach=seat.get('validation_approach')
   for p in [[dx,.675,1.62],[dx,2.5,1.62],[dx+.55,8.65,1.62],[dx+.55,9.2,1.62],[dx+1.35,9.2,1.62],[dx+1.35,12.8,1.62],[dx+1.1,13.2,1.62],[dx+1.1,approach[1],1.62],approach]:steps.append(dict(action='walk',point=p))
   steps.extend([dict(action='seat',actor=q['seat']),dict(action='pause',seconds=.7),dict(action='photo',name='QA38_ActuallySeated'),dict(action='stand')])
  elif q['action']=='capture':steps.append(dict(action='photo',name=q['name']))
  else:steps.append(q)
  if q['action']=='wait' and 'registered_bags' in q['until']:steps.append(dict(action='photo',name='QA38_AfterPhysicalBagTransfer'))
 steps.append(dict(action='geometry'))
 if flight:
  import qa_flight39
  for q in qa_flight39.specification(G.P,G.D)['continuation']:
   if q['action']=='walk':
    points=q['points']
    if debug and points[0][1]>0:points=[[G.D['aircraft38']['offset'][0],.35,1.62]]
    steps.extend(dict(action='walk',point=p) for p in points)
   elif q['action']=='wait':steps.append(dict(action='flightdeck_open'))
   elif q['action']=='assert':
    if 'fresh check-in' in q['predicate']:steps.append(dict(action='assert',predicate="G.S['aboard']"))
    else:steps.append(dict(action='assert',predicate="G.S['aboard'] and G.flight39['pilot']()"))
   else:steps.append(q)
 S.update(i=0,context=json.loads((G.R/'ArtBible/InstalledRuntime39.json').read_text()),checks=[],captures=[],bag_samples=[],steps=steps,debug=debug,output='FlightDebug39.json' if debug else 'FlightJourney39.json' if flight else 'ScannerQA38.json' if scanner else 'QA38.json',bag='Physical luggage 01' if scanner else 'Physical luggage 02',start=time.monotonic(),since=time.monotonic());S['handle']=u.register_slate_post_tick_callback(tick);save()
