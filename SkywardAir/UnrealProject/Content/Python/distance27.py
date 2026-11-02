"""Native near/mid/far and in-motion distance evidence, including real viewport state."""
import unreal as u,time,json,hashlib,traceback
def start(G,C):
 out=G.R/'ArtBible/Distance27.json';pc=G.P.STATE['pc'];world=G.P.STATE['world'];cam=next(iter(G.S['cameras'].values()));S=dict(i=0,after=time.monotonic()+2,captures=[],frames=[],checks=[])
 cfg=[('Near_2m',[-45.3,-13,1.7],[-43.23,-13,1.88],False),('Mid_5m',[-48.3,-12.5,1.62],[-43.23,-13,1.88],False),('Far_7m',[-50.25,-12.5,1.62],[-43.23,-13,1.88],False),('Far_Moving',[-50.25,-12.5,1.62],[-43.23,-13,1.88],True)]
 def save(status,**kw):out.write_text(json.dumps(dict(status=status,captures=S['captures'],viewport=list(pc.get_viewport_size()),profile=C.S['profile'],checks=S['checks'],finished=time.time() if status!='RUNNING' else None,**kw),indent=2),encoding='utf-8')
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
    if p.exists() and p.stat().st_mtime>=S['requested']:
     S['captures'].append(dict(file=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),view=cfg[S['i']][0],distance_m=(G.v(cfg[S['i']][1])-G.v(cfg[S['i']][2])).length()/100));S.update(i=S['i']+1,waiting=None,after=now+.1);save('RUNNING')
    elif now-S['requested_mono']>20:raise RuntimeError('distance photograph timed out')
    return
   if S['i']>=len(cfg):
    for n in ['SignStart','SignHeader','SignWelcome','FlightBoard']:
     t=u.load_asset('/Game/Airport27/Textures/T27_'+n);S['checks'].append(dict(name=n+' keeps full print resolution',passed=bool(t and t.get_editor_property('never_stream') and t.get_editor_property('mip_gen_settings')==u.TextureMipGenSettings.TMGS_NO_MIPMAPS)))
    S['checks'].append(dict(name='Actual viewport is 1920x1080',passed=tuple(pc.get_viewport_size())==(1920,1080)))
    save('SUCCESS' if all(q['passed'] for q in S['checks']) else 'FAILED',pan_sample_average_fps=len(S['frames'])/sum(S['frames']) if S['frames'] else None);stop();return
   name,eye,target,moving=cfg[S['i']]
   if S.get('camera')!=S['i']:
    cam.set_actor_location(G.v(eye),False,True);rot=u.MathLibrary.find_look_at_rotation(G.v(eye),G.v(target));cam.set_actor_rotation(rot,False);cam.camera_component.set_field_of_view(78.);cam.camera_component.set_editor_property('constrain_aspect_ratio',False);pc.set_view_target_with_blend(cam,0);S.update(camera=S['i'],base_rot=rot,begin=now,after=now+1);return
   if moving and now-S['begin']<4:
    import math
    t=now-S['begin'];rot=S['base_rot'];cam.set_actor_rotation(u.Rotator(pitch=rot.pitch,yaw=rot.yaw+7*math.sin(t*2.7),roll=0),False);S['frames'].append(dt);return
   p=G.R/'Screenshots'/('Distance27_'+name+'.png');S.update(waiting=p,requested=time.time(),requested_mono=now);u.SystemLibrary.execute_console_command(world,'Shot -nosuffix filename="'+p.as_posix()+'"',pc)
  except Exception:save('FAILED',error=traceback.format_exc());stop()
 S['handle']=u.register_slate_post_tick_callback(tick);save('RUNNING')
