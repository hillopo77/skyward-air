"""Complete passenger journey: live ticket, physical bag drop, portal traversal and boarding."""
import unreal as u,time,json,hashlib
from pathlib import Path
G=None;S={};R=Path(__file__).resolve().parents[4]/'Airport/Journey22'
FLOW={'checkin','bagdrop','scanner','security','boarding','boardingdoor'}
def emit(name,**details):
 S['events'].append(dict(event=name,elapsed_s=time.monotonic()-S['started'],**details));G.event(name,**details);write()
def write():
 if not G:return
 data=dict(status='READY',revision=22,stage=stage(),ticket=S.get('ticket'),journey={n:G.S.get(n,False) for n in ['checked_in','bag_accepted','security','boarding','aboard']},seat=S.get('seat'),events=S['events'],player=list(G.source(G.P.STATE['pawn'].get_actor_location())),runtime_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest());(R/'ArtBible/Session22.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
def stage():
 if S.get('seat'):return 'seated'
 if G.S.get('aboard'):return 'aboard'
 if G.S.get('boarding'):return 'jetbridge'
 if G.S.get('security'):return 'gate'
 if G.S.get('checked_in'):return 'bagdrop_security'
 return 'checkin'
def objective():
 return {'checkin':'Check in for SA107', 'bagdrop_security':'Bag drop optional / walk through security', 'gate':'SA107 / Gate A07 / B: boarding pass', 'jetbridge':'Walk through the jetbridge and aircraft door', 'aboard':'Welcome aboard / Economy 03E via the right aisle', 'seated':'Boarding complete / seated for SA107'}[stage()]
def ticket():
 if not S.get('ticket'):S['ticket']=dict(id='SW-SA107-LOCAL-01',flight='SA107',destination='Azure Bay',gate='A07',cabin='Economy',seat='03E',checked_bags=[],security_cleared=False,gate_scanned=False,aboard=False)
 return S['ticket']
def usable(q):
 return (G.point(q)-G.P.STATE['pawn'].get_actor_location()).length()<=340 and G.visible(q)
def act(q):
 kind=q['kind']
 if kind in FLOW and not usable(q):G.say('Move closer and face the control');return
 if kind=='pickup' and q['actor'] in S.get('registered_bags',[]):G.say('This suitcase has been checked for SA107');return
 if kind=='checkin':
  S['base_act'](q);ticket();G.say('SA107 / Azure Bay / Gate A07 / Economy 03E / B: pass');emit('Boarding pass issued',actor=q['actor']);return
 if kind in ('boarding','boardingdoor'):
  was=G.S['boarding'];S['base_act'](q)
  if G.S['boarding'] and not was:ticket()['gate_scanned']=True;emit('Boarding pass validated at A07')
  return
 if kind=='bagdrop':
  S['base_act'](q)
  if G.S.get('bag_drop_armed') and G.S.get('held'):
   actor=G.S['held'];asset=G.S['actor_specs'][actor]['asset']
   if asset.startswith('SM_AP_Bag') or asset=='SM_AP_CarryOn':
    belt=next(b for b in G.D['conveyors'] if b['name']==q['actor']);x0,x1,y0,y1=belt['rect'];goal=G.v(belt.get('load_point',[(x0+x1)/2,y0+.72,belt['height']+.62]));G.S['deposit_goal']=goal;S['deposit']=dict(actor=actor,belt=belt['name'],started=time.monotonic());G.say('Placing suitcase on the belt');emit('Bag placement requested',actor=actor)
  return
 return S['base_act'](q)
def use(stand_on_miss=True):
 if G.S.get('held'):
  q=G.nearest()
  if q and q['kind'] in FLOW:act(q);return True
 return S['base_use'](stand_on_miss)
def sit(q):
 aircraft=q.get('kind')=='seat' and q.get('actor') in S['aircraft_seats']
 if aircraft and not G.S.get('aboard'):G.say('Board through Gate A07 first');return
 result=S['base_sit'](q)
 if aircraft and G.P.STATE.get('seated'):
  S['seat']=q['actor'];emit('Aircraft seat occupied',actor=q['actor'],title=q.get('title'));G.say('You are aboard SA107 / '+q.get('title','Seat'))
 return result
def stand():
 result=S['base_stand']()
 if S.get('seat'):S['seat']=None;emit('Passenger stood up aboard')
 return result
def physics(dt):
 S['base_physics'](dt);pawn=G.P.STATE['pawn'];p=G.source(pawn.get_actor_location());previous=S.get('previous',p);walking=not (G.S.get('spectator') or G.S.get('driving') or G.P.STATE.get('seated'))
 deposit=S.get('deposit')
 if deposit:
  actor=G.S['actors'][deposit['actor']];c=actor.static_mesh_component;goal=G.S['deposit_goal'];distance=(c.get_center_of_mass()-goal).length()
  if G.S.get('held')!=deposit['actor'] or time.monotonic()-deposit['started']>5 or (pawn.get_actor_location()-goal).length()>340:
   G.S.pop('deposit_goal',None);S.pop('deposit',None)
  elif distance<14 and c.get_physics_linear_velocity().length()<120:
   G.release(False);G.S.pop('deposit_goal',None);S.pop('deposit',None);emit('Suitcase placed using native physics',actor=deposit['actor'])
 if G.S.get('checked_in') and G.S.get('bag_drop_armed'):
  for n,actor in G.S['physics'].items():
   if n==G.S.get('held') or n in S['registered_bags']:continue
   asset=G.S['actor_specs'][n]['asset']
   if not (asset.startswith('SM_AP_Bag') or asset=='SM_AP_CarryOn'):continue
   c=actor.static_mesh_component;x,y,z=G.source(c.get_center_of_mass())
   for belt in G.D['conveyors']:
    if belt['kind']!='bagdrop':continue
    x0,x1,y0,y1=belt['rect']
    if x0<x<x1 and y0<y<y1 and belt['height']+.015<z<belt['height']+1.3 and G.supported_on_belt(c,belt):
     S['registered_bags'].append(n);ticket()['checked_bags'].append(n);G.S['bag_accepted']=True;G.screen(G.S['actors'][belt['name']],'Scanned');G.say('Suitcase checked for SA107 / continue to security');emit('Checked suitcase accepted on physical belt',actor=n,belt=belt['name']);break
 # A full south-to-north walk through a portal is required. Flying or teleporting
 # into the portal cannot clear screening.
 if not walking or not G.S.get('checked_in'):S['lane']=None
 elif not G.S.get('security') and 1.25<p[2]<2.1 and abs(p[0]-previous[0])<max(1.,min(dt,.8)*G.P.STATE['pawn'].get_component_by_class(u.FloatingPawnMovement).get_editor_property('max_speed')/100+.25) and abs(p[1]-previous[1])<max(1.,min(dt,.8)*G.P.STATE['pawn'].get_component_by_class(u.FloatingPawnMovement).get_editor_property('max_speed')/100+.25):
  for i,(x0,x1,y0,y1) in enumerate(G.D['security_crossings']):
   if x0<p[0]<x1 and previous[1]<=y0<p[1]:S['lane']=i
   if S.get('lane')==i and x0<p[0]<x1 and previous[1]<=y1<p[1]:G.S['security']=True;ticket()['security_cleared']=True;S['lane']=None;G.cue('ScannerReady',p);G.say('Security cleared / SA107 boards at Gate A07');emit('Security cleared by full portal traversal',lane=i)
   if S.get('lane')==i and (not x0<p[0]<x1 or p[1]<y0-.1):S['lane']=None
 # Register the real cabin threshold, not arbitrary airfield positions.
 if walking and G.S.get('boarding') and G.S.get('security') and not G.S.get('aboard'):
  if previous[0]<=-1.9<p[0]<2.4 and -.3<p[1]<2.0 and 1.25<p[2]<2.1 and abs(p[0]-previous[0])<1 and abs(p[1]-previous[1])<1:
   G.S['aboard']=True;ticket()['aboard']=True;G.say('Welcome aboard / Economy 03E via the right aisle');emit('Aircraft boarded through the actual door')
 S['previous']=p
 if G.P.STATE['pc'].was_input_key_just_pressed(S['pass_key']):S['pass_visible']=not S.get('pass_visible')
 if S.get('pass_visible'):
  t=S.get('ticket');text='Collect your boarding pass at check-in' if not t else 'SKYWARD AIR / BOARDING PASS\nSA107  Azure Bay  Gate A07  Economy 03E\nChecked bags: '+str(len(t['checked_bags']))+' / Security: '+('cleared' if t['security_cleared'] else 'pending')+' / B: close'
  u.SystemLibrary.print_string(G.P.STATE['world'],text,True,False,u.LinearColor(.55,.87,1,1),.12,u.Name('BoardingPass22'))
 if time.monotonic()-S.get('last_write',0)>.5:S['last_write']=time.monotonic();write()
def initialize(game):
 global G;G=game;S.update(started=time.monotonic(),events=[],ticket=None,seat=None,registered_bags=[],previous=G.source(G.P.STATE['pawn'].get_actor_location()),lane=None,base_act=G.act,base_use=G.use_nearest,base_physics=G.physics,base_sit=G.P.sit,base_stand=G.P.stand,aircraft_seats={q['actor'] for q in G.P.STATE['items'] if q['kind']=='seat'},pass_key=G.key('B'))
 G.act=act;G.use_nearest=use;G.P.use_nearest=use;G.physics=physics;G.P.sit=sit;G.P.stand=stand
 if G.S.get('checked_in'):
  t=ticket();t.update(security_cleared=G.S.get('security',False),gate_scanned=G.S.get('boarding',False),aboard=G.S.get('aboard',False))
 cast=json.loads((R/'Narrative/Cast22.json').read_text(encoding='utf-8'));S['cast']=cast
 for character in cast['characters']:
  for q in G.S['targets']:
   if q['kind']=='npc' and q['actor']==character['actor']:q['title']='Talk to '+character['name'];q['dialogue']=character['public_dialogue'];q['story_character']=character['id']
 write()
