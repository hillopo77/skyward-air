"""Temporary read-only baseline review: genuine native frames, traces and transform samples."""
import unreal as u,json,time,hashlib,traceback,math
from pathlib import Path
G=None;S={}
V=[('01_Entrance',[-46.8,-13,1.62],[-43.2,-15,1.6]),('02_Checkin',[-40,-14,1.62],[-29,-14,1.4]),('03_BagDrop01',[-29.5,-11.25,1.62],[-26.15,-12,1]),('04_BagDrop02',[-30,-17.4,1.62],[-26.2,-16,1]),('05_SecurityEntry',[-44,-6.4,1.62],[-42,-2.9,1.6]),('06_WestEntryGap',[-47.3,-5.4,1.62],[-49,-4.2,1.3]),('07_Curtain',[-43.15,.8,1.45],[-43.15,1.92,1.3]),('08_ScannerControl',[-41.5,.95,1.25],[-42.52,2.05,.97]),('09_ScannerMonitor',[-41,1.3,1.62],[-41.95,2.32,1.55]),('10_StaffDoor',[-45.9,7.3,1.62],[-46,10,1.8]),('11_StaffStorage',[-45.7,12.7,1.62],[-48.2,12.5,1.2]),('12_Repacking',[-35.3,5.7,1.62],[-33.2,1.8,1.2]),('13_Concourse',[-30,6.6,1.62],[-30,10,1.7]),('14_A08Marker',[-29,12.9,1.62],[-31.1,17.8,2.04]),('15_A08Cubby',[-24.6,12.4,1.62],[-28,16,1.7]),('16_A08Ceiling',[-28,13.5,1.7],[-28,16.0,3.4]),('17_A08Interior',[-28,19,1.62],[-28,30,1.5]),('18_WCSign',[-28.2,-2.2,1.62],[-26.2,-3,1.9]),('19_WCLobby',[-24.5,-8.5,1.62],[-19,-9.5,1.3]),('20_WCEastGap',[-16.1,-5.5,1.62],[-13.5,-3.9,1.4]),('21_WCInterior',[-17,-6,1.62],[-17.1,-4.2,1]),('22_Arrivals',[-22,-20,1.62],[-18,-16,1.2]),('23_Cafe',[-34.2,18.2,1.62],[-41.3,26,1.6]),('24_CafeService',[-43.2,29,1.62],[-44,31.5,1.3]),('25_Gallery',[-45.6,25.7,4.77],[-44,31,4.5]),('26_A07Desks',[-20,-.8,1.62],[-14,.675,1.1]),('27_DeskClearance',[-20,-.6,1.62],[-17.5,-2,1]),('28_BridgeInside',[-12.7,.675,1.62],[-1.8,.675,1.6]),('29_DockingJoin',[-4.2,-2.8,1.8],[-2,.675,1.1]),('30_BridgeWing',[-5,16,7],[-13,3,0]),('31_ServiceRamp',[-20,16.2,1.62],[-16.8,20,1.2]),('32_Exterior',[25,-35,14],[-12,8,1])]
def save(status='RUNNING',**kw):
 (S['root']/'BaselineCapture38.json').write_text(json.dumps(dict(status=status,step=S['i'],captures=S['captures'],samples=S['samples'],traces=S.get('traces',[]),**kw),indent=2))
def tick(dt):
 try:
  cam=S['cam'];pc=G.P.STATE['pc'];now=time.monotonic()
  if not S.get('begun'):
   S['begun']=now;S['next']=now+2
  if now<S['next']:return
  if S.get('wait'):
   p=S['wait']
   if p.exists() and p.stat().st_mtime>=S['requested']:S['captures'].append(dict(file=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()));S.pop('wait');S['i']+=1;save()
   elif now-S['requested_mono']>20:raise RuntimeError('Audit frame timeout')
   return
  if S['i']>=len(S['steps']):
   traces=[]
   for n,start,end in [('WC east breach',[-15,-3.8,1],[-12,-3.8,1]),('Security west breach',[-48,-4.25,1],[-50,-4.25,1])]:
    hit=u.SystemLibrary.line_trace_single(G.P.STATE['world'],G.v(start),G.v(end),u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[G.P.STATE['pawn']],u.DrawDebugTrace.NONE,True);h=hit.to_tuple() if hit else [];c=h[10] if len(h)>10 else None;traces.append(dict(name=n,blocking=bool(h and h[0]),mesh=c.static_mesh.get_name() if c and c.static_mesh else None))
   S['traces']=traces;save('SUCCESS');u.unregister_slate_post_tick_callback(S['handle']);u.SystemLibrary.quit_game(G.P.STATE['world'],pc,u.QuitPreference.QUIT,False);return
  name,eye,target=S['steps'][S['i']]
  if S.get('view')!=name:
   cam.set_actor_location(G.v(eye),False,True);cam.set_actor_rotation(u.MathLibrary.find_look_at_rotation(G.v(eye),G.v(target)),False);S['view']=name;S['next']=now+.6;return
  sample={}
  for n,a in G.S['actors'].items():
   if n in ['X-ray scanner 01','X-ray scanner 02'] or n.startswith('Physical luggage'):
    c=a.static_mesh_component;sample[n]=dict(position=list(G.source(c.get_world_location())),speed=c.get_physics_linear_velocity().length()/100)
  S['samples'].append(dict(time=now-S['begun'],view=name,objects=sample));p=S['root']/'BaselineScreenshots'/(name+'.png');S.update(wait=p,requested=time.time(),requested_mono=now);u.SystemLibrary.execute_console_command(G.P.STATE['world'],'Shot -nosuffix filename="'+p.as_posix()+'"',pc)
 except Exception:
  save('ERROR',error=traceback.format_exc());u.unregister_slate_post_tick_callback(S['handle']);u.SystemLibrary.quit_game(G.P.STATE['world'],G.P.STATE['pc'],u.QuitPreference.QUIT,False)
def start(game):
 global G;G=game;root=G.R.parent/'Airport38/Audits';(root/'BaselineScreenshots').mkdir(parents=True,exist_ok=True);G.CAPTURE=True;cam=next(iter(G.S['cameras'].values()));cam.camera_component.set_field_of_view(78);G.P.STATE['pc'].set_view_target_with_blend(cam,0);steps=list(V)
 for j in range(8):steps.append(('33_CurtainHold_%02d'%j,[-43.15,.8,1.45],[-43.15,1.92,1.3]))
 for j in range(8):steps.append(('34_CeilingHold_%02d'%j,[-28,13.5,1.7],[-28,16,3.4]))
 for j in range(12):steps.append(('35_A08Move_%02d'%j,[-28,12.0+j*.25,1.62],[-28,18.5,2.0]))
 S.update(root=root,cam=cam,steps=steps,i=0,captures=[],samples=[]);S['handle']=u.register_slate_post_tick_callback(tick);save()
