"""Native scene photographs and repeatable stationary/moving evidence."""
import unreal as u,json,time,hashlib,traceback
G=None;S={}
V=[
 ('01_Entrance',[-46.8,-13,1.62],[-43.2,-15,1.6]),
 ('02_Checkin',[-40,-14,1.62],[-29,-14,1.4]),
 ('03_BagDrop01',[-31.2,-13,1.62],[-26.15,-13,1.1]),
 ('04_BagDrop02',[-30,-17.4,1.62],[-26.2,-16,1]),
 ('05_SecurityEntry',[-44,-6.4,1.62],[-42,-2.9,1.6]),
 ('06_WestEntryGap',[-47.3,-5.4,1.62],[-49,-4.2,1.3]),
 ('07_Curtain',[-43.15,.8,1.45],[-43.15,1.92,1.3]),
 ('08_ScannerControl',[-41.5,.95,1.25],[-42.52,2.05,.97]),
 ('09_ScannerMonitor',[-41,1.3,1.62],[-41.95,2.32,1.55]),
 ('10_StaffDoor',[-45.9,7.3,1.62],[-46,10,1.8]),
 ('11_StaffStorage',[-45.7,12.7,1.62],[-48.2,12.5,1.2]),
 ('12_Repacking',[-35.3,5.7,1.62],[-33.2,1.8,1.2]),
 ('13_Concourse',[-30,6.6,1.62],[-30,10,1.7]),
 ('14_A08Marker',[-29,10.8,1.62],[-29,14,2.8]),
 ('15_A08Arrival',[-29,15.2,1.62],[-29,22,1.6]),
 ('16_A08Ceiling',[-28,13.5,1.7],[-28,16.0,3.4]),
 ('17_A08Interior',[-28,19,1.62],[-28,30,1.5]),
 ('18_WCSign',[-28.2,-2.2,1.62],[-26.2,-3,1.9]),
 ('19_WCLobby',[-24.5,-8.5,1.62],[-19,-9.5,1.3]),
 ('20_WCEastGap',[-16.1,-5.5,1.62],[-13.5,-3.9,1.4]),
 ('21_WCInterior',[-17,-6,1.62],[-17.1,-4.2,1]),
 ('22_Arrivals',[-20,-20,1.62],[-18,-16,1.2]),
 ('23_Cafe',[-34.2,18.2,1.62],[-41.3,26,1.6]),
 ('24_CafeService',[-43.2,29,1.62],[-46.5,31.4,1.3]),
 ('25_Gallery',[-45.6,25.7,4.77],[-44,31,4.5]),
 ('26_A07Desks',[-20,1.8,1.62],[-14,.675,1.3]),
 ('27_DeskClearance',[-20,-.6,1.62],[-17.5,-1.15,1]),
 ('28_BridgeInside',[-10.5,.025,1.62],[-2,-3.4,1.6]),
 ('29_DockingJoin',[12.4,.675,1.62],[15.7,.675,1.5]),
 ('30_BridgeWing',[-9,18,8],[7,2,0]),
 ('31_FormerServiceRamp',[-20,16.2,4],[-16.8,20,-2]),
 ('32_Exterior',[45,-35,18],[-8,7,1]),
 ('36_BaggageBay',[-23.0,-17.65,1.62],[-25,-13.7,1.15]),
 ('37_BaggageReceiver',[-23.0,-14.5,1.62],[-25.5,-13,1.1]),
 ('38_Forecourt',[-57,-15,1.7],[-48,-12.5,1.7]),
 ('39_Cockpit',[16,-1.52,1.76],[16,-4,1.5]),
 ('40_Cabin',[15.6,2.5,1.65],[16,10,1.4]),
]
def save(status='RUNNING',**kw):
 (G.R/'ArtBible'/S.get('output','Photos38.json')).write_text(json.dumps(dict(status=status,context=S.get('context'),step=S['i'],captures=S['captures'],samples=S['samples'],traces=S.get('traces',[]),**kw),indent=2))
def stop(status,**kw):
 save(status,**kw);u.unregister_slate_post_tick_callback(S['handle']);u.SystemLibrary.quit_game(G.P.STATE['world'],G.P.STATE['pc'],u.QuitPreference.QUIT,False)
def tick(dt):
 try:
  cam=S['cam'];pc=G.P.STATE['pc'];now=time.monotonic()
  if now<S['next']:return
  if S.get('wait'):
   p=S['wait']
   if p.exists() and p.stat().st_mtime>=S['requested']:
    S['captures'].append(dict(name=S['steps'][S['i']][0],file=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),kind='native',staged_camera=True));S.pop('wait');S['i']+=1;save()
   elif now-S['requested_mono']>20:raise RuntimeError('Native frame timeout')
   return
  if S['i']>=len(S['steps']):
   traces=[]
   for q in G.D['repair38'].get('flow39_probes',G.D['repair38']['perimeter_probes']):
    hit=u.SystemLibrary.line_trace_single(G.P.STATE['world'],G.v(q['start']),G.v(q['end']),u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[G.P.STATE['pawn']],u.DrawDebugTrace.NONE,True)
    h=hit.to_tuple() if hit else [];c=h[10] if len(h)>10 else None
    blocking=bool(h and h[0]);traces.append(dict(q,blocking=blocking,passed=blocking==(q['expected']=='block'),mesh=c.static_mesh.get_name() if c and c.static_mesh else None))
   S['traces']=traces;stop('SUCCESS' if all(q['passed'] for q in traces) else 'FAILED');return
  name,eye,target=S['steps'][S['i']]
  # Hold sequences use identical transforms without a camera reset between
  # frames. The renderer continues running; these are genuine game captures.
  pose=(eye,target)
  if S.get('pose')!=pose:
   cam.set_actor_location(G.v(eye),False,True);cam.set_actor_rotation(u.MathLibrary.find_look_at_rotation(G.v(eye),G.v(target)),False);S['pose']=pose;S['next']=now+.6
   if name.endswith('WindowClosed'):
    G.P.STATE['movables']['Window shade 20 L18']['target']=0.;S['next']=now+1.5
   elif name.endswith('WindowOpen'):
    G.P.STATE['movables']['Window shade 20 L18']['target']=1.;S['next']=now+1.5
   if name=='54_PlayerCharacter' or '_PlayerLOD' in name:
    import characters12_runtime as C
    pawn=G.P.STATE['pawn']
    if not S.get('avatar_capture_restore'):S['avatar_capture_restore']=(pawn.get_actor_location(),pc.get_control_rotation(),C.S['third'])
    pawn.set_actor_location(G.v([-53,-12.5,1.62]),False,True);pc.set_control_rotation(u.Rotator(yaw=0));C.S['third']=True;G.S['show_avatar_in_capture']=True;S['next']=now+1
    forced=1 if name.endswith('LOD0') else 2 if name.endswith('LOD1') else 4 if name.endswith('LOD3') else 0
    C.S['avatar'].skeletal_mesh_component.set_forced_lod(forced)
   elif S.get('avatar_capture_restore'):
    import characters12_runtime as C
    p,r,third=S.pop('avatar_capture_restore');G.P.STATE['pawn'].set_actor_location(p,False,True);pc.set_control_rotation(r);C.S['third']=third;G.S['show_avatar_in_capture']=False;C.S['avatar'].skeletal_mesh_component.set_forced_lod(0)
   return
  sample={}
  for n,a in G.S['actors'].items():
   if n in ['X-ray scanner 01','X-ray scanner 02'] or n.startswith('Physical luggage'):
    c=a.static_mesh_component;sample[n]=dict(position=list(G.source(c.get_world_location())),speed=c.get_physics_linear_velocity().length()/100)
  S['samples'].append(dict(time=now-S['begun'],view=name,objects=sample))
  p=G.R/'Screenshots'/(name+'.png');S.update(wait=p,requested=time.time(),requested_mono=now,next=now+.6)
  u.SystemLibrary.execute_console_command(G.P.STATE['world'],'Shot -nosuffix filename="'+p.as_posix()+'"',pc)
 except Exception:stop('ERROR',error=traceback.format_exc())
def start(game,qa=False,mount=False,assembly=False,details=False,postures=False):
 global G;G=game
 if qa:
  import journey38_review
  journey38_review.start(G);return
 (G.R/'Screenshots').mkdir(parents=True,exist_ok=True);G.CAPTURE=True
 import exterior_native_probe39
 exterior_native_probe39.apply(G)
 cam=next(iter(G.S['cameras'].values()));cam.camera_component.set_field_of_view(78);G.P.STATE['pc'].set_view_target_with_blend(cam,0)
 steps=list(V)
 if details:
  steps=[('53_SecurityGuard',[-47.5,-2.2,1.35],[-47,-.4,.95]),
   ('54_PlayerCharacter',[-50.4,-12.5,1.35],[-53,-12.5,1.0]),
   ('60_WindowClosed',[15,14.608,1.6],[13.73,14.608,1.6]),
   ('61_WindowOpen',[15.001,14.608,1.6],[13.73,14.608,1.6]),
   ('78_ExteriorWindowClosed',[9.5,14.608,2.2],[13.73,14.608,1.6]),
   ('79_ExteriorWindowOpen',[9.501,14.608,2.2],[13.73,14.608,1.6]),
   ('84_WindowTopSeated',[15.0,14.55,1.22],[13.73,14.62,1.84]),
   ('85_WindowCornerClose',[14.65,14.15,1.55],[13.72,14.33,1.9]),
   ('86_CassetteRackJoin',[14.8,14.608,1.75],[13.8,14.608,2.05]),
   ('87_WindowExteriorCorners',[11.6,14.0,1.7],[13.5,14.608,1.7]),
   ('88_WindowOpenAisle',[16.25,13.1,1.45],[13.7,14.4,1.7]),
   ('80_PlayerLOD0',[-50.4,-12.5,1.35],[-53,-12.5,1.0]),
   ('81_PlayerLOD1',[-50.401,-12.5,1.35],[-53,-12.5,1.0]),
   ('82_PlayerLOD3',[-50.402,-12.5,1.35],[-53,-12.5,1.0]),
   ('83_EndCharacterPreview',[-45.7,-3.1,1.62],[-45.7,-1.43,1.18])]
 elif assembly:
  steps=[q for q in V if q[0][:2] in ['02','03','08','09','17','19','23','24','26','28','29','30','32','39','40']]
  steps += [('48_GlassClose',[-17.4,5.7,1.62],[-14,8,1.5]),('49_GearContact',[24,-7,-2.2],[16,6,-3.3]),('50_VanityRebuilt',[-18.7,-8.9,1.62],[-18.7,-11.2,.8]),('51_TravelShelves',[-45,30.3,4.77],[-45,33.6,4.3]),('52_NoseContour',[24,-16,3.2],[16,-6.8,.8])]
 elif mount:
  steps=[('44_PreparationRearMounted',[-42.174,-.40,1.62],[-45.7,-1.43,1.20]),('45_PreparationFrontMounted',[-45.7,-3.1,1.62],[-45.7,-1.43,1.18]),('46_PreparationSideMounted',[-43.6,-1.6,1.4],[-45.7,-1.43,1.16]),('47_CeilingSoftFill',[-28,13.5,1.7],[-28,16,3.4])]
 else:
  steps += [('44_PreparationRearMounted',[-42.174,-.40,1.62],[-45.7,-1.43,1.20]),
   ('48_GlassClose',[-18.5,10.5,1.6],[-13.8,13.0,1.6]),
   ('49_GearContact',[24,-7,-2.2],[16,6,-3.3]),('50_VanityRebuilt',[-18.7,-8.9,1.62],[-18.7,-11.2,.8]),
   ('51_TravelShelves',[-45,30.3,4.77],[-45,33.6,4.3]),('52_NoseContour',[24,-16,3.2],[16,-6.8,.8]),
   ('53_SecurityGuard',[-45.7,-2.0,1.6],[-47,-.4,1.1]),
   ('54_PlayerCharacter',[-50.4,-12.5,1.4],[-53,-12.5,1.1]),
   ('55_SeatedCharacter',[-19.0,6.5,1.45],[-21.7,6.46,1.1]),
   ('56_CafeCharacter',[-36.9,21.0,1.45],[-38.5,22.35,.85]),
   ('57_GateCrew',[-18.5,-1.15,1.5],[-16.25,-1.15,1.1]),
   ('58_CabinCharacter',[16.5,13.1,1.4],[14.13,14.175,1.05]),
   ('59_BusinessCharacter',[16,6.8,1.6],[14.48,7.8,1.1]),
   ('60_WindowClosed',[15,14.608,1.6],[13.73,14.608,1.6]),
   ('61_WindowOpen',[15.001,14.608,1.6],[13.73,14.608,1.6])]
  camera_names=['CAM_Plane_Service12_Mid','CAM_Plane_Service12_Ovens','CAM_Plane_Service12_Rear',
   'CAM_Plane_Service12_Phone','CAM_Plane_LavatoryEquipment12','CAM_Plane_SuiteDoorDetail11',
   'CAM_Plane_CrewServices11','CAM_Plane_CargoStairs10','CAM_Plane_CargoOverview15','CAM_Plane_CargoMixed15',
   'CAM_Plane_ExteriorHero15','CAM_Plane_EngineDetail15','CAM_Plane_TailDetail15']
  for i,name in enumerate(camera_names):
   camera=G.P.STATE['cameras'].get(name)
   if not camera:raise RuntimeError('Missing actual authored camera '+name)
   eye=camera.get_actor_location();target=eye+u.MathLibrary.get_forward_vector(camera.get_actor_rotation())*500
   steps.append(('%02d_'%(62+i)+name.replace('CAM_Plane_',''),list(G.source(eye)),list(G.source(target))))
  for j in range(8):steps.append(('33_CurtainHold_%02d'%j,[-43.15,.8,1.45],[-43.15,1.92,1.3]))
  for j in range(8):steps.append(('34_CeilingHold_%02d'%j,[-28,13.5,1.7],[-28,16,3.4]))
  for j in range(12):steps.append(('35_A08Move_%02d'%j,[-28,12+j*.25,1.62],[-28,18.5,2]))
 if postures:
  steps=[('53_SecurityGuard',[-47.5,-2.2,1.35],[-47,-.4,.95]),('54_PlayerCharacter',[-50.4,-12.5,1.35],[-53,-12.5,1.0])]+[q for q in steps if q[0][:2] in ('55','56','58','59')]
 S.update(cam=cam,steps=steps,i=0,context=json.loads((G.R/'ArtBible/InstalledRuntime39.json').read_text()),captures=[],samples=[],output='PosturePhotos40.json' if postures else 'DetailPhotos39.json' if details else 'AssemblyPhotos38.json' if assembly else 'MountPhotos38.json' if mount else 'Photos38.json',begun=time.monotonic(),next=time.monotonic()+3);S['handle']=u.register_slate_post_tick_callback(tick);save()
