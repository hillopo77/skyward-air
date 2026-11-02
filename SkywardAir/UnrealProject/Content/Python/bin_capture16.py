"""Focused bin motion/selection check and fresh photos; no walkthrough suite."""
import unreal as u,time,json,hashlib
from pathlib import Path
def start(r):
 st=dict(phase='test',index=0,after=time.monotonic()+20,handle=None);names=['Overhead bin R 12','Overhead bin L 12','Overhead bin R 16'];shots=[('EconomyCeiling13','UE_16_Bins_Cabin.png',False),('Bins13','UE_16_Bins_Closed.png',False),('Bins13','UE_16_Bins_Open.png',True),('CargoOverview15','UE_16_Cargo_Overview.png',False),('CargoClose15','UE_16_Cargo_Close.png',False),('CargoSuitcases15','UE_16_Cargo_Cases.png',False),('CargoMixed15','UE_16_Cargo_Mixed.png',False)]
 report=dict(status='RUNNING',revision='16',scope='Focused selection/open/close of three changed bins and seven actual game views. No complete walking or all-fittings suite.',source_sha256=hashlib.sha256((r.ROOT/'Plane.blend').read_bytes()).hexdigest(),runtime_sha256=hashlib.sha256(Path(r.__file__).read_bytes()).hexdigest(),manifest_sha256=hashlib.sha256((r.ROOT/'Exports/manifest.json').read_bytes()).hexdigest(),checks=[],captures=[])
 def save():(r.ROOT/'ArtBible/TargetedBins16.json').write_text(json.dumps(report,indent=2))
 def check(test,passed,**facts):report['checks'].append(dict(test=test,passed=bool(passed),**facts));save()
 def tick(dt):
  now=time.monotonic()
  if now<st['after'] or not r.STATE.get('configured'):return
  try:
   if st['phase']=='test':
    if st['index']>=len(names):st.update(phase='camera',index=0);return
    name=names[st['index']];q=r.STATE['movables'][name]['item'];side=1 if ' R ' in name else -1;r.reposition(r.vector([side*.85,q['point'][1],1.62]).to_tuple());r.STATE['pc'].set_view_target_with_blend(r.STATE['pawn'],0);r.point_at_item(q);nearest=r.nearest();action=r.use_nearest();check('Select changed bin '+name,nearest and nearest['actor']==name and action=='movable');st.update(name=name,phase='open',after=now+1.1)
   elif st['phase']=='open':
    m=r.STATE['movables'][st['name']];check('Lift-up bin reaches open stop '+st['name'],m['progress']>.995);m['target']=0;st.update(phase='closed',after=now+1.1)
   elif st['phase']=='closed':
    check('Bin fully closes '+st['name'],r.STATE['movables'][st['name']]['progress']<.005);st.update(phase='test',index=st['index']+1)
   elif st['phase']=='camera':
    if st['index']>=len(shots):
     report['status']='SUCCESS' if all(c['passed'] for c in report['checks']) else 'FAILED';save();u.unregister_slate_post_tick_callback(st['handle']);u.SystemLibrary.quit_game(r.STATE['world'],r.STATE['pc'],u.QuitPreference.QUIT,False);return
    tag,file,opened=shots[st['index']];r.STATE['movables']['Overhead bin R 07']['target']=1 if opened else 0;r.STATE['pc'].set_view_target_with_blend(r.STATE['cameras']['CAM_Plane_'+tag],0);st.update(file=file,camera=tag,phase='shot',after=now+3.5)
   elif st['phase']=='shot':
    p=r.ROOT/'Screenshots'/st['file'];st.update(path=p,started=time.time(),deadline=now+25,phase='wait',after=now+.5);u.SystemLibrary.execute_console_command(r.STATE['world'],'Shot filename="'+str(p).replace('\\','/')+'" -nosuffix',r.STATE['pc'])
   else:
    p=st['path']
    if p.exists() and p.stat().st_mtime>=st['started'] and p.stat().st_size>5000:
     report['captures'].append(dict(camera=st['camera'],file=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()));save();st.update(phase='camera',index=st['index']+1,after=now+.1)
    elif now>st['deadline']:raise RuntimeError('Screenshot missing '+str(p))
  except Exception as e:
   report.update(status='FAILED',error=str(e));save();u.unregister_slate_post_tick_callback(st['handle']);u.SystemLibrary.quit_game(r.STATE['world'],r.STATE['pc'],u.QuitPreference.QUIT,False)
 st['handle']=u.register_slate_post_tick_callback(tick);save()
