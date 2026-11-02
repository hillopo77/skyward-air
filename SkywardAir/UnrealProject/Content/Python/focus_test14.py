"""Live-world aim tolerance comparison, including physical occlusion controls."""
import unreal as u
import ast,hashlib,json,math,time

class Tester:
 def __init__(self,r):
  self.r=r;self.after=time.monotonic()+8;self.done=False

 def tick(self,dt):
  if self.done or time.monotonic()<self.after:return
  self.done=True;r=self.r;out=[];checks=[]
  baseline=r.ROOT/'Versions/Revision13_Before_InteractionEase14/Python/skyward_runtime.py'
  tree=ast.parse(baseline.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='nearest');fn.name='nearest13'
  ns=dict(r.__dict__);exec(compile(ast.Module(body=[fn],type_ignores=[]),str(baseline),'exec'),ns);old=ns['nearest13']
  pc=r.STATE['pc'];pawn=r.STATE['pawn'];kinds={}
  counters={}
  for index,q in enumerate(r.STATE['items']):
   if q.get('activation')=='inspect_only':continue
   required=q.get('requires_open')
   if required:
    m=r.STATE['movables'][required];m['progress']=m['target']=1.;r._apply_movable(m)
   kind=q['kind'];pt=q['point']
   fallback=[pt[0],pt[1]+.85,1.62] if kind=='seat' else [pt[0],pt[1]+.36,1.62] if kind=='screen' else [pt[0]*.65,pt[1],1.62] if kind in ('control','inspect') else [pt[0]*.55,pt[1],1.62]
   approach=r.DATA['layout']['validation'].get('seat_approaches',{}).get(q['actor'],q.get('validation_approach',fallback))
   r.reposition(list(r.vector(approach).to_tuple()));r.point_at_item(q);rotation=pc.get_control_rotation()
   # Four ordinary aiming errors; dense clusters may correctly select a nearer
   # neighbouring key. Record all outcomes without counting those as passes.
   counters[kind]=counters.get(kind,0)+1
   sample_offsets=counters[kind]<=8 or (kind=='seat' and required) or ('cockpit' in q['actor'].lower() and counters[kind]%6==0)
   for yaw,pitch in (((0,0),(3,0),(-3,0),(0,3),(0,-3),(6,0),(-6,0),(0,6),(0,-6)) if sample_offsets else ((0,0),)):
    pc.set_control_rotation(u.Rotator(pitch=rotation.pitch+pitch,yaw=rotation.yaw+yaw,roll=0))
    before=old();now=r.nearest();out.append(dict(actor=q['actor'],kind=kind,yaw_offset=yaw,pitch_offset=pitch,old_selected=before['actor'] if before else None,selected=now['actor'] if now else None,old_match=bool(before and before['actor']==q['actor']),match=bool(now and now['actor']==q['actor'])))
   if index%25==0:(r.ROOT/'ArtBible/InteractionEase14_Progress.json').write_text(json.dumps(dict(item_index=index,samples=len(out))),encoding='utf-8')
   if required:
    m=r.STATE['movables'][required];m['progress']=m['target']=0.;r._apply_movable(m)
  exact=[x for x in out if not x['yaw_offset'] and not x['pitch_offset']];offset=[x for x in out if x['yaw_offset'] or x['pitch_offset']]
  # Deliberately put a synthetic target beyond an opaque fuselage wall, while
  # staying in ordinary nearby reach. Both its own ray and selection must fail.
  saved=r.STATE['items'];r.reposition(list(r.vector([1.6,15,1.62]).to_tuple()))
  fake=dict(kind='control',actor='Behind opaque wall14',point=[3,15,1.62]);r.STATE['items']=[fake];r.point_at_item(fake)
  wall_blocked=not r.interaction_visible(fake) and r.nearest() is None;r.STATE['items']=saved
  # Clicking empty space from a seat must not eject the player.
  seat=next(q for q in saved if q['kind']=='seat' and q.get('screen_actor'))
  r.reposition(list(r.vector([0,15,1.62]).to_tuple()));r.sit(seat);pc.set_control_rotation(u.Rotator(pitch=-89,yaw=0,roll=0))
  no_eject=r.use_nearest(stand_on_miss=False) is None and r.STATE['seated'] is not None;r.stand()
  checks=[dict(name='exact aim retains every target',passed=all(x['match'] for x in exact),failures=[x for x in exact if not x['match']]),dict(name='opaque wall blocks assisted selection',passed=wall_blocked),dict(name='empty click does not leave seat',passed=no_eject),dict(name='off-centre successful target count improves',passed=sum(x['match'] for x in offset)>sum(x['old_match'] for x in offset))]
  for kind in sorted({x['kind'] for x in out}):
   group=[x for x in offset if x['kind']==kind];kinds[kind]=dict(samples=len(group),old_matches=sum(x['old_match'] for x in group),matches=sum(x['match'] for x in group))
  report=dict(status='SUCCESS' if all(x['passed'] for x in checks) else 'FAILED',runtime_sha256=hashlib.sha256(__import__('pathlib').Path(r.__file__).read_bytes()).hexdigest(),source_blend_sha256=hashlib.sha256((r.ROOT/'SourceAssets/Blender/SkywardAir.blend').read_bytes()).hexdigest(),baseline_sha256=hashlib.sha256(baseline.read_bytes()).hexdigest(),method='Actual game-world aiming at original targets and +/-3, +/-6 degrees in yaw/pitch. Same poses and physical occlusion for both selectors. Offset matches are measurements, not automatically pass/fail in dense clusters.',exact_samples=len(exact),offset_samples=len(offset),old_offset_matches=sum(x['old_match'] for x in offset),offset_matches=sum(x['match'] for x in offset),by_kind=kinds,checks=checks,samples=out)
  (r.ROOT/'ArtBible/InteractionEase14.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
  u.SystemLibrary.quit_game(r.STATE['world'],pc,u.QuitPreference.QUIT,False)
