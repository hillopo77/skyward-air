"""Native capture sequence. Waits for actual PNGs before touching the camera."""
import unreal as u,time,json,hashlib
from pathlib import Path
def start(game):
 if "-AirportShotSet=" in game.CMD:
  if '-AirportClarity26' in game.CMD:
   import arrival26_photos
   return arrival26_photos.start(game,next(q.split("=",1)[1] for q in game.CMD.split() if q.startswith("-AirportShotSet=")))
  import focused_native_photos
  return focused_native_photos.start(game,next(q.split("=",1)[1] for q in game.CMD.split() if q.startswith("-AirportShotSet=")))
 # The product crosshair stays enabled in play; hide only that overlay in photographs.
 for actor in u.GameplayStatics.get_all_actors_of_class(game.P.STATE['world'],u.PostProcessVolume):
  settings=actor.get_editor_property('settings');wb=settings.get_editor_property('weighted_blendables');items=list(wb.get_editor_property('array'));keep=[q for q in items if not q.get_editor_property('object') or q.get_editor_property('object').get_name()!='M_AimReticle13']
  if len(keep)!=len(items):wb.set_editor_property('array',keep);settings.set_editor_property('weighted_blendables',wb);actor.set_editor_property('settings',settings)

 stages={1:['01_Entrance','07_BoardingBridge'],2:['01_Entrance','03_Security','08_Lounge'],3:['02_Departures','04_Baggage'],4:['03_Security','02_Departures'],5:['05_Concourse','06_Gate','12_Cafe','08_Lounge'],6:['09_Apron','10_Runway','11_Overview'],7:['03_Security','04_Baggage','09_Apron'],8:['02_Departures','06_Gate','07_BoardingBridge'],9:['01_Entrance','05_Concourse','09_Apron'],10:[q['name'] for q in game.D['cameras']]};names=list(dict.fromkeys(['01_Entrance','03_Security','06_Gate']+stages[game.STAGE]));
 if game.D.get('revision',10)>=11:names.append('25_SeatBackStowed');game.S['cameras']['25_SeatBackStowed']=game.S['cameras']['20_SeatBack17']
 state=dict(index=0,after=time.monotonic()+3,waiting=None,captures=[],busy=False)
 def tick(dt):
  if state['busy']:return
  state['busy']=True
  try:
   now=time.monotonic();S=game.S;P=game.P
   if now<state['after'] or not game.valid(P.STATE.get('pc')):return
   if state['waiting']:
    p=state['waiting']
    if p.exists() and p.stat().st_mtime>=state['requested_at']:
     state['captures'].append(dict(file=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),camera=names[state['index']]));state.update(waiting=None,index=state['index']+1,after=now+.3)
    elif now-state['wait_started']>35:raise RuntimeError('Native screenshot did not finish: '+str(p))
    return
   if state['index']>=len(names):
    d=dict(status='SUCCESS',pass_id=game.STAGE,pass_name=game.D['passes'][game.STAGE-1]['name'],captures=state['captures'],runtime_sha256=game.MODULE_SHA,native_bodies=len(S['physics']));(game.R/'ArtBible'/('Revision11_Captures.json' if game.D.get('revision',10)>=11 else 'Pass%02d_Captures.json'%game.STAGE)).write_text(json.dumps(d,indent=2));u.unregister_slate_post_tick_callback(state['handle']);u.unregister_slate_post_tick_callback(P.STATE['handle']);u.unregister_slate_post_tick_callback(S['handle']);u.SystemLibrary.quit_game(P.STATE['world'],P.STATE['pc'],u.QuitPreference.QUIT,False);return
   name=names[state['index']];cam=S['cameras'][name]
   if state.get('camera')!=name:
    if name=='20_SeatBack17':
     for n,m in P.STATE['movables'].items():
      if n.startswith('Economy folding tray 0117'):m['target']=m['progress']=1;P._apply_movable(m)
    if name=='25_SeatBackStowed':
     for n,m in P.STATE['movables'].items():
      if n.startswith('Economy folding tray '):m['target']=m['progress']=0;P._apply_movable(m)
     cam.set_actor_location(game.v([-1.1,15.12,1.0]),False,True);cam.set_actor_rotation(u.MathLibrary.find_look_at_rotation(game.v([-1.1,15.12,1.0]),game.v([-1.868,14.57,.62])),False);cam.camera_component.set_field_of_view(66)
    P.STATE['pc'].set_view_target_with_blend(cam,0);state.update(camera=name,after=now+.7);return
   p=game.R/'Screenshots'/(('Revision11_%s.png'%name) if game.D.get('revision',10)>=11 else 'Pass%02d_%s.png'%(game.STAGE,name));state.update(waiting=p,requested_at=time.time(),wait_started=now);u.SystemLibrary.execute_console_command(P.STATE['world'],'HighResShot 1600x1000 filename="'+p.as_posix()+'"',P.STATE['pc'])
  except Exception:
   import traceback;(game.R/'ArtBible'/('Pass%02d_CaptureError.txt'%game.STAGE)).write_text(traceback.format_exc(),encoding='utf-8');u.unregister_slate_post_tick_callback(state['handle']);u.SystemLibrary.quit_game(game.P.STATE['world'],game.P.STATE['pc'],u.QuitPreference.QUIT,False)
  finally:state['busy']=False
 state['handle']=u.register_slate_post_tick_callback(tick)
