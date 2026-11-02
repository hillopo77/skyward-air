"""Actual viewport photographs of arrival26, keeping the gameplay render path."""
import unreal as u,json,time,hashlib,traceback
from pathlib import Path
def start(G,path):
 cfg=json.loads(Path(path).read_text(encoding='utf-8'));out=Path(cfg['report']);S=dict(i=0,after=time.monotonic()+2,captures=[]);cam=next(iter(G.S['cameras'].values()));pc=G.P.STATE['pc'];world=G.P.STATE['world']
 def save(status,**kw):
  import airport_clarity26 as C
  out.write_text(json.dumps(dict(status=status,captures=S['captures'],viewport=list(pc.get_viewport_size()),profile=C.S['profile'],native_viewport_capture=True,runtime_sha256=hashlib.sha256(Path(G.__file__).read_bytes()).hexdigest(),started=S['started'],finished=time.time() if status!='RUNNING' else None,**kw),indent=2),encoding='utf-8')
 def stop():
  for h in [S.get('handle'),G.S.get('handle'),G.P.STATE.get('handle')]:
   if h:
    try:u.unregister_slate_post_tick_callback(h)
    except Exception:pass
  u.SystemLibrary.quit_game(world,pc,u.QuitPreference.QUIT,False)
 def tick(dt):
  try:
   now=time.monotonic()
   if now<S['after']:return
   if S.get('waiting'):
    p=S['waiting']
    if p.exists() and p.stat().st_mtime>=S['requested']:S['captures'].append(dict(file=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),view=cfg['views'][S['i']]['name']));S.update(i=S['i']+1,waiting=None,after=now+.2);save('RUNNING')
    elif now-S['since']>25:raise RuntimeError('Viewport photo timed out')
    return
   if S['i']>=len(cfg['views']):save('SUCCESS');stop();return
   q=cfg['views'][S['i']]
   if S.get('camera')!=S['i']:
    G.S['show_hands_in_capture']=bool(q.get('first_person'));pawn=G.P.STATE['pawn']
    if q.get('first_person'):
     pawn.set_actor_location(G.v(q.get('player_eye',q['eye'])),False,True);pc.set_control_rotation(u.MathLibrary.find_look_at_rotation(pawn.get_actor_location(),G.v(q['target'])));pc.set_view_target_with_blend(pawn,0)
    else:cam.set_actor_location(G.v(q['eye']),False,True);cam.set_actor_rotation(u.MathLibrary.find_look_at_rotation(G.v(q['eye']),G.v(q['target'])),False);cam.camera_component.set_field_of_view(q.get('fov',76));cam.camera_component.set_editor_property('constrain_aspect_ratio',False);pc.set_view_target_with_blend(cam,0)
    S.update(camera=S['i'],after=now+1.0);return
   p=Path(q['file']);p.parent.mkdir(parents=True,exist_ok=True);S.update(waiting=p,requested=time.time(),since=now);u.SystemLibrary.execute_console_command(world,'Shot -nosuffix filename="'+p.as_posix()+'"',pc)
  except Exception:save('FAILED',error=traceback.format_exc());stop()
 S.update(started=time.time(),handle=u.register_slate_post_tick_callback(tick));save('RUNNING')
