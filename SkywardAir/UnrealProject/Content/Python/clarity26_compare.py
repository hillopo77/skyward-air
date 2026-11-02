"""Native viewport captures during a short repeatable pan, no high-res override."""
import unreal as u,time,json,math,traceback,hashlib
def start(G,C):
 out=G.R/'ArtBible/ClarityCompare26.json';cam=next(iter(G.S['cameras'].values()));pc=G.P.STATE['pc'];world=G.P.STATE['world'];eye=G.v([-48.1,-12.6,1.62]);target=G.v([-43.3,-11.8,1.7]);base=u.MathLibrary.find_look_at_rotation(eye,target);cam.set_actor_location(eye,False,True);cam.camera_component.set_field_of_view(78);pc.set_view_target_with_blend(cam,0)
 names=list(C.PROFILES);S=dict(index=0,phase='setup',since=time.monotonic(),captures=[],frames=[],checks=[])
 def save(status,**kw):out.write_text(json.dumps(dict(status=status,captures=S['captures'],checks=S['checks'],viewport=list(pc.get_viewport_size()),**kw),indent=2),encoding='utf-8')
 def stop():
  for h in [S.get('handle'),G.S.get('handle'),G.P.STATE.get('handle')]:
   if h:
    try:u.unregister_slate_post_tick_callback(h)
    except Exception:pass
  u.SystemLibrary.quit_game(world,pc,u.QuitPreference.QUIT,False)
 def shot(label):
  p=G.R/'Screenshots'/(label+'.png');S.update(waiting=p,requested=time.time());u.SystemLibrary.execute_console_command(world,'Shot -nosuffix filename="'+p.as_posix()+'"',pc)
 def tick(dt):
  try:
   t=time.monotonic()-S['since'];phase=S['phase']
   if S.get('waiting'):
    p=S['waiting']
    if p.exists() and p.stat().st_mtime>=S['requested']:
     S['captures'].append(dict(file=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),profile=names[S['index']],kind=phase));S.pop('waiting')
     if phase=='still':S.update(phase='pan',since=time.monotonic(),frames=[])
     else:
      frames=sorted(S['frames']);S['checks'].append(dict(profile=names[S['index']],average_fps=len(frames)/sum(frames) if frames else None,p95_ms=frames[int(.95*(len(frames)-1))]*1000 if frames else None));S.update(index=S['index']+1,phase='setup',since=time.monotonic())
    elif t>25:raise RuntimeError('Viewport screenshot timed out')
    return
   if S['index']>=len(names):save('SUCCESS');stop();return
   if phase=='setup':C.apply_profile(names[S['index']]);cam.set_actor_rotation(base,False);S.update(phase='settle',since=time.monotonic());return
   if phase=='settle' and t>1.5:S['phase']='still';shot('Compare26_'+names[S['index']]+'_Still');return
   if phase=='pan':
    S['frames'].append(dt);yaw=base.yaw+math.sin(t*math.pi)*12;cam.set_actor_rotation(u.Rotator(pitch=base.pitch,yaw=yaw),False)
    if t>3.99:S['phase']='moving';cam.set_actor_rotation(base,False);shot('Compare26_'+names[S['index']]+'_Moving')
   save('RUNNING')
  except Exception:save('FAILED',error=traceback.format_exc());stop()
 S['handle']=u.register_slate_post_tick_callback(tick);save('RUNNING')
