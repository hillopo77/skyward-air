"""Skyward character pack. Adds four selectable avatars/NPCs and the Z emote wheel.

Uses the project's existing editor-hosted runtime. Does not replace airport maps,
journey logic, collision proxies, navigation or seated-character assets.
"""
import unreal as u
import json,math,time,traceback
from pathlib import Path

BASE='/Game/CharacterPack_Oct30'
MANIFEST=Path(__file__).with_name('character_pack_manifest.json')
S={'installed':False,'wheel_open':False,'profile':0,'page':0,'emote':None,'widget':None,'callbacks':[],'npcs':{},'last_clip':None}
PREFERRED=['Salute','JoyfulJump','HipHopDancing','SalsaDancing2','SwingDancing','TwistDance','GoofyRunning','DancingTwerk','StandingIdle','Walking','Running','Jogging','RunningJump','CrouchedWalking','CrawlBackwards','Sitting','DancingMaraschinoStep','DwarfIdle','Flair','HipHopDancing2','SnakeHipHopDance']
DISPLAY={'JoyfulJump':'Jump','RunningJump':'Running jump','HipHopDancing':'Hip hop','HipHopDancing2':'Hip hop 2','SalsaDancing2':'Salsa','SwingDancing':'Swing','TwistDance':'Twist','GoofyRunning':'Goofy run','DancingTwerk':'Twerk','StandingIdle':'Idle','CrouchedWalking':'Crouch walk','CrawlBackwards':'Crab walk','DancingMaraschinoStep':'Maraschino','SnakeHipHopDance':'Snake dance','DwarfIdle':'Dwarf idle'}
NAMES=['GINGER','POLICE','CABIN CREW','COAT']
TARGETS=['CH12 Gate traveller','CH12 Security greeter','CH12 Gate pilot','CH12 Arrivals passenger 1']

def key(name):
 k=u.Key();k.import_text(name);return k
KEYS={n:key(n) for n in ['Z','Escape','Left','Right','F7','W','A','S','D','LeftShift','One','Two','Three','Four','Five','Six','Seven','Eight']}
NUMBERS=['One','Two','Three','Four','Five','Six','Seven','Eight']

def valid(obj):return bool(obj and u.SystemLibrary.is_valid(obj))
def page_items(page=None):
 p=S['page'] if page is None else page
 return PREFERRED[p*8:(p+1)*8]

def find_widget(name):
 w=S.get('widget')
 if not w:return None
 if hasattr(w,'get_widget_from_name'):return w.get_widget_from_name(name)
 return next((o for o in u.ObjectIterator(u.Widget) if o.get_name()==name and o.get_typed_outer(u.UserWidget)==w),None)

def refresh_wheel():
 if S.get('widget') and S.get('emotes'):S['emotes'].ui.refresh()

def create_wheel():
 if S.get('widget'):return S['widget']
 cl=u.load_class(None,BASE+'/UI/WBP_EmoteWheel.WBP_EmoteWheel_C');assert cl,'Emote wheel asset is missing'
 widget=u.get_default_object(u.WidgetLibrary).call_method('Create',(S['world'],cl,S['pc']));assert widget,'Could not create emote wheel';S['widget']=widget;widget.add_to_viewport(40)
 def bind(name,callback):
  button=find_widget(name);assert button,name;button.on_clicked.add_callable(callback);S['callbacks'].append(callback)
 def choice(index):
  def callback():choose_slot(index)
  return callback
 def character(index):
  def callback():select_profile(index)
  return callback
 for i in range(8):bind('Emote'+str(i),choice(i))
 for i in range(4):bind('Character'+str(i),character(i))
 bind('PreviousPage',lambda:change_page(-1));bind('NextPage',lambda:change_page(1));bind('CloseWheel',lambda:close_wheel(False));S['emotes'].build_widget();refresh_wheel();return widget

def change_page(delta):
 S['page']=(S['page']+delta)%math.ceil(len(PREFERRED)/8);S['emotes'].page_changed()

def open_wheel():
 return S['emotes'].open()

def close_wheel(keep_third=False):
 return S['emotes'].close(keep_third)

def select_profile(index):
 S['profile']=int(index)%4;S['emote']=None;S['last_clip']=None;actor=S['avatar'];comp=actor.skeletal_mesh_component;comp.set_skeletal_mesh_asset(S['profiles'][S['profile']]['mesh_obj']);comp.set_material(0,u.load_asset(S['profiles'][S['profile']]['material']));refresh_wheel()
 if S.get('emotes'):S['emotes'].profile_changed()

def choose_slot(index):
 items=page_items()
 if index<0 or index>=len(items):return
 choose_emote(items[index]);close_wheel(True)

def choose_emote(name):
 assert name in PREFERRED
 if not S['emotes'].begin_orbit():return
 profile=S['profiles'][S['profile']];clip=profile['animations'][name];once=name in ['Salute','RunningJump','JoyfulJump'];S['emote']={'name':name,'until':time.monotonic()+clip['duration'] if once else None};S['legacy'].S['third']=True;S['last_clip']=None

def new_actor(name,mesh):
 transform=u.Transform();library=u.get_default_object(u.GameplayStatics);actor=library.call_method('BeginDeferredActorSpawnFromClass',(S['world'],u.SkeletalMeshActor,transform,u.SpawnActorCollisionHandlingMethod.ALWAYS_SPAWN,None,u.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT));actor=library.call_method('FinishSpawningActor',(actor,transform,u.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT));actor.set_actor_label(name);comp=actor.skeletal_mesh_component;comp.set_skeletal_mesh_asset(mesh);comp.set_animation_mode(u.AnimationMode.ANIMATION_SINGLE_NODE);comp.set_collision_profile_name('NoCollision');comp.set_bounds_scale(1.3) if hasattr(comp,'set_bounds_scale') else None;comp.set_editor_property('cast_shadow',True);comp.set_editor_property('visibility_based_anim_tick_option',u.VisibilityBasedAnimTickOption.ONLY_TICK_POSE_WHEN_RENDERED);return actor

def greet(q):
 npc=S['npcs'].get(q.get('actor'))
 if not npc:return S['old_greet'](q)
 S['game'].say(q.get('dialogue','Hello!'));clip=npc['profile']['animations']['Salute'];npc['actor'].skeletal_mesh_component.play_animation(clip['obj'],False);npc['until']=time.monotonic()+clip['duration'];npc['last_clip']='Salute'

def install(game):
 if S['installed']:return True
 import characters12_runtime as legacy
 data=json.loads(MANIFEST.read_text(encoding='utf-8-sig'));assert data['status']=='SUCCESS';S.update(game=game,legacy=legacy,world=game.P.STATE['world'],pc=game.P.STATE['pc'],pawn=game.P.STATE['pawn'],old_greet=legacy.greet,old_change=legacy.CHANGE)
 profiles=[]
 for record in data['characters']:
  p=dict(record);p['mesh_obj']=u.load_asset(p['mesh']);assert p['mesh_obj'],p['mesh']
  for clip in p['animations'].values():clip['obj']=u.load_asset(clip['asset']);assert clip['obj'],clip['asset']
  profiles.append(p)
 assert len(profiles)==4;S['profiles']=profiles;S['avatar']=new_actor('CharacterPack Player',profiles[0]['mesh_obj']);S['avatar'].set_actor_hidden_in_game(True)
 legacy.CHANGE=key('None');legacy.greet=greet
 used=set()
 for i,p in enumerate(profiles):
  name=TARGETS[i];old=legacy.ACTORS.get(name)
  if not valid(old):
   q=next((q for q in legacy.S.get('placements',[]) if q['actor'] not in used and not q.get('animation','').endswith('Seated') and 'Review' not in q.get('name','') and q.get('name')!='Player avatar' and valid(legacy.ACTORS.get(q['actor']))),None)
   if not q:continue
   name=q['actor'];old=legacy.ACTORS[name]
  used.add(name);a=new_actor('CharacterPack '+NAMES[i],p['mesh_obj']);a.set_actor_transform(old.get_actor_transform(),False,True);a.set_actor_scale3d(u.Vector(1,1,1));old.set_actor_hidden_in_game(True);S['npcs'][name]={'actor':a,'source':old,'profile':p,'previous':old.get_actor_location(),'last_clip':None,'until':0}
 from emote_wheel_runtime import EmoteController
 S['emotes']=EmoteController(__import__(__name__))
 S['old_toggle_review']=game.P.toggle_review;S['old_use_nearest']=game.use_nearest;S['old_player_use']=game.P.use_nearest
 def toggle_review():
  if S['emotes'].view.active:
   if S['wheel_open']:close_wheel(True)
   S['emotes'].return_to_first_person(time.monotonic());return
  return S['old_toggle_review']()
 def use_nearest(*args,**kwargs):
  if S['wheel_open']:return True
  return S['old_use_nearest'](*args,**kwargs)
 S['input_wrappers']=(toggle_review,use_nearest);game.P.toggle_review=toggle_review;game.use_nearest=use_nearest;game.P.use_nearest=use_nearest
 S['installed']=True;create_wheel();game.say('Hold Z / drag toward an emote / release to play. Mouse orbits; move to return.');u.log('CHARACTER_PACK_READY: four characters, 21 clips each, hold-Z radial wheel');return True

def tick(dt):
 if S.get('busy'):return
 S['busy']=True
 try:
  if not S['installed']:
   import airport_runtime as game
   if not game.S.get('ready') or not game.P.STATE.get('configured'):return
   install(game)
  pc=S['pc'];pawn=S['pawn']
  if not valid(pc) or not valid(pawn):stop();return
  now=time.monotonic();legacy=S['legacy'];old_avatar=legacy.S.get('avatar')
  if valid(old_avatar):old_avatar.set_actor_hidden_in_game(True)
  S['emotes'].process_input(dt,now)
  if not S['wheel_open'] and pc.was_input_key_just_pressed(KEYS['F7']):select_profile(S['profile']+1)
  if S['emote'] and S['emote']['until'] and now>=S['emote']['until']:S['emote']=None;S['last_clip']=None
  actor=S['avatar'];actor.set_actor_location(pawn.get_actor_location()-u.Vector(0,0,162),False,True)
  if not S.get('external_pose'):actor.set_actor_rotation(u.Rotator(yaw=S['emotes'].view.body_yaw if S['emotes'].view.lock_body else pc.get_control_rotation().yaw-90),False)
  visible=(S['emotes'].avatar_visible(now) if S['emotes'].view.active else legacy.S.get('third',False)) or S.get('force_visible',False)
  visible=visible and not S['game'].P.STATE.get('seated') and not S['game'].S.get('spectator') and not S['game'].S.get('driving');actor.set_actor_hidden_in_game(not visible)
  S['emotes'].update_camera(dt)
  speed=pawn.get_velocity().length();name=S['emote']['name'] if S['emote'] else ('Running' if speed>30 and pc.is_input_key_down(KEYS['LeftShift']) else 'Walking' if speed>15 else 'StandingIdle')
  if not S.get('external_pose') and (S['profile'],name)!=S['last_clip']:actor.skeletal_mesh_component.play_animation(S['profiles'][S['profile']]['animations'][name]['obj'],name not in ['Salute','RunningJump','JoyfulJump']);S['last_clip']=(S['profile'],name)
  for name,npc in S['npcs'].items():
   old=npc['source'];a=npc['actor']
   if not valid(old) or not valid(a):continue
   p=old.get_actor_location();distance=(p-npc['previous']).length();a.set_actor_location(p,False,True);a.set_actor_rotation(old.get_actor_rotation(),False);old.set_actor_hidden_in_game(True);npc['previous']=p
   if now<npc['until']:continue
   clip='Walking' if distance/max(dt,.001)>10 else 'StandingIdle'
   if clip!=npc['last_clip']:a.skeletal_mesh_component.play_animation(npc['profile']['animations'][clip]['obj'],True);npc['last_clip']=clip
 except Exception:
  error=traceback.format_exc();u.log_error(error);p=Path(u.Paths.project_saved_dir())/'CharacterPack';p.mkdir(exist_ok=True);(p/'RuntimeError.txt').write_text(error,encoding='utf-8');stop()
 finally:S['busy']=False

def start():
 if S.get('handle'):return
 S['handle']=u.register_slate_post_tick_callback(tick)

def stop():
 if S.get('emotes'):S['emotes'].stop()
 if S.get('widget'):S['widget'].remove_from_parent();S['widget']=None
 if S.get('installed'):
  game=S['game']
  if S.get('input_wrappers'):
   if game.P.toggle_review is S['input_wrappers'][0]:game.P.toggle_review=S['old_toggle_review']
   if game.use_nearest is S['input_wrappers'][1]:game.use_nearest=S['old_use_nearest']
   if game.P.use_nearest is S['input_wrappers'][1]:game.P.use_nearest=S['old_player_use']
  S['legacy'].greet=S['old_greet'];S['legacy'].CHANGE=S['old_change']
  for npc in S['npcs'].values():
   if valid(npc['source']):npc['source'].set_actor_hidden_in_game(False)
   if valid(npc['actor']):npc['actor'].destroy_actor()
  if valid(S.get('avatar')):S['avatar'].destroy_actor()
 if S.get('handle'):u.unregister_slate_post_tick_callback(S['handle']);S['handle']=None
 S['installed']=False
