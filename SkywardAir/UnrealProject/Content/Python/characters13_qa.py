"""Focused native verification of the remodeled cast, joint motion and contact."""
import unreal as u,time,json,math,hashlib,traceback
from pathlib import Path
G=None;S={}
def save(status='RUNNING'):
 (S['root']/'ArtBible/NativeQA13.json').write_text(json.dumps(dict(status=status,checks=S['checks'],phase=S.get('phase'),elapsed=time.monotonic()-S['start'],qa_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2))
def check(name,p,**kw):S['checks'].append(dict(name=name,passed=bool(p),**kw));u.log('CHARACTER13 QA '+name+' '+str(bool(p)));save()
def phase(p):S.update(phase=p,since=time.monotonic())
def stop():
 for h in (S.get('handle'),G.S.get('handle'),G.P.STATE.get('handle')):
  if h:
   try:u.unregister_slate_post_tick_callback(h)
   except Exception:pass
 u.SystemLibrary.quit_game(G.P.STATE['world'],G.P.STATE['pc'],u.QuitPreference.QUIT,False)
def tick(dt):
 try:
  import characters12_runtime as C
  t=time.monotonic()-S['since'];pawn=G.P.STATE['pawn'];pc=G.P.STATE['pc']
  if S['phase']=='warmup' and t>3:
   D=json.loads((S['root']/'ArtBible/NativeCharacters13.json').read_text());source=json.loads((S['root']/'Exports/characters12.json').read_text());check('Ten remodeled native character variants',len(D['characters'])==10);check('Five pilot avatar colours',len(C.S['meshes'])==5);check('Forty-two fitted bones in every character',all(a.skeletal_mesh_component.get_num_bones()==42 for a in C.ACTORS.values()),counts=sorted(set(a.skeletal_mesh_component.get_num_bones() for a in C.ACTORS.values())));check('Clavicles and both finger chains retained',all(a.skeletal_mesh_component.get_bone_index('ClavicleL')>=0 and a.skeletal_mesh_component.get_bone_index('ThumbR_2')>=0 and a.skeletal_mesh_component.get_bone_index('Finger4L_2')>=0 for a in C.ACTORS.values()));check('Normalized authored skin weights',all(abs(q['weight_range'][0]-1)<.02 and abs(q['weight_range'][1]-1)<.02 for q in source['characters']));check('Seven native motion clips',len(C.CLIPS)==7);check('Character skeleton roots remain unit scale',all(max(abs(v-1) for v in a.skeletal_mesh_component.get_socket_transform(a.skeletal_mesh_component.get_bone_name(0),u.RelativeTransformSpace.RTS_WORLD).scale3d.to_tuple())<.01 for a in C.ACTORS.values()));check('Derived player hands have open and grip meshes',len(C.S['hand_meshes'])==3)
   q=next(q for q in G.S['targets'] if q.get('actor')=='CH12 Security pilot');S['npc']=C.ACTORS[q['actor']];c=S['npc'].skeletal_mesh_component;c.set_editor_property('visibility_based_anim_tick_option',u.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES);S['hand_start']=c.get_socket_location('HandR');pawn.set_actor_location(G.v((-36.5,-.8,1.62)),False,True);pc.set_control_rotation(u.MathLibrary.find_look_at_rotation(pawn.get_actor_location(),G.point(q)));check('Remodeled NPC remains interactable',G.visible(q));G.act(q);phase('wave')
  elif S['phase']=='wave' and t>.7:
   c=S['npc'].skeletal_mesh_component;distance=(c.get_socket_location('HandR')-S['hand_start']).length();check('Wave moves the actual skinned wrist',distance>20,wrist_travel_cm=distance);S['npc'].skeletal_mesh_component.set_editor_property('visibility_based_anim_tick_option',u.VisibilityBasedAnimTickOption.ONLY_TICK_POSE_WHEN_RENDERED)
   a=C.ACTORS['CH12 Waiting passenger 0'];a.skeletal_mesh_component.set_editor_property('visibility_based_anim_tick_option',u.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES);S['bench']=a;a.skeletal_mesh_component.set_animation(None);pawn.set_actor_location(G.v((-26.5,3.3,1.5)),False,True);pc.set_control_rotation(u.MathLibrary.find_look_at_rotation(pawn.get_actor_location(),a.get_actor_location()+u.Vector(0,0,110)));phase('reference_foot')
  elif S['phase']=='reference_foot' and t>.4:
   a=S['bench'];c=a.skeletal_mesh_component;points=json.loads((S['root']/'Exports/FootSamples13.json').read_text())['PassengerTourist'];S['foot_local']={}
   for foot,values in points.items():
    reference=c.get_socket_transform(foot,u.RelativeTransformSpace.RTS_WORLD);S['foot_local'][foot]=[u.MathLibrary.inverse_transform_location(reference,u.MathLibrary.transform_location(a.get_actor_transform(),G.v(p))).to_tuple() for p in values]
   c.play_animation(C.CLIPS['Seated'],True);phase('contact')
  elif S['phase']=='contact' and t>.8:
   c=S['bench'].skeletal_mesh_component;zs=[c.get_socket_location(n).z/100 for n in ('FootL','FootR')];check('Seated foot joints reach floor level',all(.035<z<.18 for z in zs),joint_height_m=zs);scales=[c.get_socket_transform(n,u.RelativeTransformSpace.RTS_WORLD).scale3d.to_tuple() for n in ('FootL','FootR')];check('Seated shoes retain their size',all(max(abs(v-1) for v in scale)<.03 for scale in scales),world_scale=scales);mins=[min(u.MathLibrary.transform_location(c.get_socket_transform(foot,u.RelativeTransformSpace.RTS_WORLD),u.Vector(*p)).z/100 for p in values) for foot,values in S['foot_local'].items()];check('Actual skinned sole samples meet the floor',all(-.025<z<.025 for z in mins),sole_bottom_m=mins);c.set_editor_property('visibility_based_anim_tick_option',u.VisibilityBasedAnimTickOption.ONLY_TICK_POSE_WHEN_RENDERED)
   old=C.S['skin'];C.S['skin']=(old+1)%5;C.update_hand_colour();check('Pilot colour propagates to first-person hands',bool(C.S['hands']['R'].static_mesh_component.get_material(0)));C.S['skin']=old;C.update_hand_colour();G.P.toggle_review();check('Walking avatar view toggle retained',C.S['third']);G.P.toggle_review();S['frames']=len(G.S['frames']);phase('profile')
  elif S['phase']=='profile' and t>5:
   f=sorted(G.S['frames'][S['frames']:]);check('Populated remodeled airport renders interactively',len(f)>100 and len(f)/sum(f)>35,average_fps=len(f)/sum(f),p95_ms=f[int((len(f)-1)*.95)]*1000,samples=len(f));save('SUCCESS' if all(q['passed'] for q in S['checks']) else 'FAILED');stop()
 except Exception:
  (S['root']/'ArtBible/NativeQA13_Error.txt').write_text(traceback.format_exc());save('ERROR');stop()
def start(game):
 global G;G=game;S.update(root=Path(__file__).resolve().parents[4]/'Characters/Revision13',start=time.monotonic(),checks=[]);phase('warmup');S['handle']=u.register_slate_post_tick_callback(tick);save()
