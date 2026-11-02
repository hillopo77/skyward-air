"""Small reproducible native camera sets, separate from acceptance runs."""
import unreal as u,json,time,hashlib,traceback
from pathlib import Path
def start(G,path):
 cfg=json.loads(Path(path).read_text(encoding='utf-8'));out=Path(cfg['report']);out.parent.mkdir(parents=True,exist_ok=True)
 G.S['show_hands_in_capture']=cfg.get('keep_hands',False);audit=[]
 for actor in u.GameplayStatics.get_all_actors_of_class(G.P.STATE['world'],u.SkeletalMeshActor):
  origin,extent=actor.get_actor_bounds(False);audit.append(dict(name=actor.get_actor_label(),location=actor.get_actor_location().to_tuple(),scale=actor.get_actor_scale3d().to_tuple(),origin=origin.to_tuple(),extent=extent.to_tuple(),hidden=actor.get_editor_property('hidden'),visible=actor.skeletal_mesh_component.is_visible(),component_hidden=actor.skeletal_mesh_component.get_editor_property('hidden_in_game'),main_pass=actor.skeletal_mesh_component.get_editor_property('render_in_main_pass'),head=actor.skeletal_mesh_component.get_socket_location('Head').to_tuple(),root_scale=actor.skeletal_mesh_component.get_socket_transform(actor.skeletal_mesh_component.get_bone_name(0),u.RelativeTransformSpace.RTS_WORLD).scale3d.to_tuple()))
 if cfg.get('reference_pose'):
  for actor in u.GameplayStatics.get_all_actors_of_class(G.P.STATE['world'],u.SkeletalMeshActor):actor.skeletal_mesh_component.set_animation(None)
 out.with_suffix('.actors.json').write_text(json.dumps(audit,indent=2))
 dependencies={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),Path(G.__file__),Path(G.__file__).with_name('characters12_runtime.py'),Path(G.__file__).with_name('plane18_runtime.py')]}
 state=dict(started=time.time(),index=0,after=time.monotonic()+2,waiting=None,captures=[],busy=False)
 def save(status,**kw):out.write_text(json.dumps(dict(status=status,captures=state['captures'],runtime_sha256=G.MODULE_SHA,dependency_sha256=dependencies,started=state.get('started'),finished=time.time() if status!='RUNNING' else None,**kw),indent=2))
 def stop():
  for h in [state.get('handle'),G.S.get('handle'),G.P.STATE.get('handle')]:
   if h:
    try:u.unregister_slate_post_tick_callback(h)
    except Exception:pass
  u.SystemLibrary.quit_game(G.P.STATE['world'],G.P.STATE['pc'],u.QuitPreference.QUIT,False)
 def tick(dt):
  if state['busy']:return
  state['busy']=True
  try:
   if time.monotonic()<state['after']:return
   if state['waiting']:
    p=state['waiting']
    if p.exists() and p.stat().st_mtime>=state['requested']:
     state['captures'].append(dict(file=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),view=cfg['views'][state['index']]['name']));state.update(index=state['index']+1,waiting=None,after=time.monotonic()+.2)
    return
   if state['index']>=len(cfg['views']):save('SUCCESS');stop();return
   q=cfg['views'][state['index']]
   if state.get('camera')!=state['index']:
    cam=next(iter(G.S['cameras'].values()));cam.set_actor_location(G.v(q['eye']),False,True);cam.set_actor_rotation(u.MathLibrary.find_look_at_rotation(G.v(q['eye']),G.v(q['target'])),False);cam.camera_component.set_field_of_view(q.get('fov',72));cam.camera_component.set_editor_property('constrain_aspect_ratio',False)
    for name,actor in G.S['actors'].items():
     if name.startswith('CH12 Review model'):actor.set_actor_hidden_in_game(not q.get('character_review',False))
    import characters12_runtime as characters
    for name in characters.S.get('face_overrides',{}):
     for key in ('Blink','LookLeft','LookRight'):characters.ACTORS[name].skeletal_mesh_component.set_morph_target(key,0.)
    characters.S['face_overrides']=q.get('face_morphs',{})
    for name,values in characters.S['face_overrides'].items():
     for key,value in values.items():characters.ACTORS[name].skeletal_mesh_component.set_morph_target(key,value)
    for name,value in q.get('movables',{}).items():
     m=G.P.STATE['movables'][name];m['target']=m['progress']=value;G.P._apply_movable(m)
    G.S['show_hands_in_capture']=bool(q.get('first_person'));G.S['show_avatar_in_capture']=bool(q.get('third_person'))
    if q.get('first_person') or q.get('third_person'):
     pawn=G.P.STATE['pawn'];pawn.set_actor_location(G.v(q.get('player_eye',q['eye'])),False,True);G.P.STATE['pc'].set_control_rotation(u.MathLibrary.find_look_at_rotation(pawn.get_actor_location(),G.v(q.get('player_look',q['target']))))
     if q.get('third_person'):
      import characters12_runtime as characters;characters.S['third']=True
    for review_actor in u.GameplayStatics.get_all_actors_of_class(G.P.STATE['world'],u.SkeletalMeshActor):
     if review_actor.get_actor_label().endswith('Pilot terminal art review'):review_actor.set_actor_hidden_in_game(bool(q.get('third_person')))
    if q.get('crew_animation'):
     preview=next((a for a in u.GameplayStatics.get_all_actors_of_class(G.P.STATE['world'],u.SkeletalMeshActor) if a.get_actor_label().endswith('Pilot terminal art review')),None)
     if preview:preview.skeletal_mesh_component.play_animation(characters.S['crew_clips'][q['crew_animation']],True)
    G.P.STATE['pc'].set_view_target_with_blend(G.P.STATE['pawn'] if q.get('first_person') else cam,0);state.update(camera=state['index'],after=time.monotonic()+.7);return
   if cfg.get('bone_audit'):
    pose=[]
    for actor in u.GameplayStatics.get_all_actors_of_class(G.P.STATE['world'],u.SkeletalMeshActor):
     if not (actor.get_actor_label().startswith(('CH19 ','CH21 ')) or actor.get_actor_label()=='CH12 Player avatar'):continue
     c=actor.skeletal_mesh_component;pose.append(dict(actor=actor.get_actor_label(),location=actor.get_actor_location().to_tuple(),bones={n:c.get_socket_location(n).to_tuple() for n in ['Pelvis','Chest','Head','HandL','HandR','FootL','FootR']},root_scale=c.get_socket_transform(c.get_bone_name(0),u.RelativeTransformSpace.RTS_WORLD).scale3d.to_tuple()))
    state.setdefault('pose_samples',{})[q['name']]=pose;out.with_suffix('.pose.json').write_text(json.dumps(state['pose_samples'],indent=2))
   p=Path(q['file']);p.parent.mkdir(parents=True,exist_ok=True);state.update(waiting=p,requested=time.time());u.SystemLibrary.execute_console_command(G.P.STATE['world'],'HighResShot 1600x1000 filename="'+p.as_posix()+'"',G.P.STATE['pc'])
  except Exception:save('FAILED',error=traceback.format_exc());stop()
  finally:state['busy']=False
 state['handle']=u.register_slate_post_tick_callback(tick);save('RUNNING')
