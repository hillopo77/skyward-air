"""Capture the final ready screen and lighting diagnostics without running another impact."""
import unreal as u,time,json,hashlib
from pathlib import Path
def start(flight):
 state={'requested':False,'after':0,'lights':[]};R=flight.R;out=R/'Screenshots/Flight5_09_Ready_To_Play.png';capture='-Flight5ReadyProof' in u.SystemLibrary.get_command_line()
 def tick(dt):
  if not flight.S.get('initialized'):return
  now=time.monotonic()
  if not state['after']:
   for a in u.GameplayStatics.get_all_actors_of_class(flight.S['world'],u.Actor):
    for c in a.get_components_by_class(u.LightComponentBase):
     old=str(c.get_editor_property('mobility'));c.set_mobility(u.ComponentMobility.STATIONARY);c.set_mobility(u.ComponentMobility.MOVABLE);state['lights'].append(dict(actor=a.get_actor_label(),before=old,after=str(c.get_editor_property('mobility'))))
   state['after']=now+3
  if now<state['after']:return
  if not capture:u.unregister_slate_post_tick_callback(state['handle']);return
  if not state['requested']:
   u.SystemLibrary.execute_console_command(flight.S['world'],'DumpUnbuiltLightInteractions',flight.S['pc']);u.SystemLibrary.execute_console_command(flight.S['world'],'Shot filename="'+str(out).replace('\\','/')+'" -nosuffix showui',flight.S['pc']);state.update(requested=True,requested_at=time.time());return
  if out.exists() and out.stat().st_mtime>=state['requested_at']:
   log=R/'ArtBible/FlightReady5.log';tail='\n'.join(log.read_text(errors='replace').splitlines()[-45:]) if log.exists() else '';proof=dict(status='READY',captured_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),flying=flight.S['flying'],view=flight.S['view'],ready=flight.S['report']['ready'],runtime_sha256=hashlib.sha256(Path(flight.__file__).read_bytes()).hexdigest(),capture=dict(file=out.name,sha256=hashlib.sha256(out.read_bytes()).hexdigest()),lighting_diagnostics=tail,lights=state['lights']);(R/'ArtBible/FlightReadyProof5.json').write_text(json.dumps(proof,indent=2));u.unregister_slate_post_tick_callback(state['handle'])
 state['handle']=u.register_slate_post_tick_callback(tick)
