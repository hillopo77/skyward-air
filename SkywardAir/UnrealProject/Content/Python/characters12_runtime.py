"""Native skeletal passengers, greetings and the selectable player pilot avatar."""
import unreal as u,json,time,math
from pathlib import Path
G=None;ACTORS={};CLIPS={};S=dict(third=False,skin=0,last_animation=None,greetings={})
def key(n):k=u.Key();k.import_text(n);return k
CHANGE=key('F7')
def initialize(game):
 global G,ACTORS,CLIPS;G=game
 import characters39_runtime
 characters39_runtime.prepare_before_initialize(G)
 R=Path(__file__).resolve().parents[3].parent/'Characters';revision=39 if '-AirportRepair38' in G.CMD and characters39_runtime.is_ready() else 21 if '-Characters21' in G.CMD else 19 if '-Characters19' in G.CMD else 18 if '-Characters18' in G.CMD else 13 if '-Characters13' in G.CMD else 12;R=R/('Revision'+str(revision)) if revision>12 else R;D=json.loads((R/('ArtBible/NativeCharacters'+str(revision)+'.json')).read_text());S['revision']=D.get('revision',12);assert D['status']=='SUCCESS'
 if '-AirportFoyer25' in G.CMD or '-AirportRepair38' in G.CMD:D['placements']=G.D['character_placements']
 elif '-AirportRooms24' in G.CMD:D['placements']=json.loads((Path(G.__file__).resolve().parents[4]/'Airport/Rooms24/Exports/character_layout24.json').read_text(encoding='utf-8'))
 ACTORS={a.get_actor_label():a for a in u.GameplayStatics.get_all_actors_of_class(G.P.STATE['world'],u.SkeletalMeshActor) if a.get_actor_label().startswith('CH12 ')};CLIPS={q['name']:u.load_asset(q['asset']) for q in D['animations']};S['hands']={side:G.S['actors'].get('CH12HAND '+side) for side in ('L','R')};S['hand_meshes']={n:u.load_asset(path) for n,path in D.get('view_hands',{}).items()};S['material_paths']=D.get('material_paths',{});S['placements']=D['placements'];S['meshes']=[q['asset'] for q in D['characters'] if q['name'].startswith('Player')];S['avatar']=ACTORS.get('CH12 Player avatar');G.S['actors'].update(ACTORS)
 S['crew_clips']={q['name']:u.load_asset(q['asset']) for q in D.get('crew_animations',[])}
 for i,q in enumerate(D['placements']):
  a=ACTORS.get(q['actor'])
  if not a:continue
  c=a.skeletal_mesh_component;c.set_component_tick_enabled(True);c.set_editor_property('visibility_based_anim_tick_option',u.VisibilityBasedAnimTickOption.ONLY_TICK_POSE_WHEN_RENDERED if S['revision']>=13 else u.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES);c.set_editor_property('pause_anims',False);c.play_animation((S['crew_clips'] if q['character'].startswith('Player') and S['crew_clips'] else CLIPS).get(q['animation'],CLIPS[q['animation']]),True)
  for morph in ('Blink','LookLeft','LookRight'):c.set_morph_target(morph,0.)
  if q['name'].startswith('Review model'):a.set_actor_hidden_in_game(True);continue
  if q['name']=='Player avatar':a.set_actor_hidden_in_game(True);continue
  if q.get('dialogue'):
   p=q['location'];r=math.radians(q['rotation_degrees']);G.S['targets'].append(dict(kind='npc',actor=q['actor'],point=[p[0]+math.sin(r)*.25,p[1]-math.cos(r)*.25,p[2]+1.3],title='Talk to '+('pilot' if q['character'].startswith('Player') else 'passenger'),dialogue=q['dialogue'],animation=q['animation'],character=q['character'],release_actor='CH12COLL '+q['name']))
 S['walkers']={q['actor']:dict(spec=q,index=1,origin=list(q['location'])) for q in D['placements'] if q.get('path')};old=G.P.toggle_review
 def review():
  if G.P.STATE.get('seated'):return old()
  S['third']=not S['third']
  if not S['third']:G.P.STATE['pc'].set_view_target_with_blend(G.P.STATE['pawn'],.12)
 G.P.toggle_review=review;G.S['character_count']=len(ACTORS)
 # Occupied benches are not offered as an empty seat.
 seated=[q for q in D['placements'] if q['animation'].endswith('Seated')]
 G.S['targets'][:]=[q for q in G.S['targets'] if q['kind']!='seat' or not any(math.hypot(q['eye'][0]-n['location'][0],q['eye'][1]-n['location'][1])<.38 and abs(q['eye'][2]-n['location'][2]-1.38)<.45 for n in seated)]
 original_sit=G.P.sit
 def sit(q):
  p=q.get('location',q.get('point',[999,999,999]))
  if any(math.hypot(p[0]-n['location'][0],p[1]-n['location'][1])<.28 and abs(p[2]-n['location'][2]-1.38)<.55 for n in seated):G.say('This seat is occupied');return
  return original_sit(q)
 G.P.sit=sit
 avatar=next(q for q in D['placements'] if q['name']=='Player avatar');S['skin']=next((i for i,path in enumerate(S['meshes']) if avatar['character'] in path),0);update_hand_colour()
 if '-CharacterReview' in G.CMD:
  pawn=G.P.STATE['pawn'];pawn.set_actor_location(G.v([-24.8,4.8,1.62]),False,True);G.P.STATE['pc'].set_control_rotation(u.MathLibrary.find_look_at_rotation(pawn.get_actor_location(),G.v([-24.8,8.6,1.30])))
 if S.get('revision')==39:characters39_runtime.after_initialize(__import__(__name__),G)

def update_hand_colour():
 colour=next((name for name in ('Yellow','Red','Green','Blue','Purple') if name in S['meshes'][S['skin']]),'Blue');material=u.load_asset(S['material_paths'].get('CH12_'+colour,''))
 if material:
  for hand in S['hands'].values():
   if hand:hand.static_mesh_component.set_material(0,material)

def greet(q):
 G.say(q['dialogue']);a=ACTORS.get(q['actor'])
 if a and not q.get('animation','').endswith('Seated'):a.skeletal_mesh_component.play_animation((S['crew_clips'] if q.get('character','').startswith('Player') and S['crew_clips'] else CLIPS)['Wave'],False);S['greetings'][q['actor']]=time.monotonic()+3
 G.event('Passenger greeted',actor=q['actor'])
def tick(dt):
 if not G:return
 now=time.monotonic()
 for name,walker in S.get('walkers',{}).items():
  if G.QA:continue
  q=walker['spec'];actor=ACTORS[name];point=actor.get_actor_location();goal=G.v([*q['path'][walker['index']],q['location'][2]]);delta=goal-point;delta.z=0;distance=delta.length();player=G.P.STATE['pawn'].get_actor_location();separation=point-player;separation.z=0
  if distance<8:walker['index']=(walker['index']+1)%len(q['path'])
  elif separation.length()>115:
   step=delta/max(distance,.01)*min(distance,q.get('speed',.65)*100*dt);actor.set_actor_location(point+step,False,True);actor.set_actor_rotation(u.Rotator(yaw=math.degrees(math.atan2(delta.y,delta.x))-90),False);proxy=G.S['actors'].get('CH12COLL '+q['name'])
   if proxy:proxy.set_actor_location(point+step+u.Vector(0,0,90),False,True)

 for i,(name,actor) in enumerate(ACTORS.items()):
  if S.get('revision',12)>=13 or name in S.get('face_overrides',{}):continue
  t=(now+i*.37)%(4+(i%8)*.07);value=math.sin(math.pi*t/.20)**2 if t<.20 else 0.;previous=S.setdefault('blink',{}).get(name,0.)
  if abs(value-previous)>.01:actor.skeletal_mesh_component.set_morph_target('Blink',value);S['blink'][name]=value
 for n,until in list(S['greetings'].items()):
  if now>until:ACTORS[n].skeletal_mesh_component.play_animation((S['crew_clips'] if S['crew_clips'] and any(q['actor']==n and q['character'].startswith('Player') for q in S['placements']) else CLIPS)['Idle'],True);del S['greetings'][n]
 a=S.get('avatar')
 if not a:return
 pc=G.P.STATE['pc'];pawn=G.P.STATE['pawn'];r=pc.get_control_rotation();p=pawn.get_actor_location();a.set_actor_location(p-u.Vector(0,0,162),False,True);a.set_actor_rotation(u.Rotator(yaw=r.yaw-90),False)
 third=S['third'] and not G.P.STATE.get('seated') and not G.S.get('spectator') and (not G.CAPTURE or G.S.get('show_avatar_in_capture')) and not G.QA;a.set_actor_hidden_in_game(not third or bool(S.get('camera_owner')))
 animation='Walk' if pawn.get_velocity().length()>30 else 'Idle'
 if animation!=S['last_animation']:a.skeletal_mesh_component.play_animation((S.get('crew_clips') or CLIPS)[animation],True);S['last_animation']=animation
 if pc.was_input_key_just_pressed(CHANGE):
  S['skin']=(S['skin']+1)%len(S['meshes']);m=u.load_asset(S['meshes'][S['skin']]);c=a.skeletal_mesh_component
  if hasattr(c,'set_skeletal_mesh_asset'):c.set_skeletal_mesh_asset(m)
  else:c.set_skeletal_mesh(m)
  c.play_animation((S.get('crew_clips') or CLIPS)[animation],True);update_hand_colour();G.say('Pilot colour changed · V toggles third-person view')
 if third and not G.CAPTURE and not S.get('camera_owner'):
  f=u.MathLibrary.get_forward_vector(u.Rotator(yaw=r.yaw));cam=G.S['cameras']['01_Entrance'];cp=p-f*300+u.Vector(0,0,85);cam.set_actor_location(cp,False,True);cam.set_actor_rotation(u.MathLibrary.find_look_at_rotation(cp,p-u.Vector(0,0,35)),False);pc.set_view_target_with_blend(cam,0)

 # Character-derived first-person hands receive the scene lighting normally.
 if S.get('paired_hand_owner'):return
 hands_visible=not third and not G.S.get('spectator') and (not G.CAPTURE or G.S.get('show_hands_in_capture')) and not G.QA
 forward=u.MathLibrary.get_forward_vector(r);right=u.MathLibrary.get_right_vector(r);up=u.MathLibrary.get_up_vector(r)
 for side,hand in S.get('hands',{}).items():
  if not hand:continue
  hand.set_actor_hidden_in_game(not hands_visible)
  if not hands_visible:continue
  held=bool(G.S.get('held')) and side=='R';mesh_name='SM_CH12_ViewHand_'+side+('Grip' if held else '');mesh=S['hand_meshes'].get(mesh_name)
  if mesh and S.setdefault('hand_current',{}).get(side)!=mesh_name:hand.static_mesh_component.set_static_mesh(mesh);S['hand_current'][side]=mesh_name;update_hand_colour()
  if held:
   body=G.S['actors'][G.S['held']].static_mesh_component;hp=body.get_center_of_mass()-right*15-forward*8
   grip=G.S.get('actor_specs',{}).get(G.S['held'],{}).get('action_grip_local_cm')
   if grip:
    tool=G.S['actors'][G.S['held']];rotation=tool.get_actor_rotation();scale=tool.get_actor_scale3d()
    hp=tool.get_actor_location()+u.MathLibrary.get_forward_vector(rotation)*(grip[0]*scale.x)+u.MathLibrary.get_right_vector(rotation)*(grip[1]*scale.y)+u.MathLibrary.get_up_vector(rotation)*(grip[2]*scale.z)
  else:hp=p+forward*48+right*(-28 if side=='L' else 28)+up*(-31+math.sin(now*3)*.4)
  hand.set_actor_location(hp,False,True);hand.set_actor_rotation(u.Rotator(pitch=r.pitch,yaw=r.yaw-90,roll=r.roll),False)
