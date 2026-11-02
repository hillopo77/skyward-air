"""Four native views and a matched lamps-off exposure comparison, no journey replay."""
import unreal as u,time,json,hashlib,traceback
G=None;S={}
def save(status='RUNNING',**kw):
 (G.R/'ArtBible/WarmQA33.json').write_text(json.dumps(dict(status=status,checks=S['checks'],captures=S['captures'],step=S['i'],elapsed_s=time.monotonic()-S['start'],viewport=list(G.P.STATE['pc'].get_viewport_size()),**kw),indent=2))
def check(n,b,**kw):S['checks'].append(dict(name=n,passed=bool(b),**kw))
def stop(status,**kw):
 save(status,**kw)
 for h in [S.get('handle'),G.S.get('handle'),G.P.STATE.get('handle')]:
  if h:
   try:u.unregister_slate_post_tick_callback(h)
   except Exception:pass
 u.SystemLibrary.quit_game(G.P.STATE['world'],G.P.STATE['pc'],u.QuitPreference.QUIT,False)
def tick(dt):
 try:
  t=time.monotonic()-S['since'];pc=G.P.STATE['pc'];world=G.P.STATE['world']
  if S.get('waiting'):
   p=S['waiting']
   if p.exists() and p.stat().st_mtime>=S['requested']:S['captures'].append(dict(file=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),view=S['name']));S.pop('waiting');S['i']+=1;S['since']=time.monotonic();save()
   elif t>20:raise RuntimeError('Screenshot timeout')
   return
  if S['i']>=len(S['steps']):stop('SUCCESS' if all(q['passed'] for q in S['checks']) else 'FAILED');return
  q=S['steps'][S['i']];op=q[0]
  if op=='wait':
   if t<q[1]:return
  elif op=='check':
   import airport_warm33 as L
   check('Native viewport1920x1080',tuple(pc.get_viewport_size())==(1920,1080));check('Eleven room fixture sources retained',len(L.S['lights'])==11);check('Suspended panels point down',all(a.get_actor_forward_vector().z<-.99 for a,q in L.S['lights'][5:7]));sky=u.GameplayStatics.get_all_actors_of_class(world,u.SkyLight)[0];check('Warm ambient fill restored',abs(sky.light_component.get_editor_property('intensity')-36)<.01 and not sky.light_component.get_editor_property('lower_hemisphere_is_black'));check('Corrected room mesh loaded',G.S['actors']['Check-in warm architecture29'].static_mesh_component.static_mesh.get_name()=='SM_AP_CheckinRoom33')
  elif op=='view':G.CAPTURE=True;pc.set_view_target_with_blend(G.S['cameras'][q[1]],0)
  elif op=='lamps':
   if q[1]==False:
    S['off']=[(a,a.light_component.get_editor_property('intensity')) for a in u.GameplayStatics.get_all_actors_of_class(world,u.RectLight) if -4300<a.get_actor_location().x<-2600 and 800<a.get_actor_location().y<1800]
    for a,n in S['off']:a.light_component.set_intensity(0.)
    check('Matched diagnostic disables physical check-in emitters',len(S['off'])>=11)
   else:
    for a,n in S['off']:a.light_component.set_intensity(n)
    check('Lamp intensities restored',all(abs(a.light_component.get_editor_property('intensity')-n)<.01 for a,n in S['off']))
  elif op=='photo':
   if t<1.2:return
   p=G.R/'Screenshots'/(q[1]+'.png');S.update(waiting=p,requested=time.time(),name=q[1]);u.SystemLibrary.execute_console_command(world,'Shot -nosuffix filename="'+p.as_posix()+'"',pc);return
  S['i']+=1;S['since']=time.monotonic();save()
 except Exception:stop('ERROR',error=traceback.format_exc())
def start(game):
 global G;G=game;steps=[('wait',3),('check',)]
 for view in ['01_EntryBreathingSpace','02_RightSideAccess','03_ProcessStartsAhead','04_CalmRoom','05_CeilingPanels']:steps += [('view',view),('photo',view)]
 S.update(i=0,checks=[],captures=[],steps=steps,start=time.monotonic(),since=time.monotonic());S['handle']=u.register_slate_post_tick_callback(tick);save()
