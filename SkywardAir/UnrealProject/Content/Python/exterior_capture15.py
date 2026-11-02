"""Genuine settled native-game captures on the separate apron review map."""
import unreal as u
import time,json,hashlib
from pathlib import Path

def start(r):
 state={'after':time.monotonic()+20,'index':0,'phase':'start','handle':None,'captures':[]}
 shots=[('ExteriorHero15','UE_15_Exterior_Hero_Apron.png'),('ExteriorSide15','UE_15_Exterior_Profile_Apron.png'),('NoseDetail15','UE_15_Nose_Apron.png'),('EngineDetail15','UE_15_Engine_Apron.png'),('GearDetail15','UE_15_Gear_Apron.png'),('TailDetail15','UE_15_Tail_Apron.png'),('BrandDetail15','UE_15_Branding_Apron.png')]
 report=dict(status='RUNNING',map='/Game/Maps/L_Plane_Exterior15',source_sha256=hashlib.sha256((r.ROOT/'Plane.blend').read_bytes()).hexdigest(),manifest_sha256=hashlib.sha256((r.ROOT/'Exports/manifest.json').read_bytes()).hexdigest(),runtime_sha256=hashlib.sha256(Path(r.__file__).read_bytes()).hexdigest(),method='Unmodified standalone viewport Shot after settled native rendering; separate exterior review scene on apron.',captures=[])
 def save():(r.ROOT/'ArtBible/ExteriorValidation15.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 def tick(dt):
  if time.monotonic()<state['after'] or not r.STATE.get('configured'):return
  try:
   if state['phase']=='start':
    if state['index']>=len(shots):
     report['status']='SUCCESS';save();u.unregister_slate_post_tick_callback(state['handle']);u.SystemLibrary.quit_game(r.STATE['world'],r.STATE['pc'],u.QuitPreference.QUIT,False);return
    tag,file=shots[state['index']];camera=r.STATE['cameras']['CAM_Plane_'+tag];r.STATE['pc'].set_view_target_with_blend(camera,0);state.update(phase='shot',after=time.monotonic()+3.5,file=file,camera=camera.get_actor_label())
   elif state['phase']=='shot':
    path=r.ROOT/'Screenshots'/state['file'];state.update(path=path,capture_started=time.time(),deadline=time.monotonic()+20,phase='wait',after=time.monotonic()+.5)
    u.SystemLibrary.execute_console_command(r.STATE['world'],'Shot filename="'+str(path).replace('\\','/')+'" -nosuffix',r.STATE['pc'])
   else:
    path=state['path']
    if path.exists() and path.stat().st_mtime>=state['capture_started'] and path.stat().st_size>5000:
     report['captures'].append(dict(camera=state['camera'],file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bytes=path.stat().st_size));save();state.update(phase='start',index=state['index']+1,after=time.monotonic()+.1)
    elif time.monotonic()>state['deadline']:raise RuntimeError('Native screenshot did not arrive: '+str(path))
  except Exception as error:
   report.update(status='FAILED',error=str(error));save();u.unregister_slate_post_tick_callback(state['handle']);u.SystemLibrary.quit_game(r.STATE['world'],r.STATE['pc'],u.QuitPreference.QUIT,False)
 state['handle']=u.register_slate_post_tick_callback(tick);save()
