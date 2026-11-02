"""Capture-free native frame/callback sampling; setup poses are explicitly staged."""
import unreal as u,time,json,traceback,cProfile,pstats,io,statistics
G=None;S={}
V=[('Arrival',[-46.8,-13,1.62],[-43.2,-15,1.6]),('Checkin',[-40,-14,1.62],[-29,-14,1.4]),
 ('Security',[-41,1.3,1.62],[-41.95,2.32,1.55]),('Concourse',[-30,6.6,1.62],[-30,10,1.7]),
 ('GateA08',[-28,19,1.62],[-28,30,1.5]),('Cafe',[-34.2,18.2,1.62],[-41.3,26,1.6]),
 ('Cockpit',[16,-1.52,1.62],[16,-4,1.5])]
def save(status='RUNNING',**kw):
 (G.R/'ArtBible/Performance39.json').write_text(json.dumps(dict(status=status,context=S.get('context'),hardware=S.get('hardware'),stage=S['i'],views=S['results'],method='Staged pawn positions; ordinary unpaused runtime. Separate3s callback profiles, then12s uncaptured and unprofiled wall-frame samples per view. No performance guarantee for other hardware.',**kw),indent=2))
def finish(status,**kw):
 if S.get('prof'):S['prof'].disable()
 save(status,**kw);u.unregister_slate_post_tick_callback(S['handle']);u.SystemLibrary.quit_game(G.P.STATE['world'],G.P.STATE['pc'],u.QuitPreference.QUIT,False)
def tick(dt):
 try:
  now=time.perf_counter()
  if now<S['next']:return
  if S.get('profiling'):
   S['prof'].disable();buf=io.StringIO();pstats.Stats(S['prof'],stream=buf).sort_stats('cumulative').print_stats(45)
   (G.R/'ArtBible'/('Performance39_'+V[S['i']][0]+'.txt')).write_text(buf.getvalue())
   S.update(profiling=False,sampling=True,frames=[],last=None,begun=now);return
  if S.get('sampling'):
   if S.get('last'):S['frames'].append((now-S['last'])*1000)
   S['last']=now
   if now-S['begun']<12:return
   frames=sorted(S['frames']);assert frames
   S['results'].append(dict(view=V[S['i']][0],samples=len(frames),seconds=now-S['begun'],median_ms=statistics.median(frames),p95_ms=frames[min(len(frames)-1,int(len(frames)*.95))],mean_ms=statistics.mean(frames),minimum_ms=frames[0],maximum_ms=frames[-1]));S.update(i=S['i']+1,sampling=False,posed=False);save();return
  if S['i']>=len(V):finish('SUCCESS');return
  if S.get('posed'):
   S.update(prof=cProfile.Profile(),profiling=True,next=now+3);S['prof'].enable();return
  name,eye,target=V[S['i']];pawn=G.P.STATE['pawn'];pc=G.P.STATE['pc']
  pawn.set_actor_location(G.v(eye),False,True);pc.set_control_rotation(u.MathLibrary.find_look_at_rotation(G.v(eye),G.v(target)))
  S.update(posed=True,next=now+5);save()
 except Exception:finish('ERROR',error=traceback.format_exc())
def start(game):
 global G;G=game
 import characters12_runtime as C
 rows=[]
 for q in C.S['placements']:
  actor=C.ACTORS.get(q['actor'])
  if not actor:continue
  c=actor.skeletal_mesh_component;mesh=c.get_skeletal_mesh_asset()
  rows.append(dict(actor=q['actor'],character=q['character'],mesh=mesh.get_path_name() if mesh else None,
   materials=[c.get_material(i).get_path_name() if c.get_material(i) else None for i in range(c.get_num_materials())],
   location=list(G.source(actor.get_actor_location())),scale=list(actor.get_actor_scale3d().to_tuple())))
 (G.R/'ArtBible/CharacterBindings39.json').write_text(json.dumps(dict(status='RECORDED_NATIVE',characters=rows),indent=2))
 G.S.update(checked_in=True,security=True,boarding=True,aboard=True)
 S.update(i=0,context=json.loads((G.R/'ArtBible/InstalledRuntime39.json').read_text()),hardware=json.loads((G.R/'ArtBible/Hardware39.json').read_text()),results=[],next=time.perf_counter()+12,posed=False,sampling=False);S['handle']=u.register_slate_post_tick_callback(tick);save()
