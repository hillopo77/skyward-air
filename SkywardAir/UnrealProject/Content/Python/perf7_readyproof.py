"""Genuine startup photographs; preserve the user camera after capture."""
import unreal as u,time,json,hashlib
from pathlib import Path
def start(game):
 state={'phase':0,'after':None}
 def tick(dt):
  s=game.S
  if not s.get('initialized') or not s.get('assembly_ready'):return
  if not game.alive(s.get('pc')):u.unregister_slate_post_tick_callback(state['handle']);return
  now=time.monotonic()
  if state['after'] is None:state['after']=now+4
  if now<state['after'] or s['shots']:return
  if state['phase']==0:
   game.pilot_view();state.update(phase=1,after=now+1)
  elif state['phase']==1:
   game.shot('07_Clear_Cockpit_Glass');state.update(phase=2,after=now+1)
  elif state['phase']==2:
   cam=s['flight_cams'][1];game.enter_free(cam.get_actor_location(),cam.get_actor_rotation());state.update(phase=3,after=now+1)
  elif state['phase']==3:
   game.shot('08_Spectator_Ready');state.update(phase=4,after=now+1)
  else:
   report=dict(status='READY',runtime_sha256=hashlib.sha256(Path(game.__file__).read_bytes()).hexdigest(),spectator_view=s['view'],spectator_speed_m_s=s['free_speed']/100,wall_bonds_failed=s['broken_wall'],rest_displacement_cm=max((q['actor'].get_actor_location()-u.Vector(*q['location'])).length() for q in s['active']),camera_parents=dict(pilot=s['flight_cams'][0].get_attach_parent_actor().get_actor_label(),chase=s['flight_cams'][1].get_attach_parent_actor().get_actor_label()),glass_changes=s['report']['glass_changes'],captures=list(s['report']['captures']),performance=s['report'].get('performance'),flying=s['flying'])
   (game.R/'ArtBible/PerformanceReady7.json').write_text(json.dumps(report,indent=2));u.unregister_slate_post_tick_callback(state['handle'])
   if '-Force7ProofExit' in u.SystemLibrary.get_command_line():u.SystemLibrary.quit_game(s['world'],s['pc'],u.QuitPreference.QUIT,False)
 state['handle']=u.register_slate_post_tick_callback(tick)
