"""Same-camera native Tourist morph/LOD comparison. Diagnostic, not delivery."""
import unreal as u,json,time,hashlib,traceback
G=None;S={}
CASES=[('LOD0ShadowBaseline',1,1.),('LOD0HighResShadow',1,1.)]

def save(status='RUNNING',**kw):
 (G.R/'ArtBible/Normals43QA.json').write_text(json.dumps(dict(status=status,context=S['context'],captures=S['captures'],cases=S['cases'],**kw),indent=2))

def finish(status,**kw):
 S['component'].set_forced_lod(0);S['component'].set_morph_target('SeatFit_Seated',1.);S['component'].set_cast_shadow(True);S['component'].set_cast_inset_shadow(False)
 save(status,**kw);u.unregister_slate_post_tick_callback(S['handle'])
 u.SystemLibrary.quit_game(G.P.STATE['world'],G.P.STATE['pc'],u.QuitPreference.QUIT,False)

def tick(dt):
 try:
  now=time.monotonic()
  if now<S['next']:return
  if S.get('pending'):
   p=S['pending']
   if p.exists() and p.stat().st_mtime>=S['request']:
    S['captures'].append(dict(name='Normals43_'+CASES[S['i']][0],file=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),kind='native',staged_camera=True))
    S.pop('pending');S['i']+=1;S['posed']=False;save();return
   if now-S['request_mono']>20:raise RuntimeError('Screenshot timeout')
   return
  if S['i']>=len(CASES):finish('SUCCESS');return
  name,lod,morph=CASES[S['i']];c=S['component']
  if not S.get('posed'):
   c.set_forced_lod(lod);c.set_morph_target('SeatFit_Seated',morph);c.set_cast_shadow(name!='LOD0NoSelfShadow');c.set_cast_inset_shadow(name=='LOD0InsetShadow')
   if name=='LOD0HighResShadow':
    u.SystemLibrary.execute_console_command(G.P.STATE['world'],'r.Shadow.MaxResolution 4096',G.P.STATE['pc'])
    lights=[]
    for actor in u.GameplayStatics.get_all_actors_of_class(G.P.STATE['world'],u.RectLight):
     comp=actor.light_component
     if (actor.get_actor_location()-G.v([-21.7,6.46,1.])).length()>800:continue
     before=comp.get_editor_property('shadow_resolution_scale');comp.set_editor_property('shadow_resolution_scale',4.)
     lights.append(dict(actor=actor.get_actor_label(),before=before,after=comp.get_editor_property('shadow_resolution_scale')))
    S['context']['high_resolution_shadow_probe']=dict(max_resolution=4096,lights=lights)
   S.update(posed=True,next=now+1.2);return
  try:predicted=c.get_editor_property('predicted_lod_level')
  except Exception:predicted=None
  S['cases'].append(dict(name=name,forced_lod_argument=lod,seat_fit_weight=morph,actual_seat_fit_weight=c.get_morph_target('SeatFit_Seated'),cast_shadow=c.get_editor_property('cast_shadow'),inset_shadow=c.get_editor_property('cast_inset_shadow'),predicted_lod=predicted,mesh=c.get_skeletal_mesh_asset().get_path_name()))
  p=G.R/'Screenshots'/('Normals43_'+name+'.png');S.update(pending=p,request=time.time(),request_mono=now)
  u.SystemLibrary.execute_console_command(G.P.STATE['world'],'Shot -nosuffix filename="'+p.as_posix()+'"',G.P.STATE['pc'])
 except Exception:finish('ERROR',error=traceback.format_exc())

def start(game):
 global G;G=game;G.QA=True;G.CAPTURE=False
 import characters12_runtime as C
 q=next(q for q in G.D['character_placements'] if q['name']=='Waiting passenger 0');c=C.ACTORS[q['actor']].skeletal_mesh_component
 cam=next(iter(G.S['cameras'].values()));cam.set_actor_location(G.v([-19,6.5,1.45]),False,True)
 cam.set_actor_rotation(u.MathLibrary.find_look_at_rotation(G.v([-19,6.5,1.45]),G.v([-21.7,6.46,1.1])),False);cam.camera_component.set_field_of_view(78.)
 G.P.STATE['pc'].set_view_target_with_blend(cam,0)
 context=json.loads((G.R/'ArtBible/InstalledRuntime39.json').read_text())
 try:context['stored_normal_import_method']=str(c.get_skeletal_mesh_asset().get_editor_property('asset_import_data').get_editor_property('normal_import_method'))
 except Exception as e:context['normal_method_read_error']=str(e)
 S.update(component=c,camera=cam,context=context,i=0,posed=False,captures=[],cases=[],next=time.monotonic()+2)
 S['handle']=u.register_slate_post_tick_callback(tick);save()
