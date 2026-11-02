import unreal as u,time,json,hashlib
from pathlib import Path
def start(game):
 state={'phase':0,'after':None}
 def tick(dt):
  s=game.S
  if not s.get('initialized') or not s.get('assembly_ready'):return
  if not game.alive(s.get('pc')):u.unregister_slate_post_tick_callback(state['handle']);return
  now=time.monotonic()
  if s.get('launched'):
   f=s['initial_velocity'].to_tuple();n=sum(v*v for v in f)**.5;rear=next(q['actor'] for q in s['parts'] if q['part']=='Aft').get_actor_location();delta=(rear-s['predicted_point']).to_tuple();depth=sum(a*b for a,b in zip(delta,f))/max(1,n)/100;state['rear_entry_depth_m']=max(state.get('rear_entry_depth_m',-1e9),depth)
  if state['after'] is None:state['after']=now+3
  if now<state['after'] or s['shots']:return
  phase=state['phase']
  if phase==0:game.pilot_view();state.update(phase=1,after=now+.7)
  elif phase==1:game.shot('01_Cockpit');state.update(phase=2,after=now+.5)
  elif phase==2:game.enter_free(s['flight_cams'][1].get_actor_location(),s['flight_cams'][1].get_actor_rotation());state.update(phase=3,after=now+.5)
  elif phase==3:game.shot('02_Ready');state.update(phase=4,after=now+.5)
  elif phase==4:game.launch();state.update(phase=5,after=now+.5)
  elif phase==5:
   if s.get('impact_time'):state.update(phase=6,after=now+.4)
  elif phase==6:state['impact_view']=s['view'];game.shot('03_Contact');state.update(phase=7,after=now+.9)
  elif phase==7:game.shot('04_Entry');state.update(phase=8,after=now+2.1)
  elif phase==8:game.shot('05_Progressive_Damage');state.update(phase=9,after=now+3)
  elif phase==9:game.shot('06_After_Impact');state.update(phase=10,after=now+4)
  elif phase==10:game.shot('07_Smoke');state.update(phase=11,after=now+.5)
  elif phase==11:
   side=(s['predicted_side']+2)%4;spec=next(q for q in game.D['towers'] if q['tower']==s['predicted_tower']);nx,ny=game.rotate(0,1,side);normal=u.Vector(nx,ny,0);right=u.Vector(-ny,nx,0);x,y=game.rotate(0,3152.92,side);p=u.Vector(spec['centre'][0]*100+x,-spec['centre'][1]*100+y,s['predicted_point'].z);eye=p+normal*15000+right*7000+u.Vector(0,0,2500);game.enter_free(eye,u.MathLibrary.find_look_at_rotation(eye,p));state.update(phase=12,after=now+.7)
  elif phase==12:game.shot('08_Opposite_View');state.update(phase=13,after=now+.5)
  else:
   broken={tuple(q['key']) for q in s['report']['native_break_events'] if q['kind']=='air'};spine={('Forward','Midbody'),('Midbody','Aft'),('Aft','TailBody')};photo=dict(status='SUCCESS',runtime_sha256=hashlib.sha256(Path(game.__file__).read_bytes()).hexdigest(),captures=list(s['report']['captures']),impact_view=state['impact_view'],broken_air_joints=s['broken_air'],broken_wall_bonds=s['broken_wall'],central_joints_intact=len(spine-broken),furthest_aft_cabin_entry_depth_m=state.get('rear_entry_depth_m'),aircraft_model='Thirteen breakable sections; reinforced central fuselage joints; original facade graph.');(game.R/'ArtBible/StabilityPhotos9.json').write_text(json.dumps(photo,indent=2));u.unregister_slate_post_tick_callback(state['handle'])
   if '-Stability9PhotosExit' in u.SystemLibrary.get_command_line():u.SystemLibrary.quit_game(s['world'],s['pc'],u.QuitPreference.QUIT,False)
 state['handle']=u.register_slate_post_tick_callback(tick)
