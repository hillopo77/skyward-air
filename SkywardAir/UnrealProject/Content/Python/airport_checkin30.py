"""Single-player check-in queue with live passengers and an explicit desk call."""
import unreal as u,time,json,math
G=None;C=None;S={}
def animate(name,clip):
 if S['clips'].get(name)==clip:return
 import characters12_runtime as CH
 actor=G.S['actors'].get(name);anim=CH.CLIPS.get(clip)
 if actor and anim:actor.skeletal_mesh_component.play_animation(anim,True);S['clips'][name]=clip
def move(name,goal,dt):
 a=G.S['actors'][name];delta=G.v(goal)-a.get_actor_location();delta.z=0
 if delta.length()<9:animate(name,'Idle');return True
 if (a.get_actor_location()-G.P.STATE['pawn'].get_actor_location()+u.Vector(0,0,162)).length()<78:animate(name,'Idle');return False
 step=delta/max(delta.length(),.01)*min(delta.length(),140*dt);a.set_actor_location(a.get_actor_location()+step,False,True);a.set_actor_rotation(u.Rotator(yaw=math.degrees(math.atan2(delta.y,delta.x))-90),False);animate(name,'Walk')
 q=next(q for q in G.D['character_placements'] if q['actor']==name);proxy=G.S['actors'].get('CH12COLL '+q['name'])
 if proxy:proxy.set_actor_location(a.get_actor_location()+u.Vector(0,0,90),False,True)
 return False
def act(q):
 if q['actor']==G.D['checkin30']['queue_actor']:
  if not S['joined']:
   S.update(joined=True,next=time.monotonic()+3.2);G.event('Player joined check-in queue30',passengers_ahead=len(S['remaining']))
  return
 if q['kind']=='checkin' and q['actor'].startswith('Check-in desk ') and not G.S.get('checked_in') and not S['called']:
  G.say('Join the check-in queue at the gold marker first');G.event('Check-in queue respected30',actor=q['actor']);return
 return S['base_act'](q)
def tick(dt):
 S['base'](dt);now=time.monotonic()
 if S['joined'] and S['remaining'] and now>=S['next']:
  name=S['remaining'].pop(0);spec=next(q for q in G.D['character_placements'] if q['actor']==name);proxy=G.S['actors'].get('CH12COLL '+spec['name']);proxy.static_mesh_component.set_collision_response_to_channel(u.CollisionChannel.ECC_PAWN,u.CollisionResponseType.ECR_IGNORE) if proxy else None;S['departures'][name]=dict(path=[[-32.2,-13,0],[-31.7,-14.6,0],.7,[-32.1,-13,0],[-32.1,-8.8,0],[-30,-8.8,0],[-30,-6,0],[-40+2.3*G.D['checkin30']['npc_order'].index(name),-6,0]],index=0);S['next']=now+3.2;G.event('Queue passenger advances30',actor=name,remaining=len(S['remaining']))
  if not S['remaining']:S['called']=True;G.event('Player called to check-in desk30',desk='01')
 if S['joined']:
  for i,name in enumerate(S['remaining']):move(name,[G.D['checkin30'].get('front_x',-33.9)-i*G.D['checkin30'].get('spacing_m',1.8),-13,0],dt)
  for name,item in list(S['departures'].items()):
   if item['index']>=len(item['path']):animate(name,'Idle');continue
   goal=item['path'][item['index']]
   if isinstance(goal,float):
    if 'until' not in item:item['until']=now+goal
    if now>=item['until']:item.pop('until');item['index']+=1
   elif move(name,goal,dt):item['index']+=1
 if now-S.get('ui_time',0)>.1:
  S['ui_time']=now
  if not G.S.get('checked_in'):
   key='Called' if S['called'] else 'Queue'+str(len(S['remaining'])) if S['joined'] else 'JoinQueue'
   if key!=S.get('shown'):C.S['mid'].set_texture_parameter_value('Journey',S['textures']['HUD_'+key]);S['shown']=key
  q=G.nearest() if not G.CAPTURE else None
  if q and q['actor']==G.D['checkin30']['queue_actor']:C.S['mid'].set_texture_parameter_value('Hint',S['textures']['HUD_HintJoin']);S['hint']=True
  elif S.get('hint'):
   key='Hint_'+C.S.get('hint','None')
   if key in C.S['textures']:C.S['mid'].set_texture_parameter_value('Hint',C.S['textures'][key])
   S['hint']=False
 if now-S.get('written',0)>.5:
  S['written']=now;(G.R/'ArtBible/QueueSession30.json').write_text(json.dumps(dict(status='READY',joined=S['joined'],called=S['called'],passengers_ahead=len(S['remaining']),departures={n:dict(index=q['index'],position=list(G.source(G.S['actors'][n].get_actor_location()))) for n,q in S['departures'].items()},hud=S.get('shown'),updated=time.time()),indent=2))
def initialize(game):
 global G,C;G=game;import airport_clarity26 as clarity;C=clarity
 S.update(base=G.physics,base_act=G.act,joined=False,called=False,remaining=list(G.D['checkin30']['npc_order']),departures={},clips={},textures={n:u.load_asset('/Game/Airport30/Textures/T30_'+n) for n in ['HUD_JoinQueue','HUD_Queue3','HUD_Queue2','HUD_Queue1','HUD_Called','HUD_HintJoin']})
 G.physics=tick;G.act=act;G.event('Crafted check-in30 ready',queue='live',counters=2)
 if '-CheckinPreview30' in G.CMD and '-AirportStartAboard' not in G.CMD:
  p=G.v([-41.9,-13,1.62]);G.P.STATE['pawn'].set_actor_location(p,False,True);G.P.STATE['pc'].set_control_rotation(u.MathLibrary.find_look_at_rotation(p,G.v([-33,-12.8,1.65])))
 if '-Checkin30QA' in G.CMD:
  import checkin30_qa;checkin30_qa.start(G)
