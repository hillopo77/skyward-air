"""Standalone exterior camera tour for the Twin Towers map."""
import unreal as u,time,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[4]/'TwinTowers';STATE={};cmd=u.SystemLibrary.get_command_line()
def key(s):
 k=u.Key();k.import_text(s);return k
def start():
 state=STATE;state.update(after=time.monotonic()+15,index=0,phase='init',handle=None,captures=[])
 manifest=json.loads((R/'Exports/manifest.json').read_text());shots=[q['name'] for q in manifest['cameras']]
 report=dict(status='RUNNING',source_sha256=manifest['source_sha256'],manifest_sha256=hashlib.sha256((R/'Exports/manifest.json').read_bytes()).hexdigest(),captures=[],method='Unaltered settled native standalone viewport captures.')
 def save():(R/'ArtBible/NativeReview.json').write_text(json.dumps(report,indent=2))
 def tick(dt):
  now=time.monotonic()
  if now<state['after']:return
  try:
   if state['phase']=='init':
    w=None;pc=None
    for candidate in u.ObjectIterator():
     if isinstance(candidate,u.World):
      controller=u.GameplayStatics.get_player_controller(candidate,0)
      if controller and u.GameplayStatics.get_player_pawn(candidate,0):w=candidate;pc=controller;break
    if not pc:return
    state.update(world=w,pc=pc,pawn=u.GameplayStatics.get_player_pawn(w,0),cameras={a.get_actor_label():a for a in u.GameplayStatics.get_all_actors_of_class(w,u.CameraActor)},phase='capture' if '-TwinTowersCapture' in cmd else 'interactive')
    for q in ('r.ScreenPercentage 125','r.MotionBlurQuality 0','r.TemporalAASamples 16','r.Tonemapper.Sharpen 0.2'):u.SystemLibrary.execute_console_command(w,q,pc)
    pc.set_view_target_with_blend(state['cameras'][shots[0]],0);state['after']=now+3
   elif state['phase']=='interactive':
    pc=state['pc']
    if pc.was_input_key_just_pressed(key('V')):
     state['index']=(state['index']+1)%(len(shots)+1);pc.set_view_target_with_blend(state['cameras'][shots[state['index']]] if state['index']<len(shots) else state['pawn'],.35)
   elif state['phase']=='capture':
    if state['index']>=len(shots):
     report['status']='SUCCESS';save();u.unregister_slate_post_tick_callback(state['handle']);u.SystemLibrary.quit_game(state['world'],state['pc'],u.QuitPreference.QUIT,False);return
    state['pc'].set_view_target_with_blend(state['cameras'][shots[state['index']]],0);state.update(phase='shot',after=now+3.5)
   elif state['phase']=='shot':
    path=R/'Screenshots'/(shots[state['index']]+'.png');state.update(path=path,shot_started=time.time(),deadline=now+25,phase='wait',after=now+.5);u.SystemLibrary.execute_console_command(state['world'],'Shot filename="'+str(path).replace('\\','/')+'" -nosuffix',state['pc'])
   elif state['phase']=='wait':
    p=state['path']
    if p.exists() and p.stat().st_mtime>=state['shot_started'] and p.stat().st_size>5000:
     report['captures'].append(dict(camera=shots[state['index']],file=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size));save();state.update(index=state['index']+1,phase='capture',after=now+.1)
    elif now>state['deadline']:raise RuntimeError('Screenshot missing: '+str(p))
  except Exception as e:
   report.update(status='FAILED',error=str(e));save();u.unregister_slate_post_tick_callback(state['handle'])
 state['handle']=u.register_slate_post_tick_callback(tick)
