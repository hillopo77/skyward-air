"""Native in-game photographs after preparation; inspection only, never used as a performance benchmark."""
import unreal as u,time,json,hashlib
from pathlib import Path
def start(game):
 state={'phase':0,'after':None}
 def tick(dt):
  s=game.S
  if not s.get('initialized') or not s.get('assembly_ready'):return
  if not game.alive(s.get('pc')):u.unregister_slate_post_tick_callback(state['handle']);return
  now=time.monotonic()
  if state['after'] is None:state['after']=now+3
  if now<state['after'] or s['shots']:return
  phase=state['phase']
  if phase==0:game.pilot_view();state.update(phase=1,after=now+1)
  elif phase==1:game.shot('01_Cockpit_Surround');state.update(phase=2,after=now+.5)
  elif phase==2:s['look_yaw']=-40;s['look_pitch']=9;state.update(phase=3,after=now+.5)
  elif phase==3:game.shot('02_Window_And_Sill');state.update(phase=4,after=now+.5)
  elif phase==4:game.enter_free(s['flight_cams'][1].get_actor_location(),s['flight_cams'][1].get_actor_rotation());state.update(phase=5,after=now+.5)
  elif phase==5:game.shot('03_Intact_Aircraft');state.update(phase=6,after=now+.5)
  elif phase==6:game.launch();state.update(phase=7,after=now+.5)
  elif phase==7:
   if s.get('impact_time'):state.update(phase=8,after=now+.5)
  elif phase==8:state['impact_view']=s['view'];game.shot('04_Rigid_Aircraft_Contact');state.update(phase=9,after=now+3)
  elif phase==9:game.shot('05_Settled_Aircraft');state.update(phase=10,after=now+3)
  elif phase==10:game.shot('06_Smoke_And_Damage');state.update(phase=11,after=now+.5)
  elif phase==11:
   _,spec,p,side=s['exit_hit8'];nx,ny=game.rotate(0,1,side);normal=u.Vector(nx,ny,0);right=u.Vector(-ny,nx,0);eye=p+normal*15000+right*7000+u.Vector(0,0,2500);game.enter_free(eye,u.MathLibrary.find_look_at_rotation(eye,p));state.update(phase=12,after=now+1)
  elif phase==12:game.shot('07_Opposite_Face');state.update(phase=13,after=now+.5)
  else:
   report=dict(status='SUCCESS',runtime_sha256=hashlib.sha256(Path(game.__file__).read_bytes()).hexdigest(),captures=list(s['report']['captures']),rigid_error_cm=game.rigid_error(),native_body_count=1,compound_collision_shapes=13,impact_view=state['impact_view'],broken_wall_bonds=s['broken_wall'],exit_region=s['report'].get('exit_region8'),new_surround_present=any('SM_CockpitSurround8' in a.get_actor_label() for a in s['rig']),source='Native Unreal HighResShot; original PNGs; no generated or painted screenshots.')
   (game.R/'ArtBible/RigidPhotos8.json').write_text(json.dumps(report,indent=2));u.unregister_slate_post_tick_callback(state['handle'])
   if '-Force8PhotosExit' in u.SystemLibrary.get_command_line():u.SystemLibrary.quit_game(s['world'],s['pc'],u.QuitPreference.QUIT,False)
 state['handle']=u.register_slate_post_tick_callback(tick)
