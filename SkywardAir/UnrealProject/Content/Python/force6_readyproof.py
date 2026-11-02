import unreal as u,time,json,hashlib
from pathlib import Path
def start(game):
 state={'after':None,'shot':False};path=game.R/'Screenshots/Force6_05_Playable_Ready.png'
 def tick(dt):
  s=game.S
  if not s.get('initialized') or not s.get('assembly_ready') or s.get('launched'):return
  now=time.monotonic()
  if state['after'] is None:state['after']=now+3
  if now<state['after']:return
  if not state['shot']:
   u.SystemLibrary.execute_console_command(s['world'],'DumpUnbuiltLightInteractions',s['pc']);game.shot('05_Playable_Ready');state.update(shot=True,requested_at=time.time());return
  if path.exists() and path.stat().st_mtime>=state['requested_at']:
   log=game.R/'ArtBible/ForcePreview6.log';text=log.read_text(errors='replace') if log.exists() else '';proof=dict(status='READY',capture=dict(file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest()),runtime_sha256=hashlib.sha256(Path(game.__file__).read_bytes()).hexdigest(),native_wall_joints=len(s['joints']),wall_bonds_failed=s['broken_wall'],maximum_rest_displacement_cm=max((q['actor'].get_actor_location()-u.Vector(*q['location'])).length() for q in s['active']),flying=s['flying'],view=s['view'],unbuilt_lights_zero='Lights with unbuilt interactions: 0' in text,unbuilt_primitives_zero='Primitives with unbuilt interactions: 0' in text);(game.R/'ArtBible/ForceReady6.json').write_text(json.dumps(proof,indent=2));u.unregister_slate_post_tick_callback(state['handle'])
 state['handle']=u.register_slate_post_tick_callback(tick)
